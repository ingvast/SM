import yaml
import sys

# ---------------------------------------------------------
# TEMPLATES
# ---------------------------------------------------------
HEADER = """
#ifndef STATEMACHINE_H
#define STATEMACHINE_H
#include <stdio.h>
#include <stdbool.h>
#include <string.h>

#define TOTAL_STATES %d

typedef struct SM_Context SM_Context;
typedef void (*StateFunc)(SM_Context* ctx);

// --- Forward Declarations ---
%s

struct SM_Context {
    void* owner;
    double now; 
    double state_timers[TOTAL_STATES];

    // User Context Variables
    %s
    
    // Hierarchy Pointers
    %s
};

typedef struct {
    SM_Context ctx;
    StateFunc root;
} StateMachine;

void sm_init(StateMachine* sm);
void sm_tick(StateMachine* sm);
void sm_get_state_str(StateMachine* sm, char* buffer, size_t max_len);

// --- Macros ---
#define IN_STATE(statename) IN_STATE_##statename
%s

#endif
"""

SOURCE_TOP = """
#include "statemachine.h"

// --- User Includes ---
%s

// --- Helpers ---
static void safe_strcat(char* dest, const char* src, size_t* offset, size_t max) {
    size_t len = strlen(src);
    if (*offset + len >= max) return; // Truncate safely
    strcpy(dest + *offset, src);
    *offset += len;
}

// --- State Logic ---
"""

FUNC_PREAMBLE = """
    (void)ctx;
    const char* state_name = "{short_name}";
    const char* state_full_name = "{display_name}";
    (void)state_name; 
    (void)state_full_name;
    double time = ctx->now - ctx->state_timers[{state_id}];
    (void)time; 
"""

LEAF_TEMPLATE = """
void state_{c_name}_entry(SM_Context* ctx) {{
    ctx->state_timers[{state_id}] = ctx->now;
    {preamble}
    {hook_entry}
    {history_save}
    {entry}
    ctx->{parent_ptr} = state_{c_name}_run;
    state_{c_name}_run(ctx);
}}

void state_{c_name}_exit(SM_Context* ctx) {{
    {preamble}
    {hook_exit}
    {exit}
}}

void state_{c_name}_run(SM_Context* ctx) {{
    {preamble}
    {hook_run}
    {run}
    {transitions}
}}
"""

COMPOSITE_OR_TEMPLATE = """
void state_{c_name}_entry(SM_Context* ctx) {{
    ctx->state_timers[{state_id}] = ctx->now;
    {preamble}
    {hook_entry}
    {history_save}
    {entry}
    
    {set_parent}

    if (({history}) && ctx->{self_hist_ptr} != NULL) {{
        ctx->{self_hist_ptr}(ctx);
    }} else {{
        state_{initial_target}_entry(ctx);
    }}
}}

void state_{c_name}_exit(SM_Context* ctx) {{
    {preamble}
    {hook_exit}
    {exit}
}}

void state_{c_name}_run(SM_Context* ctx) {{
    {preamble}
    {hook_run}
    {run}
    if (ctx->{self_ptr}) ctx->{self_ptr}(ctx);
    {transitions}
}}
"""

COMPOSITE_AND_TEMPLATE = """
void state_{c_name}_entry(SM_Context* ctx) {{
    ctx->state_timers[{state_id}] = ctx->now;
    {preamble}
    {hook_entry}
    {history_save}
    {entry}
    
    {set_parent}

    // Parallel Entry
    {parallel_entries}
}}

void state_{c_name}_exit(SM_Context* ctx) {{
    {preamble}
    {hook_exit}
    // Parallel Exit
    {parallel_exits}
    {exit}
}}

void state_{c_name}_run(SM_Context* ctx) {{
    {preamble}
    {hook_run}
    {run}
    // Parallel Run
    {parallel_ticks}
    {transitions}
}}
"""

# ---------------------------------------------------------
# COMMON UTILS
# ---------------------------------------------------------
def flatten_c_name(path):
    return "_".join(path)

def flatten_display_name(path):
    if len(path) == 1: return "/"
    return "/" + "/".join(path[1:])

def resolve_target_path(current_path, target_str):
    if target_str.startswith("root/"):
        return target_str.split("/")
    if target_str.startswith("../"):
        parent_scope = current_path[:-2]
        clean_target = target_str.replace("../", "")
        return parent_scope + [clean_target]
    parent_scope = current_path[:-1]
    return parent_scope + [target_str]

def get_exit_sequence(source_path, target_path):
    lca_index = 0
    min_len = min(len(source_path), len(target_path))
    while lca_index < min_len:
        if source_path[lca_index] != target_path[lca_index]:
            break
        lca_index += 1
    exits = []
    for i in range(len(source_path) - 1, lca_index - 1, -1):
        state_segment = source_path[:i+1]
        c_name = flatten_c_name(state_segment)
        exits.append(f"state_{c_name}_exit")
    return exits

# ---------------------------------------------------------
# GENERATOR: INSPECTION (New)
# ---------------------------------------------------------
def generate_inspector(name_path, data, parent_ptr_name, output_list):
    my_c_name = flatten_c_name(name_path)
    func_name = f"inspect_{my_c_name}"
    
    # 1. Determine Display Name
    # Root is special, we don't print "root" usually
    if name_path == ['root']:
        disp_name = "" 
    else:
        disp_name = "/" + name_path[-1]

    body = f"void {func_name}(SM_Context* ctx, char* buf, size_t* off, size_t max) {{\n"
    if disp_name:
        body += f"    safe_strcat(buf, \"{disp_name}\", off, max);\n"

    is_composite = 'states' in data
    is_parallel = data.get('parallel', False)

    if is_composite:
        if is_parallel:
            # Parallel: Print brackets and recurse all children
            body += f"    safe_strcat(buf, \"[\", off, max);\n"
            
            # For parallel, we don't check pointers (they are all active).
            # We assume regions are always running if parent is running.
            children = list(data['states'].items())
            for i, (child_name, child_data) in enumerate(children):
                child_path = name_path + [child_name]
                child_func = f"inspect_{flatten_c_name(child_path)}"
                
                # Recurse generation
                # Note: Region pointers are in ctx, but we don't need to check them 
                # because a Parallel state *implies* all regions are active.
                # However, the region ITSELF (Composite OR) needs to check ITS pointer.
                # We need to know the pointer name the region uses.
                # In 'generate_state_machine', we named it ptr_root_active_m1.
                region_ptr_name = f"ptr_{flatten_c_name(child_path)}"
                
                generate_inspector(child_path, child_data, region_ptr_name, output_list)
                
                body += f"    {child_func}(ctx, buf, off, max);\n"
                if i < len(children) - 1:
                    body += f"    safe_strcat(buf, \",\", off, max);\n"
            
            body += f"    safe_strcat(buf, \"]\", off, max);\n"

        else:
            # Standard OR: Check which child is active
            # We need the pointer variable name for THIS state.
            # If I am 'root', my pointer is 'ptr_root'.
            # If I am 'active', my pointer is 'ptr_active'.
            # Wait, the pointer variable is stored in the STRUCT.
            # We need to know what variable name was assigned to ME to track my children.
            # logic: my_ptr_name = ptr_{my_c_name}
            my_ptr_name = f"ptr_{my_c_name}"
            
            # Recurse generation first so functions exist
            for child_name, child_data in data['states'].items():
                child_path = name_path + [child_name]
                generate_inspector(child_path, child_data, my_ptr_name, output_list)
            
            # Generate Runtime Check
            first = True
            for child_name, child_data in data['states'].items():
                child_path = name_path + [child_name]
                child_c_name = flatten_c_name(child_path)
                inspect_func = f"inspect_{child_c_name}"
                run_func = f"state_{child_c_name}_run"
                
                else_prefix = "else " if not first else ""
                body += f"    {else_prefix}if (ctx->{my_ptr_name} == {run_func}) {inspect_func}(ctx, buf, off, max);\n"
                first = False

    body += "}\n"
    output_list.append(body)


# ---------------------------------------------------------
# GENERATOR: C LOGIC
# ---------------------------------------------------------
state_counter = 0

def generate_state_machine(name_path, data, parent_ptrs, output_lists, global_hooks):
    global state_counter
    my_id_num = state_counter
    state_counter += 1

    my_c_name = flatten_c_name(name_path)
    my_disp_name = flatten_display_name(name_path)
    
    parent_run_ptr = parent_ptrs[0] if parent_ptrs else None
    parent_hist_ptr = parent_ptrs[1] if parent_ptrs else None

    if parent_run_ptr:
        macro_def = f"#define IN_STATE_{my_c_name} (ctx->{parent_run_ptr} == state_{my_c_name}_run)"
        output_lists['macros'].append(macro_def)

    hist_save_code = f"ctx->{parent_hist_ptr} = state_{my_c_name}_entry;" if parent_hist_ptr else ""
    set_parent_code = f"ctx->{parent_run_ptr} = state_{my_c_name}_run;" if parent_run_ptr else ""

    preamble_filled = FUNC_PREAMBLE.format(
        short_name=name_path[-1],
        display_name=my_disp_name, 
        state_id=my_id_num
    )

    trans_code = ""
    for t in data.get('transitions', []):
        target_path_list = resolve_target_path(name_path, t['transfer_to'])
        target_c_func = "state_" + flatten_c_name(target_path_list)
        exit_funcs = get_exit_sequence(name_path, target_path_list)
        exit_calls = "".join([f"        {exit_func}(ctx);\n" for exit_func in exit_funcs])

        test_val = t['test']
        if test_val is True: test_cond = "true"
        elif test_val is False: test_cond = "false"
        else: test_cond = str(test_val)

        trans_code += f"""
    if ({test_cond}) {{
{exit_calls}
        {target_c_func}_entry(ctx); 
        return; 
    }}"""

    is_composite = 'states' in data
    is_parallel = data.get('parallel', False)
    
    h_entry = global_hooks.get('entry', '')
    h_run = global_hooks.get('run', '')
    h_exit = global_hooks.get('exit', '')

    if is_composite:
        if is_parallel:
            p_entries = ""
            p_exits = ""
            p_ticks = ""
            for child_name, child_data in data['states'].items():
                child_path = name_path + [child_name]
                child_c_name = flatten_c_name(child_path)
                region_ptr_name = f"ptr_{child_c_name}"

                if 'initial' not in child_data:
                    sys.exit(f"Error: Region {child_name} missing 'initial'")
                
                initial_leaf = flatten_c_name(child_path + [child_data['initial']])
                p_entries += f"    state_{initial_leaf}_entry(ctx);\n"
                p_ticks += f"    if (ctx->{region_ptr_name}) ctx->{region_ptr_name}(ctx);\n"
                p_exits += f"    // Implicit exit of region {child_name}\n"

                generate_state_machine(child_path, child_data, (region_ptr_name, None), output_lists, global_hooks)

            func_body = COMPOSITE_AND_TEMPLATE.format(
                c_name=my_c_name, state_id=my_id_num, preamble=preamble_filled,
                hook_entry=h_entry, hook_run=h_run, hook_exit=h_exit,
                entry=data.get('entry', ''), exit=data.get('exit', ''), run=data.get('run', ''),
                transitions=trans_code, set_parent=set_parent_code,
                parallel_entries=p_entries, parallel_exits=p_exits, parallel_ticks=p_ticks,
                history_save=hist_save_code
            )
            output_lists['functions'].append(func_body)

        else:
            my_ptr_name = f"ptr_{my_c_name}" 
            my_hist_name = f"hist_{my_c_name}"
            
            output_lists['context_ptrs'].append(f"StateFunc {my_ptr_name};")
            output_lists['context_ptrs'].append(f"StateFunc {my_hist_name};")

            initial_target = flatten_c_name(name_path + [data['initial']])
            history_bool = "true" if data.get('history', False) else "false"
            
            func_body = COMPOSITE_OR_TEMPLATE.format(
                c_name=my_c_name, state_id=my_id_num, preamble=preamble_filled,
                hook_entry=h_entry, hook_run=h_run, hook_exit=h_exit,
                entry=data.get('entry', ''), exit=data.get('exit', ''), run=data.get('run', ''),
                transitions=trans_code, history=history_bool,
                self_ptr=my_ptr_name, self_hist_ptr=my_hist_name,
                initial_target=initial_target, history_save=hist_save_code,
                set_parent=set_parent_code
            )
            output_lists['functions'].append(func_body)
            
            for child_name, child_data in data['states'].items():
                generate_state_machine(name_path + [child_name], child_data, (my_ptr_name, my_hist_name), output_lists, global_hooks)
    else:
        func_body = LEAF_TEMPLATE.format(
            c_name=my_c_name, state_id=my_id_num, preamble=preamble_filled,
            hook_entry=h_entry, hook_run=h_run, hook_exit=h_exit,
            entry=data.get('entry', ''), exit=data.get('exit', ''), run=data.get('run', ''),
            transitions=trans_code, history_save=hist_save_code,
            parent_ptr=parent_run_ptr
        )
        output_lists['functions'].append(func_body)

    output_lists['forwards'].append(f"void state_{my_c_name}_entry(SM_Context* ctx);")
    output_lists['forwards'].append(f"void state_{my_c_name}_run(SM_Context* ctx);")
    output_lists['forwards'].append(f"void state_{my_c_name}_exit(SM_Context* ctx);")

# ---------------------------------------------------------
# DOT GENERATOR
# ---------------------------------------------------------
def find_composites(name_path, data, result_set):
    my_id = flatten_c_name(name_path)
    if 'states' in data:
        result_set.add(my_id)
        for child_name, child_data in data['states'].items():
            find_composites(name_path + [child_name], child_data, result_set)

def generate_dot_recursive(name_path, data, lines, composite_ids):
    my_id = flatten_c_name(name_path)
    is_composite = 'states' in data
    indent = "    " * len(name_path)

    if is_composite:
        lines.append(f"{indent}subgraph cluster_{my_id} {{")
        lines.append(f"{indent}    label = \"{name_path[-1]}\";")
        if data.get('parallel', False):
             lines.append(f"{indent}    style=dashed; color=black; penwidth=1.5; node [style=filled, fillcolor=white];")
             lines.append(f"{indent}    {my_id}_start [shape=point, width=0.15];")
             for child_name, child_data in data['states'].items():
                 child_id = flatten_c_name(name_path + [child_name])
                 tgt = f"{child_id}_start" if child_id in composite_ids else child_id
                 lhead = f"lhead=cluster_{child_id}" if child_id in composite_ids else ""
                 lines.append(f"{indent}    {my_id}_start -> {tgt} [style=dashed, {lhead}];")
        else:
             lines.append(f"{indent}    style=rounded; color=black; penwidth=1.0; node [style=filled, fillcolor=white];")
             if data.get('history', False):
                 lines.append(f"{indent}    {my_id}_hist [shape=circle, label=\"H\", width=0.3];")
             
             init_child_id = flatten_c_name(name_path + [data['initial']])
             tgt = f"{init_child_id}_start" if init_child_id in composite_ids else init_child_id
             lhead = f"lhead=cluster_{init_child_id}" if init_child_id in composite_ids else ""
             lines.append(f"{indent}    {my_id}_start [shape=point, width=0.15];")
             lines.append(f"{indent}    {my_id}_start -> {tgt} [{lhead}];")

        for child_name, child_data in data['states'].items():
            generate_dot_recursive(name_path + [child_name], child_data, lines, composite_ids)
        lines.append(f"{indent}}}")
    else:
        lines.append(f"{indent}{my_id} [label=\"{name_path[-1]}\", shape=box, style=\"rounded,filled\", fillcolor=white];")

    for t in data.get('transitions', []):
        target_path = resolve_target_path(name_path, t['transfer_to'])
        target_id = flatten_c_name(target_path)
        src = f"{my_id}_start" if is_composite else my_id
        ltail = f"ltail=cluster_{my_id}" if is_composite else ""
        tgt = f"{target_id}_start" if target_id in composite_ids else target_id
        lhead = f"lhead=cluster_{target_id}" if target_id in composite_ids else ""
        
        attrs = [x for x in [ltail, lhead] if x]
        raw_test = t.get('test', '')
        attrs.append(f'label="{str(raw_test).replace('"', '\\"')}"')
        attrs.append('fontsize=10')
        lines.append(f"{indent}{src} -> {tgt} [{', '.join(attrs)}];")

def generate_dot_file(root_data):
    composite_ids = set()
    find_composites(['root'], root_data, composite_ids)
    lines = ["digraph StateMachine {", "    compound=true; fontname=\"Arial\"; node [fontname=\"Arial\"]; edge [fontname=\"Arial\"];"]
    generate_dot_recursive(['root'], root_data, lines, composite_ids)
    lines.append("}")
    return "\n".join(lines)

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python sm-builder.py <yaml_file>")

    with open(sys.argv[1], 'r') as f:
        data = yaml.safe_load(f)

    root_data = {
        'initial': data['initial'],
        'states': data['states'],
        'history': False, 
        'entry': "// Root Entry",
        'run': "// Root Run",
        'exit': "// Root Exit"
    }

    hooks = data.get('hooks', {})
    includes = data.get('includes', '')

    outputs = {'context_ptrs': [], 'functions': [], 'forwards': [], 'macros': []}
    
    # 1. Generate Logic
    generate_state_machine(['root'], root_data, None, outputs, hooks)
    
    # 2. Generate Inspectors
    inspect_list = []
    # Note: 'ptr_root' is defined implicitly in the struct as 'root' by init, 
    # but for recursion we need the root of the hierarchy pointers.
    # The root state itself manages 'ptr_root'.
    generate_inspector(['root'], root_data, 'root', inspect_list)

    header = HEADER % (
        state_counter,
        "\n".join(outputs['forwards']), 
        data.get('context', ''), 
        "\n    ".join(outputs['context_ptrs']),
        "\n".join(outputs['macros'])    
    )

    source = SOURCE_TOP % (includes) + "\n".join(outputs['functions'])
    
    # Add Inspector Logic
    source += "\n// --- Inspection Logic ---\n"
    source += "\n".join(inspect_list)
    
    source += f"""
void sm_init(StateMachine* sm) {{
    memset(&sm->ctx, 0, sizeof(sm->ctx));
    sm->ctx.owner = sm;
    state_root_entry(&sm->ctx); 
    sm->root = state_root_run; 
}}

void sm_tick(StateMachine* sm) {{
    if (sm->root) sm->root(&sm->ctx);
}}

void sm_get_state_str(StateMachine* sm, char* buffer, size_t max_len) {{
    size_t offset = 0;
    buffer[0] = '\\0';
    // Start inspection from root
    // We check if root is active
    if (sm->root) inspect_root(&sm->ctx, buffer, &offset, max_len);
}}
"""
    with open("statemachine.h", "w") as f:
        f.write(header)
    with open("statemachine.c", "w") as f:
        f.write(source)

    with open("statemachine.dot", "w") as f:
        f.write(generate_dot_file(root_data))

    print("Generated statemachine.c, .h, and .dot")

if __name__ == "__main__":
    main()
