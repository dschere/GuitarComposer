#ifndef __GCSYNTH_ACAPTURE_H
#define __GCSYNTH_ACAPTURE_H
/**
 * Creates and controls two threads 
 * that allow for live capture and playing of audio while optionally
 * playing synth audio (backing track etc.)
 * 
 * Capture thread
 *  opens the audio capture device and sends audio data to a ring buffer
 * 
 * Audio output thread
 *  reads from the ring buffer and sends the audio out. 
 * 
 */
#include "gcsynth.h"


int  StartAudioCapture(char* device);
void StopAudioCapture();

//note: affects are controlled by changing the LIVE_CAPTURE_CHANNEL
//      channel which has been reserved for live audio.

#endif