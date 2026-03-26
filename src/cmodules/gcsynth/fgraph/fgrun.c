#include "fgraph.h"

#include <malloc.h>
#include <stdio.h>


static void fg_iterate(int channel, struct fgraph_node* n, 
    struct fgraph_connection* input_connection, float* left, float* right);
static void input_op(int channel, struct fgraph_node* n, 
    struct fgraph_connection* input_connection, float* left, float* right);
static void splitter_op(int channel, struct fgraph_node* n, 
    struct fgraph_connection* input_connection, float* left, float* right);
static void mixer_op(int channel, struct fgraph_node* n, 
    struct fgraph_connection* input_connection, float* left, float* right);
static void single_input_output_node_op(int channel, struct fgraph_node* n, 
    struct fgraph_connection* input_connection, float* left, float* right);

/**
 * Note:
 * For nodes in the graph with a single input and output the buffers in the 
 * connection are not used. the run function overwrites the left/right array
 * content. The caveat is that if this function detects that node connected to 
 * output port is the OUTPUT node then it will update the left/right buffer on
 * the connection. 
 * 
 */
static void single_input_output_node_op(int channel, struct fgraph_node* n, 
    struct fgraph_connection* input_connection, float* left, float* right)
{

    char errmsg[256];
    GList* p;
    struct fgraph_connection* c;

    errmsg[0] = '\0';
    if (n == NULL) {
        sprintf(errmsg,"single_input_output_node_op 'n' is null\n");
    } else if ((p = g_list_first(n->out_ports)) == NULL) {
        sprintf(errmsg,"single_input_output_node_op type=%d null output ports!\n", n->base.type);
    }
    else if ((c = (struct fgraph_connection*) p->data) == NULL) {
        sprintf(errmsg,"single_input_output_node_op type=%d null output port!\n", n->base.type);
    } else {
        // outputs directly to left/right
        struct fgraph_node* next = c->out_node;

        // for nodes with one input and output the left/right
        // buffers are populated in place.
        n->channel = channel;
        int run_result = n->run(n, left, right); 
        ///////////////////////////////

        if (run_result != 0) {
            sprintf(errmsg,"single_input_output_node_op type=%d run failed!\n",
                n->base.type);
        } else {
            // if the next node is the output node then copy to 
            // connection buffer of the input port just like the mixer.
            // so the logic is the same.
            if (next->base.type == FG_NODE_TYPE_OUTPUT) {
                GList* f = g_list_first(next->in_ports);
                int i;
                if (f == NULL) {
                    sprintf(errmsg,"output node has no ports!\n");
                }
                struct fgraph_connection* next_c = (struct fgraph_connection*) f->data;
                for(i = 0; i < AUDIO_SAMPLES; i++) {
                    next_c->left[i] = left[i]; 
                    next_c->right[i] = right[i];
                }
            }        

            // follow connection to next node
            fg_iterate(channel, next, c, left, right);
        }
    }

    if (errmsg[0] != '\0') {
        gcsynth_raise_exception(errmsg);
    }
}

static const char* node_type_to_string(int type) {
    switch(type) {
        case FG_NODE_TYPE_LOWPASS: return "LOWPASS";
        case FG_NODE_TYPE_HIGHPASS: return "HIGHPASS";
        case FG_NODE_TYPE_BANDPASS: return "BANDPASS";
        case FG_NODE_TYPE_EFFECT: return "EFFECT";
        case FG_NODE_TYPE_INPUT: return "INPUT";
        case FG_NODE_TYPE_OUTPUT: return "OUTPUT";
        case FG_NODE_TYPE_MIXER: return "MIXER";
        case FG_NODE_TYPE_SPLITTER: return "SPLITTER";
        case FG_NODE_TYPE_GAIN_BALANCE: return "GAIN_BALANCE";
        default: return "UNKNOWN";
    }
}

char* node_type_to_str(struct fgraph_node* n) {
    switch(n->base.type) {
        case FG_NODE_TYPE_BANDPASS: return "BANDPASS";
        case FG_NODE_TYPE_EFFECT: return "EFFECT";
        case FG_NODE_TYPE_HIGHPASS: return "HIGHPASS";
        case FG_NODE_TYPE_INPUT: return "INPUT";
        case FG_NODE_TYPE_LOWPASS: return "LOWPASS";
        case FG_NODE_TYPE_MIXER: return "MIXER";
        case FG_NODE_TYPE_OUTPUT: return "OUTPUT";
        case FG_NODE_TYPE_SPLITTER: return "SPLITTER";
        default: return "UNKNOWN";
    }
}

static void print_node(gpointer key, gpointer value, gpointer user_data) {
    struct fgraph_node* node = (struct fgraph_node*)value;
    unsigned i;
    printf("  Node [%s] UUID: %s, Enabled: %d\n", 
        node_type_to_string(node->base.type), node->base.uuid, node->enabled);
    
    printf("    In Ports: %u, Out Ports: %u\n", 
        g_list_length(node->in_ports), g_list_length(node->out_ports));

    printf("    Input port connections\n");
    for(i = 0; i < g_list_length(node->in_ports); i++) {
        struct fgraph_connection* c = (struct fgraph_connection*) g_list_nth_data(node->in_ports, i);
        if (c) {
            printf("    in_port[%d] from Node %s, type %s\n", i, c->in_node->base.uuid, node_type_to_str(c->in_node));
        }
    }

    printf("    Output port connections\n");
    for(i = 0; i < g_list_length(node->out_ports); i++) {
        struct fgraph_connection* c = (struct fgraph_connection*) g_list_nth_data(node->out_ports, i);
        if (c) {
            printf("    out_port[%d] from Node %s, type %s\n", i, c->in_node->base.uuid, node_type_to_str(c->in_node));
        }

    }

}

// static void print_connection(gpointer key, gpointer value, gpointer user_data) {
//     struct fgraph_connection* conn = (struct fgraph_connection*)value;
//     printf("  Connection UUID: %s\n", conn->base.uuid);
//     printf("    From Node: %s (Port %d) -> To Node: %s (Port %d)\n", 
//            conn->uuid_in, conn->port_in, conn->uuid_out, conn->port_out);
// }

void fg_dump(struct fgraph* fg) {
    if (!fg) {
        printf("fg_dump: fgraph is NULL\n");
        return;
    }
    printf("=== Filter Graph Dump ===\n");
    printf("UUID: %s\n", fg->base.uuid);
    printf("Enabled: %d\n", fg->enabled);
    printf("Input Node UUID: %s\n", fg->input_node ? fg->input_node->base.uuid : "NONE");
    printf("Output Node UUID: %s\n", fg->output_node ? fg->output_node->base.uuid : "NONE");
    
    printf("Nodes:\n");
    if (fg->nodes) {
        g_hash_table_foreach(fg->nodes, print_node, NULL);
    } else {
        printf("  None\n");
    }

    // printf("Connections:\n");
    // if (fg->connections) {
    //     g_hash_table_foreach(fg->connections, print_connection, NULL);
    // } else {
    //     printf("  None\n");
    // }
    printf("=========================\n");
}

static void input_op(int channel, struct fgraph_node* n, struct fgraph_connection* input_connection,
    float* left, float* right)
{
    if (g_list_length(n->out_ports) > 0) {
        struct fgraph_connection* c = (struct fgraph_connection*) g_list_first(n->out_ports)->data;
        // follow the connection from the output of the INPUT node.
        fg_iterate(channel, c->out_node, c, left, right);
    }
}

static void splitter_op(int channel, struct fgraph_node* n, 
    struct fgraph_connection* input_connection, float* left, float* right)
{
    GList* iter;

    n->run(n, left, right);
    for(iter = g_list_first(n->out_ports);
        iter != NULL;
        iter = iter->next
    ) {
        struct fgraph_connection* conn = 
            (struct fgraph_connection*) iter->data;
        fg_iterate(channel, conn->out_node, conn, conn->left, conn->right );
    }
}

static struct fgraph_connection* get_nth_connection(GList* l, int idx)
{
    GList* item;
    struct fgraph_connection* result = NULL;
    char errmsg[256];

    errmsg[0] = '\0';
    
    if (l == NULL) {
        sprintf(errmsg, "get_nth_connection null list!\n");
    }
    else if ((item = g_list_nth(l, idx)) == NULL) {
        sprintf(errmsg, "get_nth_connection no item at %d\n", idx);
    }
    else {
        result = (struct fgraph_connection* ) item->data;
    } 

    if (errmsg[0] != '\0') {
        gcsynth_raise_exception(errmsg);
    }
    
    return result;
} 

static struct fgraph_connection* get_first_connection(GList* l)
{
    GList* item;
    struct fgraph_connection* result = NULL;
    char errmsg[256];

    errmsg[0] = '\0';
    
    if (l == NULL) {
        sprintf(errmsg, "get_first_connection null list!\n");
    }
    else if ((item = g_list_first(l)) == NULL) {
        sprintf(errmsg, "get_first_connection failed\n");
    }
    else {
        result = (struct fgraph_connection* ) item->data;
    } 

    if (errmsg[0] != '\0') {
        gcsynth_raise_exception(errmsg);
    }
    
    return result;
}



static void mixer_op(int channel, struct fgraph_node* n, 
    struct fgraph_connection* input_connection, float* left, float* right)
{
    int num_ports = g_list_length(n->in_ports);
    int idx = n->in_port_update_count % num_ports;
    int i;
    struct fgraph_connection* c = get_nth_connection(n->in_ports, idx);
    struct fgraph_connection* out_conn = get_first_connection(n->out_ports);

    if ((c == NULL) || (out_conn == NULL)) {
        return;
    }

    for(i = 0; i < AUDIO_SAMPLES; i++) {
        c->left[i] = left[i];
        c->right[i] = right[i];        
    }

    n->in_port_update_count++;
    if ((n->in_port_update_count % num_ports) == 0) {

        // mix all inputs to the output connection.
        n->channel = channel;
        n->run(n, left, right);

        fg_iterate(channel, out_conn->out_node, 
            out_conn, out_conn->left, out_conn->right); 
    }
    // until the last mixer input is set this is as far as processing goes for the rest.
}



/**
 * Filter graph iterator.
 *    Recursively walk from the output port of the INPUT node till we reach the input port
 *    of the OUTPUT node. 
 * 
 */
static void fg_iterate(int channel, struct fgraph_node* n, struct fgraph_connection* input_connection,
    float* left, float* right)
{    
// printf("fg_iterate channel=%d %s(uuid=%s,type=%d) input_connection %s(uuid=%s)\n",
//     channel, node_type_to_str(n), n->base.uuid, n->base.type,
//         (input_connection) ? node_type_to_str(input_connection->out_node) : "null",
//         (input_connection) ? input_connection->out_node->base.uuid: "null"
//     );
// fflush(stdout);

    switch(n->base.type) {
        case FG_NODE_TYPE_MIXER:
            mixer_op(channel, n, input_connection, left, right);
            break;
        case FG_NODE_TYPE_SPLITTER:
            splitter_op(channel, n, input_connection, left, right);
            break;
        case FG_NODE_TYPE_INPUT:
            input_op(channel, n, input_connection, left, right);
            break;
        case FG_NODE_TYPE_OUTPUT:
            // the data for the updated left, right audio is in the 
            // output nodes's input port buffer. We are done!
            break;
        default:
            single_input_output_node_op(channel, n, input_connection, left, right);
            break;
    }
}


void fg_run(struct fgraph* fg, int channel, float* left, float* right)
{
    char errmsg[256];
    int i;
    GList* f;
    struct fgraph_connection* c;

    if (fg->enabled == 0) {
        return;
    }

    errmsg[0] = '\0';

    if (fg->input_node == NULL) {
        sprintf(errmsg,"fgraph for channel %d, no input node!\n", channel);
    } else if (fg->output_node == NULL) {
        sprintf(errmsg,"fgraph for channel %d, no output node!\n", channel);
    } else if ((f = g_list_first(fg->output_node->in_ports)) == NULL) {
        sprintf(errmsg,"fgraph output for channel %d has no connection for output\n", channel);
    } else {
        // start from the input node and walk all paths to reach the output    
        fg_iterate(channel, fg->input_node, NULL, left, right);

        // copy the audio stored in the connection to the output node of the
        // filter graph.
    
        c = (struct fgraph_connection*) f->data;
        for(i = 0; i < AUDIO_SAMPLES; i++) {
            left[i] = c->left[i];
            right[i] = c->right[i];
        }
    }

    if (errmsg[0] != '\0') {
        fg_dump(fg);
        gcsynth_raise_exception(errmsg);
    }
}
