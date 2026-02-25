#ifndef __FREQDOMAIN_H
#define __FREQDOMAIN_H


//-----------------------------------------------------------

/*
   Since we are generating the input sound we can precalculate the 
   frequency domain so that we can do accurate filtering (high/low/band pass)
   without the use of expensive DFT.  
*/

// clear internal stats/buffers etc.

// defined in fgraph/freqdomain.c
void fg_freq_domain_event_clear(); 
void fg_freq_domain_event_add(int channel, float freq, float amp, float* left, float* right);

void midi_filter_created();
void midi_filter_destroyed();

float midi2freq(int midi_key);

int fg_bandpass_filter(int channel, float low, float high, float* left, float* right);
int fg_highpass_filter(int channel, float freq, float* left, float* right);
int fg_lowpass_filter(int channel, float freq, float* left, float* right);




#endif