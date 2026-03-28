
#include "fgraph.h"
#include "gcsynth_sf.h"

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
#include "freqdomain.h"


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
    struct fgraph_node* n;
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
        } else if (n->base.type != FG_NODE_TYPE_EFFECT) {
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
                    // increment count of precalculated buffers associated with frequences.
                    // to avoid fft processing.  
                    midi_filter_increment(); 
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
                    midi_filter_increment(); 
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
                    midi_filter_increment(); 
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
                            fg->input_node = node;
                            break;
                        case FG_NODE_TYPE_SPLITTER:
                            node->run = splitter_run;
                            break;

                        // likewise the output is the same as a mixer with one input 
                        case FG_NODE_TYPE_OUTPUT:
                            fg->output_node = node;
                            break;
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
        return -1;
    }

    struct fgraph_node* node = g_hash_table_lookup(fg->nodes, node_uuid);
    if (node == NULL) {
        return -1;
    }

    switch(node->base.type) {
        case FG_NODE_TYPE_LOWPASS:
        case FG_NODE_TYPE_HIGHPASS:
        case FG_NODE_TYPE_BANDPASS:
            if (!node->using_fallback_method_for_freqdomain) {
                midi_filter_decrement(); // reduce counter
            }
            break;
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
    char errmsg[256];
    int ret = 0;
    struct fgraph* fg = (struct fgraph*) lookup_fgraph_object(fg_uuid, FG_GRAPH);
    
    errmsg[0] = '\0';

    if (fg == NULL) {
        sprintf(errmsg,"fg_set_effect_property no match for graph %s\n", fg_uuid);
    } else {
        struct fgraph_node* node = (struct fgraph_node*)
            fg_lookup_node(fg, node_uuid);

        if (node == NULL) {
            sprintf(errmsg,"fg_set_effect_property no match for effect node uuid %s\n",
                node_uuid);
        } else if (node->base.type != FG_NODE_TYPE_EFFECT) {
            sprintf(errmsg,"fg_set_effect_property node type mismatch node uuid %s expected effect type got %d\n",
                node_uuid, node->base.type);
        } else {
            struct fgraph_effect* e = (struct fgraph_effect *) node;

            if (e->filter == NULL) {
                sprintf(errmsg,"fg_set_effect_property null filter\n");
            } else {
                ret = gcsynth_filter_setbyname(e->filter, property, value);
            }
        }
    }

    if (errmsg[0] != '\0') {
        gcsynth_raise_exception(errmsg);
        ret = -1;
    }

    return ret;
}

int fg_set_node_attribute(char* graph_uuid, char* node_uuid, int type, 
    int att_id, int ival, float fval,  char* sval)
{
    char errmsg[256];
    int ret = 0;
    struct fgraph* fg = (struct fgraph*) lookup_fgraph_object(graph_uuid, FG_GRAPH);
    
    errmsg[0] = '\0';

    if (fg == NULL) {
        sprintf(errmsg,"fg_set_node_attribute no match for graph %s\n", graph_uuid);
    } else {
        struct fgraph_node* node = (struct fgraph_node*)
            fg_lookup_node(fg, node_uuid);

        if (node != NULL) {
            switch(att_id) {
                // common attribuates for all nodes.
                case AID_ENABLE:
                    node->enabled = 1;
                    if (type == FG_NODE_TYPE_EFFECT) {
                        struct fgraph_effect* e = (struct fgraph_effect*) node;
                        gcsynth_filter_enable(e->filter);
                    }
                    break;
                case AID_DISABLE:
                    node->enabled = 0;
                    if (type == FG_NODE_TYPE_EFFECT) {
                        struct fgraph_effect* e = (struct fgraph_effect*) node;
                        gcsynth_filter_disable(e->filter);
                    }
                    break;
                default:
                    // specific attributes for different node types.  
                    switch(type) {
                        // specific attributes for band/low/high pass filters
                        case FG_NODE_TYPE_LOWPASS:
                        case FG_NODE_TYPE_HIGHPASS:
                        case FG_NODE_TYPE_BANDPASS:
                            fg_set_band_attribute(node, att_id, ival, fval, sval);
                            break;
                        default:
                            sprintf(errmsg,
                                "fg_set_node_attribute unsupported attribute %d in node type %d\n",
                                att_id, type);
                            break;
                    }
            }
        } else {
            sprintf(errmsg,"fg_set_node_attribute no match for node uuid %s\n",
                node_uuid);
        }
    }

    if (errmsg[0] != '\0') {
        gcsynth_raise_exception(errmsg);
        ret = -1;
    }

    return ret;
}

/**
 * create a new connection between two nodes.
 */
int fg_connect_nodes(char* fg_uuid, char* conn_uuid, 
    char* input_uuid, int output_port, char* output_uuid, int input_port)
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

        conn->out_node = (struct fgraph_node*) fg_lookup_node(fg, input_uuid);
        conn->in_node = (struct fgraph_node*) fg_lookup_node(fg, output_uuid);

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
            /*
            
                left node                                 right node 
                       out port list <- connection -> in port list
             
             */
            struct fgraph_node *left = conn->in_node;
            struct fgraph_node *right = conn->out_node;

            int left_out_port_idx = g_list_length(left->out_ports);
            int right_in_port_idx = g_list_length(right->in_ports);

            conn->port_out = left_out_port_idx;
            conn->port_in = right_in_port_idx;
            
            left->out_ports = g_list_append(left->out_ports, conn);
            right->in_ports = g_list_append(right->in_ports, conn);

// fflush(stdout);
// printf("CONNECTING %s(uuid=%s).out[%d] ---> %s(uuid=%s).in[%d]\n", node_type_to_str(left), 
//     left->base.uuid, conn->port_out,
//     node_type_to_str(right), right->base.uuid, 
//     conn->port_in);
// fflush(stdout);

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

struct fg_channel_data
{
    struct fgraph* fg;
    int channel;
};

static void do_assign_fg_to_channel(void *user_data)
{
    struct fg_channel_data* arg = (struct fg_channel_data*) user_data;

    gcsynth_channel_assign_filter_graph(arg->channel, arg->fg);
    free(user_data);
}

int assign_fg_to_channel(char* fg_uuid, int channel)
{
    struct fgraph* fg = (struct fgraph*) lookup_fgraph_object(fg_uuid, FG_GRAPH);
    struct fg_channel_data* user_data;
    char errmsg[256];
    int ret = 0;

    errmsg[0] = '\0';

    if (fg == NULL) {
        sprintf(errmsg,"assign_fg_to_channel no match for graph %s", fg_uuid);
    } else {
        user_data = 
            (struct fg_channel_data* ) malloc(sizeof(struct fg_channel_data));
        user_data->channel = channel;
        user_data->fg = fg;
        ret = gcsynth_sf_extern_func(channel, do_assign_fg_to_channel, user_data);
    }

    if (errmsg[0] != '\0') {
        gcsynth_raise_exception(errmsg);
        ret = -1;
    }

    return ret;
}


int unassign_fg_to_channel(int channel)
{
    struct fg_channel_data* user_data = 
        (struct fg_channel_data* ) malloc(sizeof(struct fg_channel_data));
    user_data->channel = channel;
    user_data->fg = NULL;
    return gcsynth_sf_extern_func(channel, do_assign_fg_to_channel, user_data);
}
