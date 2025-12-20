#include "ringbuffer.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

ring_buffer* ring_buffer_create() 
{
    ring_buffer* rb = calloc(1, sizeof(ring_buffer));
    if (rb) {
        if (pthread_mutex_init(&rb->lock, NULL) != 0) {
            perror("Mutex initialization failed");
            free(rb);
            rb = NULL;
        } 
    }
    return rb;
}

static int rb_is_full(ring_buffer* rb) 
{
    return rb->count == RING_BUFFER_DEPTH;
}

static int rb_is_empty(ring_buffer* rb) 
{
    return rb->count == 0;
}


int ring_buffer_push(ring_buffer* rb, float* left, float* right)
{
    int error = 0;
    int n;
    pthread_mutex_lock(&rb->lock);

    if (rb_is_full(rb)) {
        
        // If full, the tail must advance to discard the oldest element
        rb->tail = (rb->tail + 1) % RING_BUFFER_DEPTH;
        rb->count--; // Decrement count to account for the overwrite logic below
        error = -1;
    }

    n = AUDIO_SAMPLES * sizeof(float);
    memcpy(rb->left[rb->head], left, n);
    memcpy(rb->right[rb->head], right, n);
    rb->head = (rb->head + 1) % RING_BUFFER_DEPTH;
    rb->count++;

    pthread_mutex_unlock(&rb->lock);
    return error;
}

int ring_buffer_pop(ring_buffer* rb, float* left, float* right)
{
    int error = 0;
    int n;
    pthread_mutex_lock(&rb->lock);

    if (rb_is_empty(rb)) {
        error = -1;
    } else {
        n = AUDIO_SAMPLES * sizeof(float);
        memcpy(left, rb->left[rb->tail], n);
        memcpy(right, rb->right[rb->tail], n);
        rb->tail = (rb->tail + 1) % RING_BUFFER_DEPTH;
        rb->count--;   
    }

    pthread_mutex_unlock(&rb->lock);
    return error;
}

int ring_buffer_count(ring_buffer* rb)
{
    int count;

    pthread_mutex_lock(&rb->lock);
    count = rb->count; 
    pthread_mutex_unlock(&rb->lock);
    return count;
}