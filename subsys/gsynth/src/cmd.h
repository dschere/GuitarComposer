#ifndef API_H
#define API_H

#include "app.h"

/*
Small command language for gsynth. No control flow supported simply
a set of commands. 

<command> <param list>

param list -> [a-zA-Z0-9.] separated by spaces
options <key>=<value>
*/

#define MAX_PARAMS 8

#define LINE_BUF_LENGTH 4096

struct Cmd {
    char line_buf[LINE_BUF_LENGTH];
 
    char* command;
    char* params[MAX_PARAMS];
    int num_params;

    char* errmsg;

    // options
    int dynamic;
    int legato;
    int staccato;
};

int Cmd_from_stdin(struct Cmd* cmd);

int Cmd_dispatch(struct Cmd* cmd, struct App* app);


#endif
