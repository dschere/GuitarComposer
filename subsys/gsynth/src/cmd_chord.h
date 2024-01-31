#ifndef CMD_CHORD_H
#define CMD_CHORD_H

#include "cmd.h"
#include "app.h"
#include "note.h"

#define CHORD_CMD "chord"

#define MAX_NOTES 6

enum {
    UPSTROKE,
    DOWNSTROKE,
    NO_STROKE
};

struct Chord {
    struct Note notes[MAX_NOTES];
    int num_notes;
    int stroke;
    float percentage; // what portion of the  
    
};

int handle_cmd_chord(struct Cmd* cmd, struct App* app);


#endif
