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

typedef struct SM_Context SM_Context;
typedef void (*StateFunc)(SM_Context* ctx);

struct SM_Context {
    void* owner;         
    
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

LEAF_TEMPLATE = """
void state_{full_name}_entry(SM_Context* ctx) {{
    {history_save}
    {entry}
    ctx->{parent_ptr} = state_{full_name}_run;
    state_{full_name}_run(ctx);
}}

void state_{full_name}_exit(SM_Context* ctx) {{
    {exit}
}}

void state_{full_name}_run(SM_Context* ctx) {{
    {run}
    {transitions}
}}
"""

COMPOSITE_TEMPLATE = """
void state_{full_name}_entry(SM_Context* ctx) {{
    {history_save}
    {entry}
    
    {set_parent}

    // History vs Initial
    if (({history}) && ctx->{self_hist_ptr} != NULL) {{
        ctx->{self_hist_ptr}(ctx); // Resume saved child
    }} else {{
        state_{initial_target}_entry(ctx); // Default start
    }}
}}

void state_{full_name}_exit(SM_Context* ctx) {{
    {exit}
}}

void state_{full_name}_run(SM_Context* ctx) {{
    {run}
    if (ctx->{self_ptr}) ctx->{self_ptr}(ctx);
    {transitions}
}}
"""

# ---------------------------------------------------------
# GENERATOR LOGIC
# ---------------------------------------------------------

def flatten_name(path):
    return "_".join(path)

def resolve_target(current_path, target_str):
    if target_str.startswith("root/"):
        parts = target_str.split("/")
        return "state_" + "_".join(parts)
    if target_str.startswith(".../"):
        parent = current_path[:-1] 
        grandparent = parent[:-1]
        target_clean = target_str.replace(".../", "")
        return "state_" + "_".join(grandparent + [target_clean])
    
    parent = current_path[:-1]
    return "state_" + "_".join(parent + [target_str])

def generate_state_machine(name_path, data, parent_ptrs, output_lists):
    my_name = flatten_name(name_path)
    
    my_ptr_name = f"ptr_{my_name}" 
    my_hist_name = f"hist_{my_name}"

    parent_run_ptr = parent_ptrs[0] if parent_ptrs else None
    parent_hist_ptr = parent_ptrs[1] if parent_ptrs else None

    # History Save Code
    if parent_hist_ptr:
        hist_save_code = f"ctx->{parent_hist_ptr} = state_{my_name}_entry;"
    else:
        hist_save_code = "// Root: No parent history"

    # Parent Set Code
    if parent_run_ptr:
        set_parent_code = f"ctx->{parent_run_ptr} = state_{my_name}_run;"
    else:
        set_parent_code = "// Root: Handled by sm_init"

    # Transitions
    trans_code = ""
    for t in data.get('transitions', []):
        target_func = resolve_target(name_path, t['transfer_to'])
        # REMOVED: explicit extern declaration
        trans_code += f"""
    if ({t['test']}) {{
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
            entry=data.get('entry', ''),
            exit=data.get('exit', ''),
            run=data.get('run', ''),
            transitions=trans_code,
            history_save=hist_save_code,
            parent_ptr=parent_run_ptr
        )
        output_lists['functions'].append(func_body)

    # Add Forward Decls to global list
    output_lists['forwards'].append(f"void state_{my_name}_entry(SM_Context* ctx);")
    output_lists['forwards'].append(f"void state_{my_name}_run(SM_Context* ctx);")
    output_lists['forwards'].append(f"void state_{my_name}_exit(SM_Context* ctx);")

def main():
    if len(sys.argv) < 2:
        print("Usage: python sm-builder.py <yaml_file>")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        data = yaml.safe_load(f)

    outputs = {'context_ptrs': [], 'functions': [], 'forwards': []}
    
    root_data = {
        'initial': data['initial'],
        'states': data['states'],
        'history': False, 
        'entry': "// Root Entry",
        'run': "// Root Run",
        'exit': "// Root Exit"
    }
    
    generate_state_machine(['root'], root_data, None, outputs)
    
    header = HEADER % (data.get('context', ''), "\n    ".join(outputs['context_ptrs']))
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
    print("Generated clean nested statemachine.")

if __name__ == "__main__":
    main()
