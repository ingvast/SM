#include <stdio.h>
#include <unistd.h> // for sleep
#include "statemachine.h"

int main() {
    StateMachine myMachine;
    
    // IMPORTANT: Link the context back to the machine 
    // (This allows the state functions to modify the machine's state)
    myMachine.ctx.owner = &myMachine;

    // Custom initialization of your context variables
    myMachine.ctx.input_signal = 0;
    myMachine.ctx.counter = 0;

    // Init the machine (sets initial state)
    sm_init(&myMachine);

    printf("Starting Process Control...\n");

    while(1) {
        // Run one cycle of the machine
        sm_tick(&myMachine);

        // Simulate external inputs changing
	switch( myMachine.ctx.counter ){
		case 1:
			myMachine.ctx.input_signal = 1;
			break;
		case 2:
			myMachine.ctx.input_signal = 0;
			break;
		case 3:
			myMachine.ctx.input_signal = 1;
			break;
	}

        sleep(1); 
    }

    return 0;
}
