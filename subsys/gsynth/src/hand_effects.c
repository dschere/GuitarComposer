#include <stdio.h>
#include <string.h>
#include <ctype.h>

#include "hand_effects.h"


static int get_int(char* ptr, int *offset) {
    int n = -1;

    *offset = 0;
    if (isdigit(*ptr)) {
        n = *ptr - '0';
        ptr++;
        *offset = *offset + 1;
        if (isdigit(*ptr)) {
            n = (n * 10) + (*ptr - '0');
            *offset = *offset + 1;
        }
    }

    return n;        
}


static float get_float(const char *ptr, int *offset) {
    float f = 0;
    int i;


    for(i = 0; isdigit(ptr[i]) || ptr[i] == '.'; i++)
      ;

    if (i > 0) {
        sscanf(ptr,"%f",&f);
    }
    *offset = i;
    
    return f;
}


int parse_hand_effects(struct HandEffect* he, char* ptr) {
    
    int val;
    int i;
    int offset;

    for(i = 0; i < MAX_HAND_EFFECTS && (*ptr); i++) {
        switch(*ptr) {
            case '-':
                he->ev_list[i].ev_type = EV_HAMMERON;                
                break;
            case '/':                
                he->ev_list[i].ev_type = EV_SLIDE;
                break;
            case '^':
                he->ev_list[i].ev_type = EV_BEND;
                break;
            case 'v':
                he->ev_list[i].ev_type = EV_VIBRATO;
                break;
            case '!':
                he->ev_list[i].ev_type = EV_PREBEND_RELEASE;
                break;
            default:
                fprintf(stderr,"Unknown hand effect %c\n", *ptr);
                return -1;
        }
        ptr++;
        switch(he->ev_list[i].ev_type) {
            case EV_HAMMERON:
            case EV_SLIDE:
                he->ev_list[i].val = get_int(ptr, &offset);
                if (offset == 0) {
                    fprintf(stderr,"...%s  Hammeron and slides expect an integer value afterwords\n",ptr);
                    return -1;
                }
                break;
            default:
                he->ev_list[i].fval = get_float(ptr, &offset);
                if (offset == 0) {
                    fprintf(stderr,"...%s Floating point value expected\n", ptr);
                    return -1;
                }
                break;
        }
        ptr += offset;
    }

    he->num_ev = i;
    return 0;
}

