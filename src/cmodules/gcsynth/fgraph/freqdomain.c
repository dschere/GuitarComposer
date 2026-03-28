#include "../gcsynth.h"
#include "freqdomain.h"
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <pthread.h>

struct freq_sample
{
     float freq;
     float amp;
     float left[AUDIO_SAMPLES];
     float right[AUDIO_SAMPLES];

     struct freq_sample* next;
};

struct freq_domain 
{
    // array of linked lists.
    struct freq_sample* channels[NUM_CHANNELS];

    // list of channels being used.
    int clist[NUM_CHANNELS];
    int clist_size;
};

// prevent the need for using malloc/free for speed.
#define MAX_FREQ_SAMPLES_PER_AUDIO_FRAME 1024
static struct freq_sample freq_sample_memory[MAX_FREQ_SAMPLES_PER_AUDIO_FRAME];
static int freq_sample_memory_idx = 0;


static struct freq_domain FreqDomain;
static unsigned int MidiFilterCount = 0; // effects configured that need FreqDomain info.
pthread_mutex_t MidiFilterCount_mutex;

// todo these two below are updated when filters are added and removed from channels
// that have a bandpass filter associated with them.

void midi_filter_increment() {
    pthread_mutex_lock(&MidiFilterCount_mutex);
    if (MidiFilterCount < 0x7FFFFFFF) {
        MidiFilterCount++;
    }
    pthread_mutex_unlock(&MidiFilterCount_mutex);
}

void midi_filter_decrement() {
    pthread_mutex_lock(&MidiFilterCount_mutex);
    if (MidiFilterCount > 0) {
        MidiFilterCount--;
    }
    pthread_mutex_unlock(&MidiFilterCount_mutex);
}

unsigned int get_midi_filter_count() {
    unsigned int count;
    pthread_mutex_lock(&MidiFilterCount_mutex);
    count = MidiFilterCount;
    pthread_mutex_unlock(&MidiFilterCount_mutex);
    return count;
}



void fg_freq_domain_event_clear()
{
    if (MidiFilterCount > 0) {
        memset(&FreqDomain, 0, sizeof(FreqDomain));
    }
} 

void fg_freq_domain_event_add(int channel, float freq, float amp, float* left, float* right)
{
    //todo this gets replaced with asking the filter graph structure 
    //for this channel if a filter graph is in use.
//printf("fg_freq_domain_event_add freq=%f amp=%f \n", freq, amp );
    if (get_midi_filter_count() > 0) {
        struct freq_sample* c_item = &freq_sample_memory[freq_sample_memory_idx];
        int i;

        freq_sample_memory_idx = (freq_sample_memory_idx+1) % MAX_FREQ_SAMPLES_PER_AUDIO_FRAME;

        c_item->freq = freq;
        c_item->amp = amp;
        for(i = 0; i < AUDIO_SAMPLES; i++) {
            c_item->left[i] = left[i];
            c_item->right[i] = right[i];
        }

        if (FreqDomain.channels[channel] == NULL) {
            FreqDomain.clist[FreqDomain.clist_size] = channel;
            FreqDomain.clist_size++;
        }
        c_item->next = FreqDomain.channels[channel]; 
        FreqDomain.channels[channel] = c_item;
    }
}

float midi2freq(int midi_key)
{
    float p = (midi_key - 69)/12.0;
    return 440.0 * pow(2, p);
}

/*
   band/high/low pass filters.
   
   A return > 0 means a match if 0 then left/right are unchanged.
   Otherwise they are populated by audio data within frequence range. 
*/

enum
{
    OP_BANDPASS,
    OP_LOWPASS,
    OP_HIGHPASS
};


static void fs_copy_samples(int count, struct freq_sample* fs, float* left, float *right) 
{
    int i;
    for(i = 0; i < AUDIO_SAMPLES; i++) {
        if (count == 0) {
            left[i] = fs->left[i];
            right[i] = fs->right[i];    
        } else {
            left[i] += fs->left[i];
            right[i] += fs->right[i];
        }
    }
}

static int bandpass_op(int channel, int op, float low, float high, float* left, float* right)
{
    //FUTURE if this channel is live we then need to use a FT to analyze the frequency domain.
    // or disable the call completely.
    struct freq_sample* fs;
    int count = 0;

    for(fs = FreqDomain.channels[channel]; fs != NULL; fs=fs->next) {
//printf("bandpass_op freq=%f amp=%f\n", fs->freq, fs->amp);
        switch( op )
        {
            case OP_BANDPASS:
                if (fs->freq >= low && fs->freq <= high) {
                    fs_copy_samples(count, fs, left, right);
                    count++;    
                } 
                break;
            case OP_HIGHPASS:
                if (fs->freq >= high) {
                    fs_copy_samples(count, fs, left, right);
                    count++;
                }
                break;
            case OP_LOWPASS:
                if (fs->freq <= low) {
                    fs_copy_samples(count, fs, left, right);
                    count++;
                }
                break;
        }
    }

    return count;
}

int fg_bandpass_filter(int channel, float low, float high, float* left, float* right)
{
    return bandpass_op(channel, OP_BANDPASS, low, high, left, right);
}

int fg_highpass_filter(int channel, float freq, float* left, float* right)
{
    return bandpass_op(channel, OP_HIGHPASS, freq, freq, left, right);
}

int fg_lowpass_filter(int channel, float freq, float* left, float* right)
{
    return bandpass_op(channel, OP_LOWPASS, freq, freq, left, right);
}
