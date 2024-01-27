#ifndef APP_H
#define APP_H

#include <fluidsynth.h>

#define MAX_SOUNDFONT_PATH 1024
#define NUM_GSTRINGS 6
#define GSTR_NOT_PLAYING -1 
#define DEFAULT_BPM 120


struct App {
    char soundfontpath[MAX_SOUNDFONT_PATH];

    fluid_settings_t *settings;
    fluid_synth_t *synth;
    fluid_audio_driver_t *adriver;
    fluid_sequencer_t *sequencer;

    short synth_destination;
    short client_destination;

    int font_id;
    int gstring_state[NUM_GSTRINGS];
    int tuning[NUM_GSTRINGS];

    // default settings
    // can be altered dynamically using settings command 
    int bpm;
    int dynamic;
    int legato;
    int staccato;


};

int App_setup(struct App* app);
int App_mainloop(struct App* app);
void App_schedule_noteon(struct App* app, int chan, short key, short vel, unsigned int ticks);


#endif
