#include "../gcsynth_filter_graph.h"
#include "../gcsynth.h"

#include <string.h>
#include <math.h>

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
static int MidiFilterCount = 0; // effects configured that need FreqDomain info.


void midi_filter_created() {
    MidiFilterCount++;
}

void midi_filter_destroyed() {
    if (MidiFilterCount > 0) {
        MidiFilterCount--;
    }
}

void fg_freq_domain_event_clear()
{
    if (MidiFilterCount > 0) {
        memset(&FreqDomain, 0, sizeof(FreqDomain));
    }
} 

void fg_freq_domain_event_add(int channel, float freq, float amp, float* left, float* right)
{
    if (MidiFilterCount > 0) {
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


