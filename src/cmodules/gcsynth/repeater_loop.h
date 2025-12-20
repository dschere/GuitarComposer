#ifndef __REPEATER_LOOP
#define __REPEATER_LOOP



/**
 * Repeated calls functionPointer
 *  every (AUDIO_SAMPLES / SAMPLE_RATE) seconds, compensating
 *  for processing time. The function pointer returns true if
 *  we are to continue running in the loop.
 */
int repeater_loop( int (*functionPointer)(void *), void *fp_arg );


#endif