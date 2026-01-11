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

// --- Forward Declarations (Visible for Macros) ---
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

// --- State Check Macros ---
#define IN_STATE(statename) IN_STATE_##statename
%s

#endif
"""

SOURCE_TOP = """
#include "statemachine.h"

// --- User Includes / Helper Functions ---
%s

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
# PATH & LCA LOGIC
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
# C GENERATOR
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

    # 1. Generate State Check Macro
    # If I have a parent pointer, checking if I am active means checking if 
    # my parent points to MY run function.
    if parent_run_ptr:
        macro_def = f"#define IN_STATE_{my_c_name} (ctx->{parent_run_ptr} == state_{my_c_name}_run)"
        output_lists['macros'].append(macro_def)

    # Helpers
    hist_save_code = f"ctx->{parent_hist_ptr} = state_{my_c_name}_entry;" if parent_hist_ptr else ""
    set_parent_code = f"ctx->{parent_run_ptr} = state_{my_c_name}_run;" if parent_run_ptr else ""

    preamble_filled = FUNC_PREAMBLE.format(
        short_name=name_path[-1],
        display_name=my_disp_name, 
        state_id=my_id_num
    )

    # --- TRANSITIONS ---
    trans_code = ""
    for t in data.get('transitions', []):
        target_path_list = resolve_target_path(name_path, t['transfer_to'])
        target_c_func = "state_" + flatten_c_name(target_path_list)
        
        exit_funcs = get_exit_sequence(name_path, target_path_list)
        exit_calls = ""
        for exit_func in exit_funcs:
            exit_calls += f"        {exit_func}(ctx);\n"

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
            # --- PARALLEL LOGIC ---
            p_entries = ""
            p_exits = ""
            p_ticks = ""
            
            for child_name, child_data in data['states'].items():
                child_path = name_path + [child_name]
                child_c_name = flatten_c_name(child_path)
                
                # We calculate the pointer name that the child WILL use
                region_ptr_name = f"ptr_{child_c_name}"
                
                # FIX: Do NOT append to output_lists['context_ptrs'] here.
                # The child generation step below will see it is composite and add it.

                if 'initial' not in child_data:
                    print(f"Error: Region {child_name} missing 'initial'")
                    sys.exit(1)
                
                initial_leaf = flatten_c_name(child_path + [child_data['initial']])
                p_entries += f"    state_{initial_leaf}_entry(ctx);\n"
                p_ticks += f"    if (ctx->{region_ptr_name}) ctx->{region_ptr_name}(ctx);\n"
                p_exits += f"    // Implicit exit of region {child_name}\n"

                generate_state_machine(child_path, child_data, (region_ptr_name, None), output_lists, global_hooks)

            func_body = COMPOSITE_AND_TEMPLATE.format(
                c_name=my_c_name, state_id=my_id_num, preamble=preamble_filled,
                hook_entry=h_entry, hook_run=h_run, hook_exit=h_exit,
                entry=data.get('entry', ''), exit=data.get('exit', ''), run=data.get('run', ''),
                transitions=trans_code,
                set_parent=set_parent_code,
                parallel_entries=p_entries,
                parallel_exits=p_exits,
                parallel_ticks=p_ticks,
                history_save=hist_save_code
            )
            output_lists['functions'].append(func_body)

        else:
            # --- STANDARD OR LOGIC ---
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
                transitions=trans_code,
                history=history_bool,
                self_ptr=my_ptr_name, self_hist_ptr=my_hist_name,
                initial_target=initial_target,
                history_save=hist_save_code,
                set_parent=set_parent_code
            )
            output_lists['functions'].append(func_body)
            
            for child_name, child_data in data['states'].items():
                generate_state_machine(name_path + [child_name], child_data, (my_ptr_name, my_hist_name), output_lists, global_hooks)
            
    else:
        # LEAF
        func_body = LEAF_TEMPLATE.format(
            c_name=my_c_name, state_id=my_id_num, preamble=preamble_filled,
            hook_entry=h_entry, hook_run=h_run, hook_exit=h_exit,
            entry=data.get('entry', ''), exit=data.get('exit', ''), run=data.get('run', ''),
            transitions=trans_code,
            history_save=hist_save_code,
            parent_ptr=parent_run_ptr
        )
        output_lists['functions'].append(func_body)

    output_lists['forwards'].append(f"void state_{my_c_name}_entry(SM_Context* ctx);")
    output_lists['forwards'].append(f"void state_{my_c_name}_run(SM_Context* ctx);")
    output_lists['forwards'].append(f"void state_{my_c_name}_exit(SM_Context* ctx);")

# ---------------------------------------------------------
# DOT GENERATOR
# ---------------------------------------------------------
def generate_dot_recursive(name_path, data, lines):
    my_id = flatten_c_name(name_path)
    is_composite = 'states' in data
    indent = "    " * len(name_path)

    if is_composite:
        lines.append(f"{indent}subgraph cluster_{my_id} {{")
        lines.append(f"{indent}    label = \"{name_path[-1]}\";")
        if data.get('parallel', False):
            lines.append(f"{indent}    style=dashed; color=black; node [style=filled,color=white];")
            lines.append(f"{indent}    {my_id}_start [shape=point, width=0.15];")
            for child_name, child_data in data['states'].items():
                 init_leaf = flatten_c_name(name_path + [child_name] + [child_data['initial']])
                 lines.append(f"{indent}    {my_id}_start -> {init_leaf} [style=dashed];")
        else:
            lines.append(f"{indent}    style=filled; color=lightgrey; node [style=filled,color=white];")
            if data.get('history', False):
                 lines.append(f"{indent}    {my_id}_hist [shape=circle, label=\"H\", width=0.3];")
            initial_child = flatten_c_name(name_path + [data['initial']])
            lines.append(f"{indent}    {my_id}_start [shape=point, width=0.15];")
            lines.append(f"{indent}    {my_id}_start -> {initial_child};")

        for child_name, child_data in data['states'].items():
            generate_dot_recursive(name_path + [child_name], child_data, lines)
        lines.append(f"{indent}}}")
    else:
        lines.append(f"{indent}{my_id} [label=\"{name_path[-1]}\", shape=box];")

    for t in data.get('transitions', []):
        target_path = resolve_target_path(name_path, t['transfer_to'])
        target_id = flatten_c_name(target_path)
        raw_test = t.get('test', '')
        label = str(raw_test).replace('"', '\\"')
        lines.append(f"{indent}{my_id} -> {target_id} [label=\"{label}\", fontsize=10];")

def generate_dot_file(root_data):
    lines = ["digraph StateMachine {", "    compound=true; fontname=\"Arial\"; node [fontname=\"Arial\"]; edge [fontname=\"Arial\"];"]
    generate_dot_recursive(['root'], root_data, lines)
    lines.append("}")
    return "\n".join(lines)

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("Usage: python sm-builder.py <yaml_file>")
        sys.exit(1)

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
    generate_state_machine(['root'], root_data, None, outputs, hooks)
    
    header = HEADER % (
        state_counter,
        "\n".join(outputs['forwards']), # Forward decls
        data.get('context', ''), 
        "\n    ".join(outputs['context_ptrs']),
        "\n".join(outputs['macros'])    # Macros
    )

    source = SOURCE_TOP % (includes) + "\n".join(outputs['functions'])
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
"""
    with open("statemachine.h", "w") as f:
        f.write(header)
    with open("statemachine.c", "w") as f:
        f.write(source)

    dot_content = generate_dot_file(root_data)
    with open("statemachine.dot", "w") as f:
        f.write(dot_content)

    print("Generated statemachine.c, .h, and .dot")

if __name__ == "__main__":
    main()
