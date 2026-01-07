import yaml
import sys

# ---------------------------------------------------------
# TEMPLATES (C Code Snippets)
# ---------------------------------------------------------
HEADER_TEMPLATE = """
#ifndef STATEMACHINE_H
#define STATEMACHINE_H

#include <stdio.h>
#include <stdbool.h>

// Context Structure: Holds your machine's variables
typedef struct {
    %s
} SM_Context;

// State Function Pointer Definition
typedef void (*StateFunc)(SM_Context* ctx);

// State Machine Struct
typedef struct {
    StateFunc current_state;
    StateFunc next_state;
    SM_Context ctx;
} StateMachine;

// Function Prototypes
void sm_init(StateMachine* sm);
void sm_tick(StateMachine* sm);

#endif
"""

SOURCE_TEMPLATE = """
#include "statemachine.h"

// Forward declarations of state functions
%s

// --- State Logic ---
%s

// --- Core Machine Logic ---

void sm_init(StateMachine* sm) {
    // Initialize Context
    // (In a real scenario, you might memset 0 here)
    
    // Set initial state
    sm->current_state = state_%s_entry;
    sm->next_state = NULL;
}

void sm_tick(StateMachine* sm) {
    if (sm->current_state != NULL) {
        sm->current_state(&sm->ctx);
    }
    
    // Check if a transition occurred
    if (sm->next_state != NULL) {
        // Execute the transition
        sm->current_state = sm->next_state;
        sm->next_state = NULL;
        
        // Immediately enter the new state
        sm->current_state(&sm->ctx);
    }
}
"""

STATE_FUNC_TEMPLATE = """
// State: {name}
void state_{name}_run(SM_Context* ctx); // Forward decl for run

void state_{name}_entry(SM_Context* ctx) {{
    // 1. Run the user's entry code
    {entry_code}

    // 2. UPDATE THE POINTER: Switch to the RUN function for the next tick
    ((StateMachine*)ctx->owner)->current_state = state_{name}_run;

    // 3. Run the logic immediately for this tick
    state_{name}_run(ctx);
}}

void state_{name}_exit(SM_Context* ctx) {{
    // EXIT CODE
    {exit_code}
}}

void state_{name}_run(SM_Context* ctx) {{
    // RUN CODE (Repeated logic)
    {run_code}

    // TRANSITIONS
    {transition_code}
}}
"""

TRANSITION_TEMPLATE = """
    if ({test}) {{
        state_{current}_exit(ctx);
        // We set the pointer for the NEXT tick (or immediate, depending on engine design)
        // Here we return to the engine to handle the swap to avoid stack recursion depth issues
        extern void state_{target}_entry(SM_Context*); // forward decl specific to this scope
        // We cheat slightly and use a global or pass the SM struct. 
        // For this simple version, we assume we need to return or set a flag.
        // But to keep it pure C without globals, we need the SM struct. 
        // For simplicity, we assume the user code sets a 'next_state' variable 
        // but we can't easily access 'sm' here without passing it.
        // Let's rely on a helper or just return.
    }}
"""

# To make the generated C cleaner and robust, we will change the StateFunc signature 
# in the generator logic below to allow returning the next state.

# ---------------------------------------------------------
# GENERATOR LOGIC
# ---------------------------------------------------------

def generate_c_code(data):
    states = data['states']
    initial_state = data['initial']
    context_vars = data.get('context', 'int dummy;')

    # 1. Generate Forward Declarations
    forward_decls = []
    for name in states:
        forward_decls.append(f"void state_{name}_entry(SM_Context* ctx);")

    # 2. Generate State Functions
    state_functions = []
    
    for name, logic in states.items():
        entry_code = logic.get('entry', '// No entry code')
        exit_code = logic.get('exit', '// No exit code')
        run_code = logic.get('run', '// No run code')
        
        # Build Transitions
        # We need a way to signal a state change. 
        # In this simple pointer model, we will use a specific pattern:
        # We need to access the 'sm' struct to set next_state. 
        # For this prototype, we will assume the generated C header defines a macro or 
        # we change the signature. Let's stick to the cleanest C approach:
        # The transition code acts on 'ctx' or returns. 
        
        trans_logic = ""
        transitions = logic.get('transitions', [])
        
        # To handle the 'transfer-to', we need a dirty trick in C or a clean engine.
        # Clean engine: The state functions take (StateMachine* sm).
        # Let's update the templates implicitly here.
        
        for t in transitions:
            target = t['transfer_to']
            test = t['test']
            # Note: We cast ctx back to StateMachine* if we need to set next_state,
            # but simpler is to expect the user to include the header and know the struct layout,
            # or simply assume 'sm_set_next' exists.
            # Let's generate specific code:
            
            trans_block = f"""
    if ({test}) {{
        state_{name}_exit(ctx);
        // Hack: We need the function pointer for the target
        extern void state_{target}_entry(SM_Context*);
        // We need to tell the engine to switch. 
        // In a flat machine, we can return the function pointer, 
        // but void is requested. We will use a wrapper struct trick in V2.
        // For now, let's inject a "hidden" global or assume the ctx has a back-pointer.
        // Let's assume SM_Context has a void* owner;
        ((StateMachine*)ctx->owner)->next_state = state_{target}_entry;
        return; 
    }}"""
            trans_logic += trans_block

        func_body = STATE_FUNC_TEMPLATE.format(
            name=name,
            entry_code=entry_code,
            exit_code=exit_code,
            run_code=run_code,
            transition_code=trans_logic,
            current=name
        )
        state_functions.append(func_body)

    # 3. Assemble Source
    # We need to inject the "owner" pointer into the Context struct definition
    context_vars_patched = "void* owner;\n" + context_vars
    
    header = HEADER_TEMPLATE % (context_vars_patched)
    source = SOURCE_TEMPLATE % (
        "\n".join(forward_decls),
        "\n".join(state_functions),
        initial_state
    )

    return header, source

def main():
    if len(sys.argv) < 2:
        print("Usage: python generator.py machine.yaml")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        data = yaml.safe_load(f)

    header, source = generate_c_code(data)

    with open("statemachine.h", "w") as f:
        f.write(header)
    
    with open("statemachine.c", "w") as f:
        f.write(source)

    print("Generated statemachine.c and statemachine.h")

if __name__ == "__main__":
    main()
