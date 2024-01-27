#include <stdio.h>
#include <string.h>
#include <ctype.h>

#include "hand_effects.h"


static int get_number(char* ptr, int *offset) {
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


int parse_hand_effects(struct HandEffect* he, char* ptr) {
    
    int val;
    int i = 0;
    int offset;

    while(*ptr) {
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

        if (he->ev_list[i].ev_type == EV_VIBRATO) {
            
        } else {
            ptr++;
            val = get_number(ptr, &offset);
            if (val == -1) {
                fprintf(stderr,"Expected fret number got '%s'\n", ptr);
                return -1;
            }
            if (he->ev_list[i].ev_type == EV_BEND || he->ev_list[i].ev_type == EV_PREBEND_RELEASE) {
                if (val > 8) {
                    fprintf(stderr,"Illegal bend value must be 1-8 with 8 being 2 semitones\n");
                    return -1;
                }
            }

            he->ev_list[i].val = val;
            ptr += offset;
        }
        i++;
    }

    he->num_ev = i;

    return 0;
}

