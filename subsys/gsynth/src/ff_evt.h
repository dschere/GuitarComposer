#ifndef __FT_EVT_H
#define __FT_EVT_H

#include "app.h"

/*
enum
{
   FF_EVT_NOTEON,
   FF_EVT_NOTEOFF,
   FF_EVT_PITCHWHEEL
};
*/

int future_noteon(struct App* app, int chan, int key, int vel, int when);
int future_noteoff(struct App* app, int chan, int key, int when);
int future_bend(struct App* app, int chan, int val, int when);



#endif
