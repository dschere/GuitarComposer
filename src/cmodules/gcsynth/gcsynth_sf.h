#ifndef __GCSYNTH_SF_H
#define __GCSYNTH_SF_H

#define GCSYNTH_NUM_SF_CHANNELS 32
#define GCSYNTH_AUDIO_BUFSIZE 65535

#ifndef MAX_CHANNELS
#define MAX_CHANNELS 64
#endif

typedef void (*AudioChannelFilter)(int channel, float* left, float* right, int samples);

int gcsynth_sf_init(char* sf_file[], int num_fonts, AudioChannelFilter filter_func);


/**
 * bind a channel with a particular audio thread for a given soundfont id
 */
int gcsynth_sf_select(int chan, int sfont_id, int bank, int preset);


int gcsynth_sf_noteon(int chan, int midicode, int vel);
int gcsynth_sf_noteoff(int chan, int midicode);
int gcsynth_sf_pitchrange(int chan, float pitch_range);


void gcsynth_sf_reset();



#endif
