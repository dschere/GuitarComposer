#ifndef __HAND_EFFECTS_H
#define __HAND_EFFECTS_H




#define MAX_HAND_EFFECTS 32

enum {
    EV_HAMMERON,
    EV_SLIDE,
    EV_VIBRATO,
    EV_BEND,
    EV_PREBEND_RELEASE,

    NUM_EV_TYPES
};

struct HandEffectEvt {
    int val;
    float fval;
    int ev_type;
};

struct HandEffect {
    struct HandEffectEvt ev_list[MAX_HAND_EFFECTS];
    int num_ev;
};

int parse_hand_effects(struct HandEffect* he, char* ptr);

#endif
