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

struct SM_Context {
    void* owner;
    
    // System Time (User must update this in main loop!)
    double now; 
    
    // Array to store entry timestamp for every state ID
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

#endif
"""

SOURCE_TOP = """
#include "statemachine.h"

// Forward Declarations
%s

// --- State Logic ---
"""
# COMMON HEADER for all state functions
# Injects: Unused suppression, Name strings, and Time calculation
FUNC_PREAMBLE = """
    // Suppress unused warning for context
    (void)ctx;

    // Reflection helpers
    const char* state_name = "{short_name}";
    const char* state_full_name = "{full_name}";
    (void)state_name;       // Suppress unused warning
    (void)state_full_name;  // Suppress unused warning

    // Time helper (Duration since entry)
    double time = ctx->now - ctx->state_timers[{state_id}];
    (void)time;             // Suppress unused warning
"""

LEAF_TEMPLATE = """
void state_{full_name}_entry(SM_Context* ctx) {{
    // 1. Snapshot time
    ctx->state_timers[{state_id}] = ctx->now;
    {preamble}
    {history_save}
    {entry}
    ctx->{parent_ptr} = state_{full_name}_run;
    state_{full_name}_run(ctx);
}}

void state_{full_name}_exit(SM_Context* ctx) {{
    {preamble}
    {exit}
}}

void state_{full_name}_run(SM_Context* ctx) {{
    {preamble}
    {run}
    {transitions}
}}
"""

COMPOSITE_TEMPLATE = """
void state_{full_name}_entry(SM_Context* ctx) {{
    // 1. Snapshot time
    ctx->state_timers[{state_id}] = ctx->now;
    {preamble}
    {history_save}
    {entry}
    
    {set_parent}

    if (({history}) && ctx->{self_hist_ptr} != NULL) {{
        ctx->{self_hist_ptr}(ctx);
    }} else {{
        state_{initial_target}_entry(ctx);
    }}
}}

void state_{full_name}_exit(SM_Context* ctx) {{
    {preamble}
    {exit}
}}

void state_{full_name}_run(SM_Context* ctx) {{
    {preamble}
    {run}
    if (ctx->{self_ptr}) ctx->{self_ptr}(ctx);
    {transitions}
}}
"""

# ---------------------------------------------------------
# UTILS
# ---------------------------------------------------------

def flatten_name(path):
    return "_".join(path)

def resolve_target(current_path, target_str):
    if target_str.startswith("root/"):
        parts = target_str.split("/")
        return "state_" + "_".join(parts)
    
    # UPDATED: Handle '..' (Parent)
    if target_str.startswith("../"):
        parent = current_path[:-1] 
        grandparent = parent[:-1]
        target_clean = target_str.replace("../", "")
        return "state_" + "_".join(grandparent + [target_clean])
    
    parent = current_path[:-1]
    return "state_" + "_".join(parent + [target_str])

def resolve_target_dot(current_path, target_str):
    # Same logic but just returns ID string for DOT
    if target_str.startswith("root/"):
        return "_".join(target_str.split("/"))
    if target_str.startswith("../"):
        parent = current_path[:-1] 
        grandparent = parent[:-1]
        target_clean = target_str.replace("../", "")
        return "_".join(grandparent + [target_clean])
    parent = current_path[:-1]
    return "_".join(parent + [target_str])

# ---------------------------------------------------------
# C GENERATOR
# ---------------------------------------------------------

# Global counter for State IDs
state_counter = 0

def generate_state_machine(name_path, data, parent_ptrs, output_lists):
    global state_counter
    my_id_num = state_counter
    state_counter += 1

    my_name = flatten_name(name_path)
    my_ptr_name = f"ptr_{my_name}" 
    my_hist_name = f"hist_{my_name}"

    parent_run_ptr = parent_ptrs[0] if parent_ptrs else None
    parent_hist_ptr = parent_ptrs[1] if parent_ptrs else None

    # Helpers for templates
    hist_save_code = f"ctx->{parent_hist_ptr} = state_{my_name}_entry;" if parent_hist_ptr else ""
    set_parent_code = f"ctx->{parent_run_ptr} = state_{my_name}_run;" if parent_run_ptr else ""

    # Generate Preamble (Vars available in all functions)
    preamble_filled = FUNC_PREAMBLE.format(
        short_name=name_path[-1],
        full_name=my_name,
        state_id=my_id_num
    )

    # Transitions
    trans_code = ""
    for t in data.get('transitions', []):
        target_func = resolve_target(name_path, t['transfer_to'])
        
        # Robust boolean handling
        test_val = t['test']
        if test_val is True: test_cond = "true"
        elif test_val is False: test_cond = "false"
        else: test_cond = str(test_val)

        trans_code += f"""
    if ({test_cond}) {{
        state_{my_name}_exit(ctx);
        {target_func}_entry(ctx); 
        return; 
    }}"""

    is_composite = 'states' in data

    if is_composite:
        output_lists['context_ptrs'].append(f"StateFunc {my_ptr_name};")
        output_lists['context_ptrs'].append(f"StateFunc {my_hist_name};")

        initial_target = flatten_name(name_path + [data['initial']])
        history_bool = "true" if data.get('history', False) else "false"
        
        func_body = COMPOSITE_TEMPLATE.format(
            full_name=my_name,
            state_id=my_id_num,
            preamble=preamble_filled,
            entry=data.get('entry', ''),
            exit=data.get('exit', ''),
            run=data.get('run', ''),
            transitions=trans_code,
            history=history_bool,
            self_ptr=my_ptr_name,
            self_hist_ptr=my_hist_name,
            initial_target=initial_target,
            history_save=hist_save_code,
            set_parent=set_parent_code
        )
        output_lists['functions'].append(func_body)
        
        for child_name, child_data in data['states'].items():
            generate_state_machine(name_path + [child_name], child_data, (my_ptr_name, my_hist_name), output_lists)
            
    else:
        func_body = LEAF_TEMPLATE.format(
            full_name=my_name,
            state_id=my_id_num,
            preamble=preamble_filled,
            entry=data.get('entry', ''),
            exit=data.get('exit', ''),
            run=data.get('run', ''),
            transitions=trans_code,
            history_save=hist_save_code,
            parent_ptr=parent_run_ptr
        )
        output_lists['functions'].append(func_body)

    output_lists['forwards'].append(f"void state_{my_name}_entry(SM_Context* ctx);")
    output_lists['forwards'].append(f"void state_{my_name}_run(SM_Context* ctx);")
    output_lists['forwards'].append(f"void state_{my_name}_exit(SM_Context* ctx);")

# ---------------------------------------------------------
# DOT GENERATOR
# ---------------------------------------------------------
def generate_dot_recursive(name_path, data, lines):
    my_id = flatten_name(name_path)
    is_composite = 'states' in data
    indent = "    " * len(name_path)

    if is_composite:
        lines.append(f"{indent}subgraph cluster_{my_id} {{")
        lines.append(f"{indent}    label = \"{name_path[-1]}\";")
        lines.append(f"{indent}    style=filled; color=lightgrey; node [style=filled,color=white];")
        if data.get('history', False):
             lines.append(f"{indent}    {my_id}_hist [shape=circle, label=\"H\", width=0.3];")
        initial_child = flatten_name(name_path + [data['initial']])
        lines.append(f"{indent}    {my_id}_start [shape=point, width=0.15];")
        lines.append(f"{indent}    {my_id}_start -> {initial_child};")
        for child_name, child_data in data['states'].items():
            generate_dot_recursive(name_path + [child_name], child_data, lines)
        lines.append(f"{indent}}}")
    else:
        lines.append(f"{indent}{my_id} [label=\"{name_path[-1]}\", shape=box];")

    for t in data.get('transitions', []):
        target_id = resolve_target_dot(name_path, t['transfer_to'])
        # Clean label for Dot
        label = str(t.get('test', '')).replace('"', '\\"')
        lines.append(f"{indent}{my_id} -> {target_id} [label=\"{label}\", fontsize=10];")

def generate_dot_file(root_data):
    lines = ["digraph StateMachine {", "    compound=true; fontname=\"Arial\"; node [fontname=\"Arial\"]; edge [fontname=\"Arial\"];"]
    generate_dot_recursive(['root'], root_data, lines)
    lines.append("}")
    return "\n".join(lines)

def main():
    if len(sys.argv) < 2:
        print("Usage: python sm-builder.py <yaml_file>")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        data = yaml.safe_load(f)

    # Wrap root
    root_data = {
        'initial': data['initial'],
        'states': data['states'],
        'history': False, 
        'entry': "// Root Entry",
        'run': "// Root Run",
        'exit': "// Root Exit"
    }

    # Generate C
    outputs = {'context_ptrs': [], 'functions': [], 'forwards': []}
    generate_state_machine(['root'], root_data, None, outputs)
    
    # --- FIX START ---
    # We populate all 3 placeholders (%d, %s, %s) in one go
    header = HEADER % (
        state_counter,
        data.get('context', ''), 
        "\n    ".join(outputs['context_ptrs'])
    )
    # --- FIX END ---

    source = SOURCE_TOP % ("\n".join(outputs['forwards'])) + "\n".join(outputs['functions'])
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

    # Generate DOT
    dot_content = generate_dot_file(root_data)
    with open("statemachine.dot", "w") as f:
        f.write(dot_content)

    print("Generated statemachine.c, .h, and .dot")

if __name__ == "__main__":
    main()
