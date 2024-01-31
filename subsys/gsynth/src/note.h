#ifndef __NOTE_H__
#define __NOTE_H__

#include "app.h"
#include "cmd.h"

#include "hand_effects.h"


#define MAX_HAMMERON_PULLOFFS 8

struct Note {
    int fret;
    int gstr;
    float duration;
    // for note comamnd its zero (immediate)
    // for a chord this used to create strumming effect.
    int delay; 
    int dynamic;
    int key; // computed using tuning.

    struct HandEffect he;

    // use by struct Chord
    int used;
};

int note_proc(struct Note* nptr, struct Cmd* cmd, struct App* app);



#endif
