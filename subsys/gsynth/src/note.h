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
    int dynamic;
    int key; // computed using tuning.

    struct HandEffect he;
};

int note_proc(struct Note* nptr, struct Cmd* cmd, struct App* app);



#endif
