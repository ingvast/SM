from .common import flatten_name, resolve_target_path, get_exit_sequence

HEADER = """
#![allow(unused_variables)]
#![allow(dead_code)]
#![allow(non_snake_case)]

// --- User Includes / Context Types ---
%s

pub struct Context {
    pub now: f64,
    pub state_timers: [f64; %d],
    
    // Hierarchy Pointers (Option<fn>)
    %s
    
    // User Context Fields
    %s
}

// Function Pointer Type
type StateFn = fn(&mut Context);

pub struct StateMachine {
    pub ctx: Context,
    pub root: Option<StateFn>,
}

impl StateMachine {
    pub fn new() -> Self {
        let mut ctx = Context {
            now: 0.0,
            state_timers: [0.0; %d],
            
            // Init Hierarchy Pointers
            %s
            
            // Init User Context
            %s
        };
        
        let mut sm = StateMachine {
            ctx,
            root: None,
        };
        
        // Start Machine
        state_root_entry(&mut sm.ctx);
        sm.root = Some(state_root_run);
        sm
    }

    pub fn tick(&mut self) {
        if let Some(run_fn) = self.root {
            run_fn(&mut self.ctx);
        }
    }

    pub fn get_state_str(&self) -> String {
        let mut buffer = String::new();
        if self.root.is_some() {
             inspect_root(&self.ctx, &mut buffer);
        }
        buffer
    }
}

// --- Helper Macros/Methods ---
impl Context {
    %s 
}

// --- State Logic ---
"""

FUNC_PREAMBLE = """
    let state_name = "{short_name}";
    let state_full_name = "{display_name}";
    let time = ctx.now - ctx.state_timers[{state_id}];
"""

# In codegen/rust_lang.py

LEAF_TEMPLATE = """
fn state_{c_name}_start(ctx: &mut Context) {{
    ctx.state_timers[{state_id}] = ctx.now;
    {preamble}
    {hook_entry}
    // Set pointer, but NO run call
    ctx.{parent_ptr} = Some(state_{c_name}_run);
}}

fn state_{c_name}_entry(ctx: &mut Context) {{
    state_{c_name}_start(ctx);
    // Leaf has no children to enter
}}

fn state_{c_name}_exit(ctx: &mut Context) {{
    {preamble}
    {hook_exit}
    {exit}
}}

fn state_{c_name}_run(ctx: &mut Context) {{
    {preamble}
    {hook_run}
    {run}
    {transitions}
}}
"""

COMPOSITE_OR_TEMPLATE = """
fn state_{c_name}_start(ctx: &mut Context) {{
    ctx.state_timers[{state_id}] = ctx.now;
    {preamble}
    {hook_entry}
    {set_parent}
}}

fn state_{c_name}_entry(ctx: &mut Context) {{
    state_{c_name}_start(ctx);
    
    // Recurse to child
    if ({history}) && ctx.{self_hist_ptr}.is_some() {{
        let hist_fn = ctx.{self_hist_ptr}.unwrap();
        hist_fn(ctx);
    }} else {{
        state_{initial_target}_entry(ctx);
    }}
}}

fn state_{c_name}_exit(ctx: &mut Context) {{
    {preamble}
    {hook_exit}
    {exit}
}}

fn state_{c_name}_run(ctx: &mut Context) {{
    {preamble}
    {hook_run}
    {run}
    if let Some(child_run) = ctx.{self_ptr} {{
        child_run(ctx);
    }}
    {transitions}
}}
"""

COMPOSITE_AND_TEMPLATE = """
fn state_{c_name}_start(ctx: &mut Context) {{
    ctx.state_timers[{state_id}] = ctx.now;
    {preamble}
    {hook_entry}
    {set_parent}
}}

fn state_{c_name}_entry(ctx: &mut Context) {{
    state_{c_name}_start(ctx);
    // Start all parallel regions
    {parallel_entries}
}}

fn state_{c_name}_exit(ctx: &mut Context) {{
    {preamble}
    {hook_exit}
    {parallel_exits}
    {exit}
}}

fn state_{c_name}_run(ctx: &mut Context) {{
    {preamble}
    {hook_run}
    {run}
    {parallel_ticks}
    {transitions}
}}
"""


INSPECTOR_TEMPLATE = """
fn inspect_{c_name}(ctx: &Context, buf: &mut String) {{
    {push_name}
    {content}
}}
"""

class RustGenerator:
    def __init__(self, data):
        self.data = data
        self.state_counter = 0
        self.outputs = {'context_ptrs': [], 'context_init': [], 'functions': [], 'impls': []}
        self.inspect_list = []
        self.decisions = data.get('decisions', {})
        self.hooks = data.get('hooks', {})
        self.includes = data.get('includes', '')

    def _fmt_func(self, path):
        return "state_" + flatten_name(path, "_") + "_exit"

    def generate(self):
        root_data = {
            'initial': self.data['initial'], 'states': self.data['states'],
            'history': False, 'entry': "// Root Entry", 'run': "// Root Run", 'exit': "// Root Exit"
        }
        
        self.recurse(['root'], root_data, None)
        self.gen_inspector(['root'], root_data, 'root')

        user_init = self.data.get('context_init', '')

        header = HEADER % (
            self.includes, 
            self.state_counter,
            "\n    ".join(self.outputs['context_ptrs']),
            self.data.get('context', ''), 
            self.state_counter,
            "\n            ".join(self.outputs['context_init']),
            user_init,
            "\n    ".join(self.outputs['impls'])
        )
        
        source = "\n".join(self.outputs['functions'])
        source += "\n// --- Inspection ---\n" + "\n".join(self.inspect_list)

        return header + source, ""

    def _fmt_entry(self, path, suffix="_entry"):
        return "state_" + flatten_name(path, "_") + suffix

    def emit_transition_logic(self, name_path, t, indent_level=1):
        indent = "    " * indent_level
        code = ""
        target_str = t['transfer_to']
        
        test_val = t.get('test', True)
        if test_val is True: test_cond = "true"
        elif test_val is False: test_cond = "false"
        else: test_cond = str(test_val)
        
        import re
        test_cond = re.sub(r'IN_STATE\(([\w_]+)\)', r'ctx.in_state_\1()', test_cond)

        code += f"{indent}if {test_cond} {{\n"

        # Check for Decision or State
        if target_str in self.decisions:
            # Inline Decision Logic (Recursive)
            decision_rules = self.decisions[target_str]
            for rule in decision_rules:
                code += self.emit_transition_logic(name_path, rule, indent_level + 1)
        else:
            # Transition to State
            target_path = resolve_target_path(name_path, target_str)
            
            # 1. Calculate Exits (Bottom-Up)
            exit_funcs = get_exit_sequence(name_path, target_path, self._fmt_func)
            
            # 2. Calculate Entries (Top-Down) [NEW]
            from .common import get_entry_sequence
            entry_funcs = get_entry_sequence(name_path, target_path, self._fmt_entry)
            
            exit_calls = "".join([f"{indent}    {fn}(ctx);\n" for fn in exit_funcs])
            entry_calls = "".join([f"{indent}    {fn}(ctx);\n" for fn in entry_funcs])

            code += f"{exit_calls}"
            code += f"{entry_calls}"
            code += f"{indent}    return;\n"

        code += f"{indent}}}\n"
        return code

    def recurse(self, name_path, data, parent_ptrs):
        my_id_num = self.state_counter
        self.state_counter += 1
        my_c_name = flatten_name(name_path, "_")
        
        disp_name = "/" + "/".join(name_path[1:]) if len(name_path) > 1 else "/"
        preamble = FUNC_PREAMBLE.format(short_name=name_path[-1], display_name=disp_name, state_id=my_id_num)

        parent_run_ptr = parent_ptrs[0] if parent_ptrs else None
        parent_hist_ptr = parent_ptrs[1] if parent_ptrs else None

        # Helper method for In-State check
        if parent_run_ptr:
            method = f"""
    pub fn in_state_{my_c_name}(&self) -> bool {{
        self.{parent_run_ptr}.map(|f| f as usize) == Some(state_{my_c_name}_run as usize)
    }}"""
            self.outputs['impls'].append(method)

        hist_save_code = f"ctx.{parent_hist_ptr} = Some(state_{my_c_name}_entry);" if parent_hist_ptr else ""
        set_parent_code = f"ctx.{parent_run_ptr} = Some(state_{my_c_name}_run);" if parent_run_ptr else ""

        trans_code = ""
        for t in data.get('transitions', []):
            trans_code += self.emit_transition_logic(name_path, t, 2)

        is_composite = 'states' in data
        is_parallel = data.get('parallel', False)
        
        h_entry = self.hooks.get('entry', '')
        h_run = self.hooks.get('run', '')
        h_exit = self.hooks.get('exit', '')

        if is_composite:
            if is_parallel:
                p_entries, p_exits, p_ticks = "", "", ""
                for child_name, child_data in data['states'].items():
                    child_path = name_path + [child_name]
                    region_ptr = f"ptr_{flatten_name(child_path, '_')}"
                    
                    init_leaf = flatten_name(child_path + [child_data['initial']], "_")
                    p_entries += f"    state_{init_leaf}_entry(ctx);\n"
                    p_ticks += f"    if let Some(f) = ctx.{region_ptr} {{ f(ctx); }}\n"
                    p_exits += f"    // Implicit exit {child_name}\n"
                    
                    self.recurse(child_path, child_data, (region_ptr, None))

                func_body = COMPOSITE_AND_TEMPLATE.format(
                    c_name=my_c_name, state_id=my_id_num, preamble=preamble,
                    hook_entry=h_entry, hook_run=h_run, hook_exit=h_exit,
                    entry=data.get('entry', ''), exit=data.get('exit', ''), run=data.get('run', ''),
                    transitions=trans_code, set_parent=set_parent_code,
                    parallel_entries=p_entries, parallel_exits=p_exits, parallel_ticks=p_ticks,
                    history_save=hist_save_code
                )
            else:
                my_ptr = f"ptr_{my_c_name}"
                my_hist = f"hist_{my_c_name}"
                
                self.outputs['context_ptrs'].append(f"pub {my_ptr}: Option<StateFn>,")
                self.outputs['context_ptrs'].append(f"pub {my_hist}: Option<StateFn>,")
                self.outputs['context_init'].append(f"{my_ptr}: None,")
                self.outputs['context_init'].append(f"{my_hist}: None,")
                
                init_target = flatten_name(name_path + [data['initial']], "_")
                hist_bool = "true" if data.get('history', False) else "false"

                func_body = COMPOSITE_OR_TEMPLATE.format(
                    c_name=my_c_name, state_id=my_id_num, preamble=preamble,
                    hook_entry=h_entry, hook_run=h_run, hook_exit=h_exit,
                    entry=data.get('entry', ''), exit=data.get('exit', ''), run=data.get('run', ''),
                    transitions=trans_code, history=hist_bool,
                    self_ptr=my_ptr, self_hist_ptr=my_hist,
                    initial_target=init_target, history_save=hist_save_code,
                    set_parent=set_parent_code
                )
                
                for child_name, child_data in data['states'].items():
                    self.recurse(name_path + [child_name], child_data, (my_ptr, my_hist))
        else:
            func_body = LEAF_TEMPLATE.format(
                c_name=my_c_name, state_id=my_id_num, preamble=preamble,
                hook_entry=h_entry, hook_run=h_run, hook_exit=h_exit,
                entry=data.get('entry', ''), exit=data.get('exit', ''), run=data.get('run', ''),
                transitions=trans_code, history_save=hist_save_code,
                parent_ptr=parent_run_ptr
            )

        self.outputs['functions'].append(func_body)

    def gen_inspector(self, name_path, data, ptr_name_struct):
        my_c_name = flatten_name(name_path, "_")
        disp_name = "" if name_path == ['root'] else "/" + name_path[-1]
        
        push_name = f'buf.push_str("{disp_name}");' if disp_name else ""
        content = ""

        is_composite = 'states' in data
        if is_composite:
            if data.get('parallel', False):
                content += 'buf.push_str("[");\n'
                children = list(data['states'].items())
                for i, (child_name, child_data) in enumerate(children):
                    child_path = name_path + [child_name]
                    child_func = f"inspect_{flatten_name(child_path, '_')}"
                    region_ptr = f"ptr_{flatten_name(child_path, '_')}"
                    self.gen_inspector(child_path, child_data, region_ptr)
                    content += f"    {child_func}(ctx, buf);\n"
                    if i < len(children)-1: content += '    buf.push_str(",");\n'
                content += 'buf.push_str("]");\n'
            else:
                my_ptr = f"ptr_{my_c_name}"
                for child_name, child_data in data['states'].items():
                    self.gen_inspector(name_path + [child_name], child_data, my_ptr)
                
                first = True
                for child_name, child_data in data['states'].items():
                    c_name = flatten_name(name_path + [child_name], "_")
                    else_txt = "else " if not first else ""
                    content += f"    {else_txt}if ctx.{my_ptr}.map(|f| f as usize) == Some(state_{c_name}_run as usize) {{ inspect_{c_name}(ctx, buf); }}\n"
                    first = False

        self.inspect_list.append(INSPECTOR_TEMPLATE.format(c_name=my_c_name, push_name=push_name, content=content))

