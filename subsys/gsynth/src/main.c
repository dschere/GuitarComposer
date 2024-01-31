#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include <fluidsynth.h>

#include "app.h"

static int proc_command_line(struct App* app, int argc, char* argv[]);

int main(int argc, char* argv[]) {
    struct App app;
    int err;
   
    // initialize app structure.
    memset(&app, 0, sizeof(app));  
    app.duration_multiplier = 1.0;

    if ((err = proc_command_line(&app, argc, argv)) != 0) {
        return err;
    }

    if ((err = App_setup(&app)) != 0) {
        return err;
    }

    return App_mainloop(&app);
}

static int proc_command_line(struct App* aptr, int argc, char* argv[]){

    if (argc != 2) {
        fprintf(stderr,"Expected <gsynth> <soundfont>\n");
        return -1;
    }
    memset(aptr->soundfontpath, 0, sizeof(aptr->soundfontpath));
    strncpy(aptr->soundfontpath, argv[1], sizeof(aptr->soundfontpath)-1);
    if (access(aptr->soundfontpath, R_OK) != F_OK){
        fprintf(stderr,"Unable to access file %s\n", aptr->soundfontpath);
        return -1;
    }     

    return 0;
}
