#include <string.h>

#include "cmd_note.h"
#include "ff_evt.h"

// return duration of note in beats
static float duration(char ch) {
    switch(ch){
        case 'W':
            return 4.0;
        case 'H':
            return 2.0;
        case 'Q':
            return 1.0;
        case 'E':
            return 0.5;
        case 'S':
            return 0.25;             
        case 'T':
            return 0.125;
        case 's':
            return 0.0625;
        default:
            return 0; // invalid                     
    }
}

int parse_note_specifier(char *token, struct Note* nptr, struct App* app){
/*
  <duration><string>_<fret>[options]

  duration - 
    W - whole
    H - half
    Q - quater
    E - eigth
    S - sixteenth
    T - thirtysecond 
    s - sixtyforth

  options
    '-' hammer on/pulloff
    '/' slide


*/
    int err = 0;
    int i=0;
    int len = strlen(token);
    int effect_fret;

    if (len == 0) {
        fprintf(stderr,"Syntax error empty note specifier\n");
        return -1;
    } 

    nptr->duration = duration(token[i]);
    if (nptr->duration == 0) {
         fprintf(stderr,"Invalid note specifier %s\n", token);
         return -1;
    }
    i++;

    // parse string number 
    if (token[i] < '1' || token[i] > '6') {
        fprintf(stderr,"Invalid string number must be between 1-6\n");
        return -1;
    }
    nptr->gstr = token[i] - '1';
    i++;

    if (token[i] != '_') {
        fprintf(stderr,"Inavlid %s Expected N<gstring>_<fret>[options]\n", token);
        return -1;
    }
    i++;

    if (token[i] < '0' && token[i] >'9') {
        fprintf(stderr,"Inavlid %s Expected N<gstring>_<fret>[options]\n", token);
        return -1;
    }

    if (token[i+1] >= '0' && token[i+1] <= '9') {
        nptr->fret = 10 * (token[i] - '0') + (token[i+1] - '0');
        i += 2; 
    } else {
        nptr->fret = token[i] - '0';
        i++;
    }

    // use tuning to determine midi key
    nptr->key = app->tuning[nptr->gstr] + nptr->fret; 

    // now look for 'hand' effects: bends, slides, vibrato etc.
    if (i < len) {
        err = parse_hand_effects(&nptr->he, &token[i]);
    }

    return err;
}

static int parse_note(struct Cmd* cmd, struct Note* nptr, struct App* app)
{
    int err = 0;
    int i;

    memset(nptr, 0, sizeof(struct Note));

    // the first argument is the note specifier 
    if (cmd->num_params < 1) {
        fprintf(stderr,"Expected: note ote specifier> [options]\n");
        return -1;
    }
        
    if (parse_note_specifier(cmd->params[0], nptr, app) == -1) {
        return -1;
    }

    // followed by options
    return err;
}

int handle_cmd_note(struct Cmd* cmd, struct App* app) {
    struct Note n;
    int err = parse_note(cmd, &n, app);

    if (err == 0) {
        err = note_proc(&n, cmd, app);
    }     

    return err;
}
