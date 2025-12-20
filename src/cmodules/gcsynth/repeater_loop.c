#include <bits/time.h>
#include <time.h>

#include "gcsynth.h"


/**
 * @brief Computes the difference between two timespec structs (a - b = result)
 *
 * @param a The minuend (end time)
 * @param b The subtrahend (start time)
 * @param result Pointer to store the difference
 */
static inline void timespec_diff(struct timespec *a, struct timespec *b,
                                 struct timespec *result) {
    /* Perform the subtraction of seconds and nanoseconds */
    result->tv_sec = a->tv_sec - b->tv_sec;
    result->tv_nsec = a->tv_nsec - b->tv_nsec;

    /* Normalize the result if the nanoseconds part is negative */
    if (result->tv_nsec < 0) {
        result->tv_sec--;
        result->tv_nsec += 1000000000L; // 1 second = 1,000,000,000 nanoseconds
    }
}

static inline void timespec_delay_time(struct timespec* ts)
{
    ts->tv_sec = 0;
    ts->tv_nsec = AUDIO_SAMPLES / (SAMPLE_RATE * 1000000000L);
}




/**
 * Repeated calls functionPointer
 *  every (AUDIO_SAMPLES / SAMPLE_RATE) seconds, compensating
 *  for processing time. The function pointer returns true if
 *  we are to continue running in the loop.
 */
int repeater_loop( int (*functionPointer)(void *), void* fp_arg )
{
    int running = 1;
    struct timespec delay_ts, proc_start_ts, proc_end_ts, elapsed_ts, remaining;

    remaining.tv_sec = 0;
    remaining.tv_nsec = 0;

    while (running == 1) {
        clock_gettime(1, &proc_start_ts);
        running = functionPointer(fp_arg);
        if (running == 1) {
            clock_gettime(1, &proc_end_ts);
            timespec_diff(&proc_end_ts, &proc_start_ts, &elapsed_ts);
            // add the remaining time we didn't sleep 
            elapsed_ts.tv_nsec += remaining.tv_nsec;

            // get desired delay time based on sample size and sample rate.
            timespec_delay_time(&delay_ts);
            // subtract computation time causing drift.
            if (elapsed_ts.tv_nsec < delay_ts.tv_nsec) {
                delay_ts.tv_nsec -= elapsed_ts.tv_nsec;
                // delay for creating next frame.
                nanosleep(&delay_ts, &remaining);
            }
        }
    }

    return running;
}
