#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#include "cmd_chord.h"
#include "cmd_note.h"

/*
chord <duration> <note>[,<note>] opts

*/


int handle_cmd_chord(struct Cmd* cmd, struct App* app)
{
    int err = 0;
    float duration_in_beats;
    char duration_sym;
    int delay;
    char buffer[256];
    char* save_ptr;
    char* ptr;
    int duration_in_ms;
    struct Chord chord;
    int i;
    int n = 0;

    memset((void *) &chord, 0, sizeof(chord));

    if (cmd->num_params < 2) {
        fprintf(stderr,"Expected chord <duration> <note>[,<note>] [options]\n");
        return -1;
    }

    duration_sym = cmd->params[0][0];
    
    // the parsing is identical except for the first character
    // so prepend the duration character infront of each note.
    for(i = 0, ptr = strtok_r(cmd->params[1],",",&save_ptr); 
        (i < MAX_NOTES) && ptr; 
        i++) {
        
        sprintf(buffer, "%c%s", duration_sym, ptr);
        chord.notes[i].dynamic = cmd->dynamic;
        err = parse_note_specifier(buffer, &chord.notes[i], app);
        if (err) {
            fprintf(stderr,"Problem was the found with note %d\n", i);
            return -1;
        }
 
        ptr = strtok_r(NULL,",",&save_ptr);
    }
    chord.num_notes = i;

    chord.stroke = NO_STROKE;
    chord.percentage = 0.5;


    for(i = 2; i < cmd->num_params; i++) {
        if        (strcmp(cmd->params[i],"up") == 0) {
            chord.stroke = UPSTROKE;
        } else if (strcmp(cmd->params[i],"down") == 0) {
            chord.stroke = DOWNSTROKE;
        } else if (isdigit(cmd->params[i][0])) {
            // get the value from 0-100 that represents the percentage of
            // time used for the stroke.
            sscanf(cmd->params[i],"%d", &n);
            chord.percentage = n * 0.01;
        }
    }

    duration_in_beats = duration(duration_sym);
    duration_in_ms = 1000 * (duration_in_beats * (60.0 / app->bpm));
    delay = 0;
    switch(chord.stroke) {
        case DOWNSTROKE:
            for(i = 0; i < chord.num_notes; i++) {
                chord.notes[i].delay = delay;
                // printf("note_proc i=%d, delay=%d, gstr=%d, fret=%d\n",
                //     i, chord.notes[i].delay, chord.notes[i].gstr, chord.notes[i].fret );
                if (note_proc(&chord.notes[i], cmd, app)) 
                    return -1;
                delay += (duration_in_ms/chord.num_notes) * chord.percentage;
            }    
            break;
        case UPSTROKE:    
            for(i = chord.num_notes-1; i > 0 ; i--) {
                chord.notes[i].delay = delay;
                //printf("note_proc i=%d, delay=%d, gstr=%d, fret=%d\n",
                //    i, chord.notes[i].delay, chord.notes[i].gstr, chord.notes[i].fret );
                if (note_proc(&chord.notes[i], cmd, app)) 
                    return -1;
                delay += (duration_in_ms/chord.num_notes) * chord.percentage;
            }
            break;
        default:
            for(i = 0; i < chord.num_notes; i++) {
                //printf("note_proc i=%d, delay=%d, gstr=%d, fret=%d\n",
                //    i, chord.notes[i].delay, chord.notes[i].gstr, chord.notes[i].fret );
                if (note_proc(&chord.notes[i], cmd, app)) 
                    return -1;
            }

    }

    return err;
}