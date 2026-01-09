#include <stdio.h>
#include <unistd.h> // for sleep
#include "statemachine.h"

int main() {
    StateMachine myMachine;
    
    // IMPORTANT: Link the context back to the machine 
    // (This allows the state functions to modify the machine's state)
    myMachine.ctx.owner = &myMachine;


    // Init the machine (sets initial state)
    sm_init(&myMachine);

    printf("Starting Process Control...\n");

    while(1) {
        // Run one cycle of the machine
        sm_tick(&myMachine);


        sleep(1); 
    }

    return 0;
}
