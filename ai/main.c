#include <stdio.h>
#include <unistd.h> // for usleep
#include <time.h>   // for clock_gettime
#include "statemachine.h"

// Helper: Get real-world time in seconds
double get_time_sec() {
    struct timespec ts;
    // CLOCK_MONOTONIC ensures time always moves forward, even if system time changes
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec / 1000000000.0;
}

int main() {
    StateMachine sm;
    
    // 1. Initialize the machine
    sm_init(&sm);
    
    // 2. Initialize the time BASELINE 
    // (Otherwise the first state might see time=1700000000.0 immediately)
    // Actually, our logic is: time = now - state_entry_time.
    // So we just need to make sure 'now' is correct before the first tick.
    sm.ctx.now = get_time_sec();
    
    // Reset internal timers to this start time so we don't jump immediately
    // (Optional, but good practice if you want robust startup)
    for(int i=0; i<TOTAL_STATES; i++) {
        sm.ctx.state_timers[i] = sm.ctx.now;
    }

    printf("--- Started (Tick Rate: 10Hz) ---\n");

    while(1) {
        // Update time
        sm.ctx.now = get_time_sec();
        
        // Run logic
        sm_tick(&sm);
        
        // Force output to appear immediately (fix for "delayed printing")
        fflush(stdout);
        
        // Sleep 100ms
        usleep(100000); 
    }

    return 0;
}
