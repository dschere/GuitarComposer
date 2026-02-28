
#include "fgraph.h"


#include <glib.h>
#include <stdio.h>
#include <malloc.h>
#include <string.h>

#include "bandpass.h"


static GHashTable* fgraph_db = NULL;


int fg_init()
{
    if ((fgraph_db = g_hash_table_new(g_str_hash, g_str_equal)) == NULL) {
        fprintf(stderr,"Unable to create fgraph hash table!\n");
        return -1;
    }
    return 0;
}

struct fgraph_base* lookup_fgraph_object(char* uuid, int expected_type)
{
    struct fgraph_base* item = NULL;

    if (fgraph_db != NULL) {
        item = g_hash_table_lookup(fgraph_db, uuid);
        if (item != NULL) {
            if ((expected_type != -1) && (item->type != expected_type)) {
                item = NULL;
                gcsynth_raise_exception("lookup_fgraph_object wrong type!");
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


int fg_create_node(char* fg_uuid, char* node_uuid, int node_type)
{
    struct fgraph* fg = (struct fgraph*) lookup_fgraph_object(fg_uuid, FG_GRAPH);
    int ret = 0;

    if (fg != NULL) {
        switch(node_type) {
            // create a low pass filter
            case FG_LOW_PASS: {
                    struct fgraph_lowpass* node = malloc(sizeof(struct fgraph_lowpass));
                    memset(node, 0, sizeof(struct fgraph_lowpass));
                    strncpy(node->node.base.uuid, node_uuid, sizeof(node->node.base.uuid)-1);
                    node->node.base.type = FG_LOW_PASS;
                    node->freq = 261.63;
                    node->node.run = lowpass_run;
                    node->node.enabled = 1;
                    g_hash_table_insert(fg->nodes, node->node.base.uuid, node);
                }
                break;
            // create a high pass filter
            case FG_HIGH_PASS:{
                    struct fgraph_highpass* node = malloc(sizeof(struct fgraph_highpass));
                    memset(node, 0, sizeof(struct fgraph_lowpass));
                    strncpy(node->node.base.uuid, node_uuid, sizeof(node->node.base.uuid)-1);
                    node->node.base.type = FG_HIGH_PASS;
                    node->freq = 261.63;
                    node->node.run = highpass_run;
                    node->node.enabled = 1;
                    g_hash_table_insert(fg->nodes, node->node.base.uuid, node);
                }
                break;
            case FG_BAND_PASS:{
                    struct fgraph_bandpass* node = malloc(sizeof(struct fgraph_bandpass));
                    memset(node, 0, sizeof(struct fgraph_lowpass));
                    strncpy(node->node.base.uuid, node_uuid, sizeof(node->node.base.uuid)-1);
                    node->node.base.type = FG_BAND_PASS;
                    node->freq_high = 261.63;
                    node->freq_low = 261.63;
                    node->node.run = bandpass_run;
                    node->node.enabled = 1;
                    g_hash_table_insert(fg->nodes, node->node.base.uuid, node);
                }
                break;
            case FG_EFFECT:
            case FG_INPUT:
            case FG_OUTPUT:
            case FG_MIXER:
            case FG_SPLITTER:
            case FG_GAIN_BALANCE:
        }


    } else {
        fprintf(stderr,"No match for fg_uuid = %s or type mismatch not a graph.\n", fg_uuid);
        ret = -1;
    }
    

    return ret;
}

int fg_delete_node(char* fg_uuid, char* node_uuid)
{
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
                    case FG_LOW_PASS:
                    case FG_HIGH_PASS:
                    case FG_BAND_PASS:
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

        conn->in_node = (struct fgraph_node*) lookup_fgraph_object(input_uuid, -1);
        conn->out_node = (struct fgraph_node*) lookup_fgraph_object(output_uuid, -1);

        if (conn->in_node == NULL) {
            ret = -1;
            gcsynth_raise_exception("fg_connect_nodes no match for input uuid\n");
        }
        else if (conn->out_node == NULL) {
            ret = -1;
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