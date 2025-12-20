#ifndef __RINGBUFFER_H
#define __RINGBUFFER_H

#include <pthread.h>

#include "gcsynth.h"

typedef struct {
    pthread_mutex_t lock;

    float left[RING_BUFFER_DEPTH][AUDIO_SAMPLES];
    float right[RING_BUFFER_DEPTH][AUDIO_SAMPLES];

    int head; // index to write the next element
    int tail; // index to read the next element
    int count; // current number of elements in the buffer
} ring_buffer;

ring_buffer* ring_buffer_create();

// length of right/left is assumed to be AUDIO_SAMPLES in length.
int ring_buffer_push(ring_buffer* rb, float* left, float* right);
int ring_buffer_pop(ring_buffer* rb, float* left, float* right);
int ring_buffer_count(ring_buffer* rb);

#endif