#include <stdio.h>
#include <stdlib.h>
#include <string.h>


#include "cmd.h"
#include "cmd_note.h"
#include "cmd_chord.h"

#define DEFAULT_DYNAMIC 80


static int DefaultDynamic = DEFAULT_DYNAMIC; 



static int handle_bpm(struct Cmd* cmd, struct App* app) {
    int err = 0;
    if (cmd->num_params == 1) {
        app->bpm = atoi(cmd->params[0]);
    } else {
        fprintf(stderr,"Expected bpm <number>\n");
        err = -1;
    }    
    return err;
}

static int handle_legato(struct Cmd* cmd, struct App* app) {
    int err = 0;
    if (cmd->num_params == 1) {
        app->legato = atoi(cmd->params[0]);
    } else {
        fprintf(stderr,"Expected legato 0|1\n");
        err = -1;
    } 
    return err;
}

static void update_duration_multiplier(struct App* app) {
    float m = 1.0;

    if (app->dotted) {
        m *= 1.5;
    }
    if (app->triplet) {
        m *= 0.66;
    }

    app->duration_multiplier = m;
}

static int toggle_dotted(struct Cmd* cmd, struct App* app) {
    app->dotted = (app->dotted) ? 0: 1;
    update_duration_multiplier(app);
    return 0;
}

static int toggle_triplet(struct Cmd* cmd, struct App* app) {
    app->triplet = (app->triplet) ? 0: 1;
    update_duration_multiplier(app);
    return 0;
}


struct {
    char* command;
    int (*handler)(struct Cmd* cmd, struct App* app);
}DispatchTable[]={{
    NOTE_CMD,
    handle_cmd_note
},{
    "dotted",
    toggle_dotted
},{
    "triplet",
    toggle_triplet
},{
    "bpm",
    handle_bpm
},{
    "legato",
    handle_legato
},{
    CHORD_CMD,
    handle_cmd_chord
},{
    NULL,
    NULL
}};



static void process_options(struct Cmd* cmd) {
    // set default to forte
    char* dyn_labels[] = {"ppp", "pp", "p", "mp", "mf", "f", "ff", "fff", NULL};
    int dyn_values[] = {16, 33, 49, 64, 80, 96, 112, 127, -1};
    int i, p;
    
    cmd->dynamic = DefaultDynamic; 
    cmd->legato = 0;
    cmd->staccato = 0;

    // check optional parameters
    for (p = 0; p < cmd->num_params; p++) {
        for(i = 0; dyn_labels[i] != NULL; i++) {
            if (strcmp(dyn_labels[i], cmd->params[p]) == 0) {
                cmd->dynamic = dyn_values[i]; 
            }
        }
        if (strcmp(cmd->params[p],"legato") == 0) {
            cmd->legato = 1;
        }
        if (strcmp(cmd->params[p],"staccato") == 0) {
            cmd->staccato = 1;
        }
    }

    
}



int Cmd_from_stdin(struct Cmd* cmd)
{
    char* ptr = fgets(cmd->line_buf, sizeof(cmd->line_buf)-1, stdin);
    char* token;
    char* delim = " ";
    char* save_ptr;

    // reuse memory for error messages if needed
    cmd->errmsg = cmd->line_buf;
    
    if (ptr == NULL) {
        strcpy(cmd->errmsg,"fgets failed to read from stdin!\n");
        return -1;
    }

    // remove traing newline.
    ptr[ strlen(ptr) - 1] = '\0';

    token = strtok_r(ptr, delim, &save_ptr);    
    if (token == NULL) {
        strcpy(cmd->errmsg,"Unable to read command from message!\n");
        return -1;
    }

    cmd->command = token;

    for(
        cmd->num_params = 0;
        (cmd->num_params < MAX_PARAMS);
        cmd->num_params++
    ) {
        token = strtok_r(NULL, delim, &save_ptr);
        if (token == NULL) {
            break;
        }
        cmd->params[cmd->num_params] = token;
    }

    // compute options
    process_options(cmd);

    cmd->errmsg = NULL;
    return 0;
}



int Cmd_dispatch(struct Cmd* cmd, struct App* app)
{
    int err = 0;
    int i;

    // inherit settings from app these can be overriden by command options
    // for a specific note/chord ..
    cmd->legato = app->legato;
    cmd->staccato = app->staccato;

    for(i = 0; DispatchTable[i].command != NULL; i++) {
        if (strcmp(DispatchTable[i].command, cmd->command) == 0) {
            err = DispatchTable[i].handler(cmd, app);
            if (err == -1) {
                return err;
            }
        }
    }

    return err;
}



