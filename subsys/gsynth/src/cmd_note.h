#ifndef CMD_NOTE_H
#define CMD_NOTE_H

#include "cmd.h"
#include "note.h"

/*
<duration><string>_<fret>[options]

*/

#define NOTE_CMD "note"

int handle_cmd_note(struct Cmd* cmd, struct App* app);

int parse_note_specifier(char *token, struct Note* nptr, struct App* app);

#endif
