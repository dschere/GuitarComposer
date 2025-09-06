#include <SDL2/SDL.h>
#include <pthread.h>
#include <unistd.h>
#include <glib.h>

#include "gcsynth.h"
#include "gcsynth_channel.h"
#include "gcsynth_acapture.h"

struct audio_capture_frame {
    float left[AUDIO_SAMPLES];
    float right[AUDIO_SAMPLES];
};

struct capture_thread {
    SDL_AudioSpec spec;
    SDL_AudioDeviceID dev;
    GAsyncQueue *live_data_queue;

    pthread_attr_t attr;
    pthread_t thread; 
    
    pthread_mutex_t running_mutex;
    int running; 
    int initialized;
};

struct audio_thread {
    SDL_AudioSpec spec;
    SDL_AudioDeviceID dev;

    pthread_attr_t attr;
    pthread_t thread; 
    
    pthread_mutex_t running_mutex;
    int running;
    int initialized; 
};


static struct capture_thread CaptureThread;
static struct audio_thread   AudioThread;

#define MAX_BUFFERED_FRAMES 32
static struct audio_capture_frame capture_ringbuf[MAX_BUFFERED_FRAMES];
static unsigned int frame_idx = 0;


#define TEST 0

#ifdef TEST
static float ave_power(struct audio_capture_frame* frame, int samples) {
    int i;
    float p = 0.0;
#define fabs(x) (x < 0) ? -x: x

    for(i = 0; i < samples; i++) {
        p += fabs(frame->left[i]);
        p += fabs(frame->right[i]);
    }
    return p / samples;
}
#endif


// -- capture thread 


static void capture_callback(void *userdata, Uint8 *stream, int len) {
    struct capture_thread* t = (struct capture_thread*) userdata;
    int samples = (len / (2 * sizeof(float))); //2 output channels
    float *buffer = (float*) stream;
    int i;
    struct audio_capture_frame* frame = 
        &capture_ringbuf[(frame_idx++) % MAX_BUFFERED_FRAMES];

    for(i = 0; i < samples; i++) {
        frame->left[i] = buffer[i*2];
        frame->right[i] = buffer[(i*2) + 1];
    }

    if (g_async_queue_length(CaptureThread.live_data_queue) < MAX_BUFFERED_FRAMES) {
        g_async_queue_push(CaptureThread.live_data_queue, frame);

#ifdef TEST
// for testing
printf("capture callback: ave_power -> %f\n", ave_power(frame,samples));
#endif

    }// otherwise we have to drop the frame.
}

static void *capture_thread(void *arg) {
    // service capture device 
    SDL_PauseAudioDevice(CaptureThread.dev, 0);  // Start playback
    int running = 1;

    while (running) {
        SDL_Delay(220);
        pthread_mutex_lock(&CaptureThread.running_mutex);
        running = CaptureThread.running;
        pthread_mutex_unlock(&CaptureThread.running_mutex);
    }

    SDL_CloseAudioDevice(CaptureThread.dev);
    return NULL;
}


static int capture_thread_init(char* device_name) {
    int result = 0;

    CaptureThread.spec.freq = SAMPLE_RATE;
    CaptureThread.spec.format = AUDIO_F32SYS;
    CaptureThread.spec.channels = 2;
    CaptureThread.spec.samples = AUDIO_SAMPLES;
    CaptureThread.spec.callback = capture_callback;
    CaptureThread.spec.userdata = &CaptureThread;
    CaptureThread.live_data_queue = g_async_queue_new();

    CaptureThread.dev = SDL_OpenAudioDevice(
        device_name,
        1,
        &CaptureThread.spec,
        NULL,
        0
    );
    if (CaptureThread.dev == 0) {
        fprintf(stderr, "SDL_OpenAudioDevice failed: %s\n", SDL_GetError());
        result = -1;
    }

    return result;
}

static int capture_thread_start()
{
    pthread_attr_init(&CaptureThread.attr);
    // launch capture thread to route audio checks to the audio thread.
    pthread_attr_setdetachstate(
            &CaptureThread.attr,PTHREAD_CREATE_DETACHED);

    // launch audio thread 
    if (pthread_create(
        &CaptureThread.thread, 
        &CaptureThread.attr, 
        capture_thread, 
        &CaptureThread) != 0) 
    {
        return -1;
    }

    CaptureThread.running = 1;
    return 0;
}

static void capture_thread_stop() {
    if (CaptureThread.running) {
        pthread_mutex_lock(&CaptureThread.running_mutex);
        CaptureThread.running = 0;
        pthread_mutex_unlock(&CaptureThread.running_mutex);

        pthread_join(CaptureThread.thread, NULL);
    }
}


// -- audio out thread

static void audio_callback(void *userdata, Uint8 *stream, int len) {
    struct capture_thread* t = (struct capture_thread*) userdata;
    int samples = (len / (2 * sizeof(float))); //2 output channels
    float *buffer = (float*) stream;
    int i;

    memset(stream, 0, len);

    struct audio_capture_frame* frame = 
        g_async_queue_timeout_pop(CaptureThread.live_data_queue,0);
    if (frame != NULL) {
        // run through effects if configured
        if (gcsynth_channel_filter_is_enabled(LIVE_CAPTURE_CHANNEL)) {
            synth_filter_router(LIVE_CAPTURE_CHANNEL, frame->left, frame->right, samples);
        }

#ifdef TEST
// for testing
printf("audio callabck ave_power -> %f\n", ave_power(frame,samples));
#endif

        // output interleaved 
        for(i = 0; i < samples; i++) {
            buffer[i * 2]     = frame->left[i];
            buffer[i * 2 + 1] = frame->right[i];
        }
    }
}

static void *audio_thread(void *arg) {
    // service capture device 
    SDL_PauseAudioDevice(AudioThread.dev, 0);  // Start playback
    int running = 1;

    while (running) {
        SDL_Delay(220);
        pthread_mutex_lock(&AudioThread.running_mutex);
        running = AudioThread.running;
        pthread_mutex_unlock(&AudioThread.running_mutex);
    }

    SDL_CloseAudioDevice(AudioThread.dev);
    return NULL;
}



static int audio_thread_init() {
    int result = 0;

    AudioThread.spec.freq = SAMPLE_RATE;
    AudioThread.spec.format = AUDIO_F32SYS;
    AudioThread.spec.channels = 2;
    AudioThread.spec.samples = AUDIO_SAMPLES;
    AudioThread.spec.callback = audio_callback;
    AudioThread.spec.userdata = &CaptureThread;
    
    AudioThread.dev = SDL_OpenAudioDevice(
        NULL,
        0,
        &AudioThread.spec,
        NULL,
        0
    );
    if (AudioThread.dev == 0) {
        fprintf(stderr, "SDL_OpenAudioDevice failed: %s\n", SDL_GetError());
        result = -1;
    }

    return result;
}

static int audio_thread_start()
{

    pthread_attr_init(&AudioThread.attr);
    // launch capture thread to route audio checks to the audio thread.
    pthread_attr_setdetachstate(
            &AudioThread.attr,PTHREAD_CREATE_DETACHED);

    // launch audio thread 
    if (pthread_create(
        &AudioThread.thread, 
        &AudioThread.attr, 
        audio_thread, 
        &CaptureThread) != 0) 
    {
        return -1;
    }

    AudioThread.running = 1;
    return 0;
}

static void audio_thread_stop() {
    if (AudioThread.running) { 
        pthread_mutex_lock(&AudioThread.running_mutex);
        AudioThread.running = 0;
        pthread_mutex_unlock(&AudioThread.running_mutex);

        pthread_join(AudioThread.thread, NULL);
    }
}


// -- external interface

void StopAudioCapture()
{
    audio_thread_stop();
    capture_thread_stop();    
}

int StartAudioCapture(char* device)
{
    int result = -1;
    
    if (
        (audio_thread_init() == 0) &&
        (audio_thread_start() == 0) &&
        (capture_thread_init(device) == 0) &&
        (capture_thread_start() == 0)
    ) {
        result = 0;
    } else {
        StopAudioCapture();
    }
 
    return result;
}

