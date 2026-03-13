
#include "fgraph.h"


#include <glib.h>
#include <stdio.h>
#include <malloc.h>
#include <string.h>
#include <pthread.h>

#include "bandpass.h"
#include "gainbalance.h"
#include "mixer.h"
#include "splitter.h"
#include "effect.h"


static GHashTable* fgraph_db = NULL;
static pthread_mutex_t fgraph_db_mutex;


static void
print_entry(gpointer key, gpointer value, gpointer user_data)
{
    const char *skey = key;               /* key is a NUL-terminated string */
    struct fgraph_base* base = value;

    printf("        key (%s), value node type %d\n", skey, base->type);
}

static void print_fgraph(struct fgraph* fg)
{
    printf("Contents of filter graph:\n");

    printf("    node table:\n");
    g_hash_table_foreach(fg->nodes, print_entry, NULL);
}

int fg_init()
{
    if ((fgraph_db = g_hash_table_new(g_str_hash, g_str_equal)) == NULL) {
        fprintf(stderr,"Unable to create fgraph hash table!\n");
        return -1;
    }

    if (pthread_mutex_init(&fgraph_db_mutex, NULL) != 0) {
        perror("Mutex initialization failed");
        return 1;
    }

    return 0;
}

struct fgraph_node* fg_lookup_node(struct fgraph* fg, char* uuid)
{
    struct fgraph_node* n = NULL;
    if (fg != NULL && fg->nodes != NULL) {
        n = g_hash_table_lookup(fg->nodes, uuid);
    }
    return n;
}

struct fgraph_connection* fg_lookup_connection(struct fgraph* fg, char* uuid)
{
    struct fgraph_connection* c = NULL; 
    if (fg != NULL) {
        c = g_hash_table_lookup(fg->connections, uuid);
    }
    return c;
}


struct fgraph_base* lookup_fgraph_object(char* uuid, int expected_type)
{
    struct fgraph_base* item = NULL;

    if (fgraph_db != NULL) {
        pthread_mutex_lock(&fgraph_db_mutex);
        item = g_hash_table_lookup(fgraph_db, uuid);
        pthread_mutex_unlock(&fgraph_db_mutex);

        if (item != NULL) {
            if ((expected_type != -1) && (item->type != expected_type)) {
                char errmsg[1024];
                sprintf(errmsg,"lookup_fgraph_object wrong type! received %d expected %d\n", item->type, expected_type);
                fprintf(stderr, "%s", errmsg);
                gcsynth_raise_exception(errmsg);
                item = NULL;
            }
        }
    }

    return item;
}


void fg_create(char* uuid)
{
    if (fgraph_db != NULL) {
        struct fgraph* fg = malloc(sizeof(struct fgraph));
        memset(fg, 0, sizeof(struct fgraph));
        strncpy(fg->base.uuid, uuid, sizeof(fg->base.uuid)-1);

        fg->base.type = FG_GRAPH;
        fg->nodes  = g_hash_table_new(g_str_hash, g_str_equal);
        fg->connections = g_hash_table_new(g_str_hash, g_str_equal);

        g_hash_table_insert(fgraph_db, fg->base.uuid, fg);
        //printf("Created node type %d with uuid = %s\n", fg->base.type, fg->base.uuid);
    }
}

void fg_set_enable(char* uuid, int enabled)
{
    struct fgraph* fg = g_hash_table_lookup(fgraph_db, uuid);

    if (fg == NULL) {
        return;
    }

    fg->enabled = enabled;
}


void fg_destroy(char* uuid)
{
    if (fgraph_db != NULL) {
        struct fgraph* fg = g_hash_table_lookup(fgraph_db, uuid);

        if (fg == NULL) {
            return;
        }

        // detetach from channel.

        // remove nodes and connections from graph.
        if (fg->nodes != NULL) {
            g_hash_table_destroy(fg->nodes);
        }
        if (fg->connections != NULL) {
            g_hash_table_destroy(fg->connections);
        }

        // remove entry.
        g_hash_table_remove(fgraph_db, uuid);
        //printf("Deleted node type %d with uuid = %s\n", fg->base.type, fg->base.uuid);

        free(fg);
    }
}

int fg_setup_effect(char* fg_uuid, char* node_uuid, char* path, char* label)
{
    int ret = -1;
    char errmsg[256];
    struct fgraph* fg = g_hash_table_lookup(fgraph_db, fg_uuid);
    struct fgraph_base* n;
    struct fgraph_effect* e;
    
    if (fg == NULL) {
        sprintf(errmsg,"fg_setup_effect: Unable to find filter graph for uuid %s\n", fg_uuid);
        gcsynth_raise_exception(errmsg);
    } else {
        n = fg_lookup_node(fg, node_uuid);
        if (n == NULL) {
            sprintf(errmsg,"fg_setup_effect: no match for effect uuid (%s) in fg %s\n", 
                node_uuid, fg_uuid);
            print_fgraph(fg);
            gcsynth_raise_exception(errmsg);
        } else if (n->type != FG_NODE_TYPE_EFFECT) {
            sprintf(errmsg,"fg_setup_effect: graph node not an effect type!\n");
            gcsynth_raise_exception(errmsg);
        } else {
            e = (struct fgraph_effect *) n; // safe to cast.

            //Note: this function calls gcsynth_raise_exception if null is returned,
            e->filter = gcsynth_filter_new_ladspa(path, label);
            if (e->filter != NULL) {
                printf("initialized %s from %s\n", label, path);
                ret = 0;
            } 
        }  
    }

    return ret;
}



int fg_create_node(char* fg_uuid, char* node_uuid, int node_type)
{
    struct fgraph* fg = (struct fgraph*) lookup_fgraph_object(fg_uuid, FG_GRAPH);
    int ret = 0;

    if (fg != NULL) {
        switch(node_type) {
            // create a low pass filter
            case  FG_NODE_TYPE_LOWPASS: {
                    struct fgraph_lowpass* node = malloc(sizeof(struct fgraph_lowpass));
                    memset(node, 0, sizeof(struct fgraph_lowpass));
                    strncpy(node->node.base.uuid, node_uuid, sizeof(node->node.base.uuid)-1);
                    node->node.base.type =  FG_NODE_TYPE_LOWPASS;
                    node->freq = 261.63;
                    node->node.run = lowpass_run;
                    node->node.enabled = 1;
                    g_hash_table_insert(fg->nodes, node->node.base.uuid, node);
                    //printf("Created node type %d with uuid = %s\n", node->node.base.type, node_uuid); 
                }
                break;
            // create a high pass filter
            case  FG_NODE_TYPE_HIGHPASS:{
                    struct fgraph_highpass* node = malloc(sizeof(struct fgraph_highpass));
                    memset(node, 0, sizeof(struct fgraph_lowpass));
                    strncpy(node->node.base.uuid, node_uuid, sizeof(node->node.base.uuid)-1);
                    node->node.base.type =  FG_NODE_TYPE_HIGHPASS;
                    node->freq = 261.63;
                    node->node.run = highpass_run;
                    node->node.enabled = 1;
                    g_hash_table_insert(fg->nodes, node->node.base.uuid, node);
                    //printf("Created node type %d with uuid = %s\n", node->node.base.type, node_uuid); 
                }
                break;
            case FG_NODE_TYPE_BANDPASS:{
                    struct fgraph_bandpass* node = malloc(sizeof(struct fgraph_bandpass));
                    memset(node, 0, sizeof(struct fgraph_lowpass));
                    strncpy(node->node.base.uuid, node_uuid, sizeof(node->node.base.uuid)-1);
                    node->node.base.type = FG_NODE_TYPE_BANDPASS;
                    node->freq_high = 261.63;
                    node->freq_low = 261.63;
                    node->node.run = bandpass_run;
                    node->node.enabled = 1;
                    g_hash_table_insert(fg->nodes, node->node.base.uuid, node);
                    //printf("Created node type %d with uuid = %s\n", node->node.base.type, node_uuid); 
                }
                break;
            case FG_NODE_TYPE_MIXER: 
            case FG_NODE_TYPE_SPLITTER:
            case FG_NODE_TYPE_OUTPUT:
            case FG_NODE_TYPE_INPUT: {
                    struct fgraph_node* node = malloc(sizeof(struct fgraph_node));
                    memset(node, 0, sizeof(struct fgraph_node));
                    strncpy(node->base.uuid, node_uuid, sizeof(node->base.uuid)-1);
                    node->base.type = node_type;
                    node->enabled = 1;

                    switch(node_type) {
                        // functionally the input is the same as splitter only one output
                        case FG_NODE_TYPE_INPUT:
                        case FG_NODE_TYPE_SPLITTER:
                            node->run = splitter_run;
                            break;

                        // likewise the output is the same as a mixer with one input 
                        case FG_NODE_TYPE_OUTPUT:
                        case FG_NODE_TYPE_MIXER:
                            node->run = mixer_run;
                            break;        
                    }

                    g_hash_table_insert(fg->nodes, node->base.uuid, node);
                    //printf("Created node type %d with uuid = %s\n", node_type, node_uuid); 
                }
                break;
            case FG_NODE_TYPE_GAIN_BALANCE: {
                    struct fgraph_gain_balance* gb = malloc(sizeof(struct fgraph_gain_balance));
                    struct fgraph_node* node = &gb->node;
                    memset(node, 0, sizeof(struct fgraph_node));
                    strncpy(node->base.uuid, node_uuid, sizeof(node->base.uuid)-1);
                    node->base.type = node_type;
                    node->enabled = 1;
                    node->run = gainbalance_run;

                    gb->balance = 1.0; // left -1.0 right 1.0
                    gb->gain = 1.0;  
                    
                    g_hash_table_insert(fg->nodes, node->base.uuid, gb);
                    //printf("Created node type %d with uuid = %s\n", node_type, node_uuid); 
                }
                break;
            case FG_NODE_TYPE_EFFECT: {
                    struct fgraph_effect* e = malloc(sizeof(struct fgraph_effect));
                    struct fgraph_node* node = &e->node;
                    memset(node, 0, sizeof(struct fgraph_node));
                    strncpy(node->base.uuid, node_uuid, sizeof(node->base.uuid)-1);
                    node->base.type = node_type;
                    node->enabled = 0; // not ready until effect initialization is called.
                    node->run = fg_effect_run;
                    e->filter = NULL;
                    g_hash_table_insert(fg->nodes, node->base.uuid, e);
                }
                break;
            
            default:
                break;
        }


    } else {
        char errmsg[1024];

        sprintf(errmsg,"No match for fg_uuid = %s or type mismatch not a graph.\n", fg_uuid);
        gcsynth_raise_exception(errmsg);
        ret = -1;
    }
    

    return ret;
}

int fg_delete_node(char* fg_uuid, char* node_uuid)
{
    struct fgraph* fg = g_hash_table_lookup(fgraph_db, fg_uuid);

    if (fg == NULL) {
        return;
    }

    struct fgraph_node* node = g_hash_table_lookup(fg->nodes, node_uuid);
    if (node == NULL) {
        return;
    }

    //!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    /*
     Warning: The python layer needs to make sure that connections are removed prior to this
     call. 
     */
    
    //g_hash_table_destroy(fg->nodes);
    g_hash_table_remove(fg->nodes, node_uuid);
    free(node);

    return 0;
}

int fg_set_effect_property(char* fg_uuid, char* node_uuid, char* property, float value)
{
    return 0;
}

int fg_set_node_attribute(char* node_uuid, int type, 
    int att_id, int ival, float fval,  char* sval)
{
    int ret = 0;
    struct fgraph_node* node = (struct fgraph_node*)
        lookup_fgraph_object(node_uuid, type);

    if (node != NULL) {
        switch(att_id) {
            // common attribuates for all nodes.
            case AID_ENABLE:
                node->enabled = 1;
                break;
            case AID_DISABLE:
                node->enabled = 0;
                break;
            default:
            // specific attributes for different node types.  
                switch(type) {
                    // specific attributes for band/low/high pass filters
                    case  FG_NODE_TYPE_LOWPASS:
                    case  FG_NODE_TYPE_HIGHPASS:
                    case FG_NODE_TYPE_BANDPASS:
                        fg_set_band_attribute(node, att_id, ival, fval, sval);
                        break;
                    default:
                        fprintf(stderr,
                            "fg_set_node_attribute unsupported attribute %d in node type %d\n",
                               att_id, type);
                        ret = -1;
                        break;
                }
        }

    } else {
        ret = -1;
        gcsynth_raise_exception("fg_set_node_attribute no match for uuid or type\n");
    }

    return 0;
}

/**
 * create a new connection between two nodes.
 */
int fg_connect_nodes(char* fg_uuid, char* conn_uuid, 
    char* input_uuid, int input_port, char* output_uuid, int output_port)
{
    int ret = 0;
    struct fgraph* fg = (struct fgraph*) lookup_fgraph_object(fg_uuid, FG_GRAPH);

    if (fg != NULL) {
        struct fgraph_connection* conn = malloc(sizeof(struct fgraph_connection));
        memset(conn, 0, sizeof(struct fgraph_connection));
        conn->base.type = FG_CONNECTION;
        strncpy(conn->base.uuid, conn_uuid, sizeof(conn->base.uuid)-1);

        strncpy(conn->uuid_in, input_uuid, sizeof(conn->uuid_in)-1);
        conn->port_in = input_port;
        strncpy(conn->uuid_out, output_uuid, sizeof(conn->uuid_out)-1); 
        conn->port_out = output_port;

        conn->in_node = (struct fgraph_node*) fg_lookup_node(fg, input_uuid);
        conn->out_node = (struct fgraph_node*) fg_lookup_node(fg, output_uuid);

        if (conn->in_node == NULL) {
            ret = -1;
            fprintf(stderr,"fg_connect_nodes: no match for input uuid (%s)\n", input_uuid );
            gcsynth_raise_exception("fg_connect_nodes no match for input uuid\n");
        }
        else if (conn->out_node == NULL) {
            ret = -1;
            fprintf(stderr,"fg_connect_nodes: no match for output uuid (%s)\n", output_uuid );
            gcsynth_raise_exception("fg_connect_nodes no match for output uuid\n");
        }
        else {
            conn->in_node->out_ports = g_list_append(conn->in_node->out_ports, conn);
            conn->out_node->in_ports = g_list_append(conn->out_node->in_ports, conn);

            g_hash_table_insert(fg->connections, conn->base.uuid, conn);
        }

    } else {
        ret = -1;
        gcsynth_raise_exception("fg_connect_nodes fg_uuid failed to map to a filter graph\n");
    }

    return ret;
}

/**
 * remove a connection from the filter graph. Updates the ports of the 
 * input and output nodes associated with the connection.
 */
int fg_delete_connection(char* fg_uuid, char* conn_uuid)
{
    int ret = 0;
    struct fgraph* fg = (struct fgraph*) lookup_fgraph_object(fg_uuid, FG_GRAPH);

    if (fg != NULL) {
        struct fgraph_connection* conn = g_hash_table_lookup(fg->connections, conn_uuid);

        if (conn == NULL) {
            ret = -1;
            gcsynth_raise_exception("fg_delete_connection no match for uuid\n");
        } else {
            // remove port connects in connected notes 
            conn->in_node->out_ports = g_list_remove(conn->in_node->out_ports, conn);
            conn->out_node->in_ports = g_list_remove(conn->out_node->in_ports, conn);

            g_hash_table_remove(fg->connections, conn_uuid);
            free(conn);
        }
    } else {
        ret = -1;
        gcsynth_raise_exception("fg_delete_connection fg_uuid failed to map to a filter graph\n");
    }

    return ret;
}



// void fg_init(struct gcsynth_filter_graph* fg)
// {
//     memset(fg, 0, sizeof(struct gcsynth_filter_graph));
// }


// void fg_enable(struct gcsynth_filter_graph* fg, int enabled)
// {
//     fg->enabled = enabled;
// }



// void fg_proc_balance_gain(float balance, float gain, float* left, float* right)
// {
//     int i;
//     float right_mul, left_mul;

//     if ((balance != 0.0) || (gain != 0.0) ) {
//         if (balance >= -1.0 && balance <= 1.0) {
//             right_mul = (1-balance);
//             left_mul = 2.0 - right_mul;
//         }
//         for( i = 0; i < AUDIO_SAMPLES; i++) {
//             left[i] = (left[i] * left_mul) * (1+gain);
//             right[i] = (right[i] * right_mul) * (1+gain);
//         }
//     }
// }

// /**
//  * 1. copy left/right to input buffer 
//  * 2. pre demux processing
//  * 3. cycle through demux filter chains
//  * 4. mix the output of all chains
//  * 5. apply post mux processing
//  */
// void fg_run(struct gcsynth_filter_graph* fg, int channel, float* left, float* right)
// {
//     if (fg->enabled) {
//         fg->out_left = left;
//         fg->out_right = right;

//         if (fg->demuxer.num_chains == 0) {
//             // in this case there is no filter chain. Only the pre demux filters
//             // and balance and gain being used. No need to waste time copying
//             // data to buffers we can do everything in the left/right buffers
//             // provided.
//             pre_demux_proc(fg, left, right);
//         } else {
//             // 1. copy left/right to input buffer
//             memcpy(fg->in_left, left, sizeof(fg->in_left));
//             memcpy(fg->in_right, right, sizeof(fg->in_right));

//             // 2. pre demux effects (such as a noise gate, compressor)
//             pre_demux_proc(fg, fg->in_left, fg->in_right);

//             // 3. apply audio effects to each filter chain 
//             demux_proc(fg, channel);

//             // 4. mux the output from all filter chains.
//             muxer_proc(fg);
//         }

//         // apply balance and gain.
//         fg_proc_balance_gain(fg->balance, fg->gain, left, right);
//     }
// }

// int fg_create_filter(
//     struct gcsynth_filter_graph* fg,
//     int chain_idx, // -1 means this filter is applied pre-demux
//     const char* pathname, 
//     char* label 
// )
// {
//     int error = 0;
//     struct gcsynth_filter* f = gcsynth_filter_new_ladspa(pathname, label);

//     if (f == NULL) {
//         error = -1;
//     } else {
//         if (chain_idx == -1) {
//             fg->pre_demux_effects = g_list_append(fg->pre_demux_effects, f);
//             fg->filter_enabled_count++;
//         } else if ((chain_idx >= 0) && (chain_idx < MAX_FILTER_CHAINS)) {
//             struct fg_effect_chain* chain = &fg->demuxer.effect_chains[chain_idx];
//             chain->effects = g_list_append(chain->effects, f);
//             fg->filter_enabled_count++;
//         }  else {
//             error = -1;
//             gcsynth_filter_destroy(f);
//             gcsynth_raise_exception("filter chain index out of range!");
//         }
//     }

//     return error;
// }


// // primitive that searches for a filter by label in a filter chain
// // or pre demux filter. 
// struct fg_find_filter_result fg_find_filter(
//     struct gcsynth_filter_graph* fg,
//     int chain_idx, // -1 means this filter is applied pre-demux
//     char* label
// ){
//     struct fg_find_filter_result result; 
    
//     memset(&result, 0, sizeof(struct fg_find_filter_result));
//     if (chain_idx == -1) {
//         GList* iter;
//         for(iter = g_list_first(fg->pre_demux_effects);
//             iter != NULL;
//             iter = iter->next
//         ) {
//             struct gcsynth_filter* f = (struct gcsynth_filter*) iter->data; 
//             if (strcmp(f->desc->Label, label) == 0) {
//                 result.list = &fg->pre_demux_effects;
//                 result.iter = iter;
//                 result.filter = f;
//                 result.found = 1;
//                 break;
//             }
//         }
//     } else if ((chain_idx >= 0) && (chain_idx < MAX_FILTER_CHAINS)){
//         // this is the deletion of a specific audio filter within a chain.
//         struct fg_effect_chain* chain = &fg->demuxer.effect_chains[chain_idx];
//         GList* iter;
//         for(iter = g_list_first(chain->effects);
//             iter != NULL;
//             iter = iter->next
//         ) {
//             struct gcsynth_filter* f = (struct gcsynth_filter*) iter->data; 
//             if (strcmp(f->desc->Label, label) == 0) {
//                 result.list = &chain->effects;
//                 result.iter = iter;
//                 result.filter = f;
//                 result.found = 1;
//             }
//         }
//     } 
    
//     return result;
// }



// int fg_remove_filter(
//     struct gcsynth_filter_graph* fg,
//     int chain_idx, // -1 means this filter is applied pre-demux
//     char* label
// ) {
//     struct fg_find_filter_result result =  
//         fg_find_filter(fg,chain_idx,label);

//     if (result.found == 1) {
//         GList* list = *result.list;
        
//         list = g_list_delete_link(list, result.iter);
//         fg->filter_enabled_count--;
//     }
//     return result.found;
// }