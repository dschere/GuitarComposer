/*
This module uses the TinySoundFont library in conjunction with the SDL
library to create a homemade synth library. After spending too mauch time
hacking fluidsynth I have thrown in towel and decided to roll my own.

We are allowed upto 15 audio clients. This caps the number of concurrent
channels that can have ladspa audio effects applied to them.

Also based on tsf's design one sound font is allowed on one audio client. 


*/

#include <time.h>
#define TSF_IMPLEMENTATION
#include "tsf.h"

#include <SDL2/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <pthread.h>
#include <unistd.h>

#include "gcsynth.h"
#include "gcsynth_sf.h"
#include "gcsynth_channel.h"

#include "audio_output.h"

#include "gcsynth_sf.h"

#define AUDIO_SAMPLES 512
#define BUFSIZE       0xFFFF
#define MAX_CHANNEL_NUM 128


#define MAX_ATHREADS 15 


struct audio_thread {
    SDL_AudioSpec spec;
    SDL_AudioDeviceID dev;
    // Holds the global instance pointer
    tsf* g_TinySoundFont;

    // A Mutex so we don't call note_on/note_off while rendering audio samples
    GAsyncQueue *queue;

    pthread_attr_t attr;
    pthread_t thread; 
    
    pthread_mutex_t running_mutex;
    int running; 

    int ladspa_channel;   
    int athread;
    int sfont_id;
};

enum {
    SF_NOTEON,
    SF_NOTEOFF,
    SF_SELECT,
    SF_PITCH_WHEEL,
    SF_PITCH_RANGE,
    SF_RESET,
    
    SF_NUM_MSG_TYPES
};

struct audio_thread_msg {
    int ev_type;
    int chan;
    int midicode;
    float vel;
    int bank;
    int preset;
    int pitchWheel;
    float pitch_range;
};


// route all ladspa audio to this callback for any of the 1-14 audio threads.
static AudioChannelFilter AudioFilterFunc;

static struct audio_thread AudioThreads[MAX_ATHREADS];
static int NumAudioThreads;


static struct audio_thread* ChannelAllocTable[MAX_CHANNELS];




/*
Echo experiment to see if the 'noise' disappears if I
do the echo without ladspa.
*/
// double ring1[SAMPLE_RATE];
// int r1 = 0;

// double ring2[SAMPLE_RATE*2];
// int r2 = 0;

// double ring3[SAMPLE_RATE*3];
// int r3 = 0;

// static void echo_test(float* buffer, int samples)
// {
//     int i;

//     for(i = 0; i < samples; i++) {
//         ring1[(r1 + samples + 1) % SAMPLE_RATE]     = buffer[i] * 0.66;
//         ring2[(r2 + samples + 1) % (SAMPLE_RATE*2)] = buffer[i] * 0.33;
//         ring3[(r3 + samples + 1) % (SAMPLE_RATE*3)] = buffer[i] * 0.15;
        
//         buffer[i] += (float)
//             ring1[(r1 + i) % SAMPLE_RATE] +
//             ring2[(r2 + i) % (SAMPLE_RATE*2)] + 
//             ring3[(r3 + i) % (SAMPLE_RATE*3)]
//         ;

//         ring1[(r1 + i) % SAMPLE_RATE] = 0.0;
//         ring2[(r2 + i) % (SAMPLE_RATE*2)] = 0.0;
//         ring3[(r3 + i) % (SAMPLE_RATE*3)] = 0.0;

//         r1++;
//         r2++;
//         r3++;
//     }
     

// }















/*
   refactored tsf_render_float so it routes audio data to ladspa filters
   if enabled for this channel.

Original:

TSFDEF void tsf_render_float(tsf* f, float* buffer, int samples, int flag_mixing)
{
	struct tsf_voice *v = f->voices, *vEnd = v + f->voiceNum;
	if (!flag_mixing) TSF_MEMSET(buffer, 0, (f->outputmode == TSF_MONO ? 1 : 2) * sizeof(float) * samples);
	for (; v != vEnd; v++)
		if (v->playingPreset != -1)
			tsf_voice_render(f, v, buffer, samples);
}
*/
TSFDEF void my_tsf_render_float(tsf* f, float* buffer, int samples)
{
	struct tsf_voice *v = f->voices, *vEnd = v + f->voiceNum;
    int n = (f->outputmode == TSF_MONO ? 1 : 2) * sizeof(float) * samples;
	TSF_MEMSET(buffer, 0, n);
    int i;

	for (; v != vEnd; v++) {
		if (v->playingPreset != -1) {

            if (!gcsynth_channel_filter_is_enabled(v->playingChannel)) {
                tsf_voice_render(f, v, buffer, samples);
            } else {
                float chan_buffer[AUDIO_SAMPLES * 16 * sizeof(float)];

                memset(chan_buffer, 0, n);
                tsf_voice_render(f, v, chan_buffer, samples);

                synth_interleaved_filter_router(v->playingChannel, 
                    chan_buffer, samples);

                for(i = 0; i < n; i++) {
                    buffer[i] += chan_buffer[i];
                }
            }            
        }
    }
}


static struct audio_thread* get_audio_thread(int chan) {
    return ChannelAllocTable[chan % MAX_CHANNELS];
}

static void checkin(int chan) {
    if (chan >=0 && chan < MAX_CHANNELS) {
        ChannelAllocTable[chan] = NULL;
    }
}

static struct audio_thread* checkout(int chan, int sfont_id) {
    struct audio_thread* at = NULL; 
    int a_index;
    
    if (chan < 0 || chan >= MAX_CHANNELS) {
        return NULL;
    }

    at = ChannelAllocTable[chan];

    if (!at) { // if channel not allocated.
        // use the sound font id, multiple channels can share tha same
        // audio thread since they are not using a per channel effect.
        for(a_index = 0; a_index < NumAudioThreads; a_index++) {
            if (sfont_id == AudioThreads[a_index].sfont_id) {
                ChannelAllocTable[chan] = &AudioThreads[a_index];
                at = &AudioThreads[a_index];
                break;
            }
        }
    }

    return at;
}

/**
 * Nonblocking call to the message queue, process any queued 
 * requests.  
 */
static void proc_at_msgs(struct audio_thread* at) {
    struct audio_thread_msg* msg;

    while ((msg = g_async_queue_timeout_pop(at->queue,0)) != NULL) {
        switch(msg->ev_type) {
            case SF_NOTEON:
                tsf_channel_note_on(
                    at->g_TinySoundFont,
                    msg->chan,
                    msg->midicode,
                    msg->vel 
                );
                break;

            case SF_NOTEOFF:
                tsf_channel_note_off(
                    at->g_TinySoundFont,
                    msg->chan,
                    msg->midicode
                );
                break;

            case SF_SELECT:
                tsf_channel_set_bank_preset(at->g_TinySoundFont, 
                msg->chan, msg->bank, msg->preset);    
                break;

            case SF_PITCH_WHEEL:
                tsf_channel_set_pitchwheel(at->g_TinySoundFont, msg->chan, 
                msg->pitchWheel);
                break;

            case SF_PITCH_RANGE:
                tsf_channel_set_pitchrange(at->g_TinySoundFont, msg->chan, 
                    msg->pitch_range);
                break;

            case SF_RESET:
                tsf_reset(at->g_TinySoundFont);
                break;

        }
        free(msg);
    }
}




// compute the actual freq
// struct timespec {
//     time_t   tv_sec;        /* seconds */
//     long     tv_nsec;       /* nanoseconds */
// };


// this gets called SAMPLE_RATE / AUDIO_SAMPLES every second.
static void audio_callback(void *userdata, Uint8 *stream, int len) {
    struct audio_thread* at = (struct audio_thread*) userdata;
    int samples = (len / (2 * sizeof(float))); //2 output channels

   //actual_freq(len);

    // process any pending messages 
    proc_at_msgs(at);
 
    // render to audio buffer while allowing for ladspa effects to 
    // be applied to each playing voice.
	my_tsf_render_float(at->g_TinySoundFont, (float*)stream, samples);

    // optional output such as to a wave file.
    proc_audio_output((float *)stream, samples);
}

static void *audio_thread(void *arg) {
    struct audio_thread* at = (struct audio_thread*) arg;
    SDL_PauseAudioDevice(at->dev, 0);  // Start playback
    int running = 1;

    while (running) {
        SDL_Delay(1000);
        pthread_mutex_lock(&at->running_mutex);
        running = at->running;
        pthread_mutex_unlock(&at->running_mutex);
    }

    printf("audio thread exited\n");

    return NULL;
}



/**
Failed experiment: 
    produced an unwanted echo. 
    never fixed the effects problem.

Audio source thread.

drift = 0

while forever
    start_time = now
    usleep for INPUT_FEED_INTERVAL -drift seconds
    actual_sleep_tm = now - start_time

    samples = actual_sleep_tm * SAMPLE_RATE 
       -- if we slepts for exactly INPUT_FEED_INTERVAL then 
          samples would = SAMPLE_RATE which it almost never will 
          be ;)

    start_proc_time = now

    process queued messages if any.
    
    process sf events + ladspa

    queue output to sdl

    drift = now - start_proc_time
*/
static void *audio_source_thread(void *arg) {
    struct audio_thread* at = (struct audio_thread*) arg;
    struct timespec requested_time, remaining; 
    struct timespec now;
    long nsecs_after_sleep, nsecs_after_proc;
    long interval = 
        (AUDIO_SAMPLES * 1000000000L)/SAMPLE_RATE;
    
    float buffer[AUDIO_SAMPLES * 16 * sizeof(float)];
    int samples;
    float bps = ((float)SAMPLE_RATE) / 1000000000.0;
    float r;

    requested_time.tv_sec = 0;
    requested_time.tv_nsec = interval;

    SDL_PauseAudioDevice(at->dev, 0);  // Start playback
    
    while (1) {        
        nanosleep(&requested_time, &remaining); 

        r = bps * (requested_time.tv_nsec - remaining.tv_nsec);
        samples = (int) r;   
         
        // process any pending messages 
        proc_at_msgs(at);

        my_tsf_render_float(at->g_TinySoundFont, buffer, samples);

        if (SDL_QueueAudio(at->dev, buffer, samples * 2 * sizeof(float)) < 0) {
            fprintf(stderr, "SDL_QueueAudio failed: %s\n", SDL_GetError());
            break;
        }
    }
    
    return NULL;
}








/*
    api methods 
*/


/**
 * Create an audio thread for each sound font since the soundfont library
 * does not support multiple sound fonts.
 */
int gcsynth_sf_init(char* sf_file[], int num_font_files, AudioChannelFilter filter_func) {
    int a_thread;
    
    if (SDL_Init(SDL_INIT_AUDIO) < 0) {
        fprintf(stderr, "SDL_Init failed: %s\n", SDL_GetError());
        return -1;
    }

    if (num_font_files >= (MAX_ATHREADS-1)) {
        fprintf(stderr, "Too many sound fonts!\n");
        return -1;
    }

    NumAudioThreads = num_font_files;
    AudioFilterFunc = filter_func;

    // setup 
    for(a_thread =0; a_thread < num_font_files; a_thread++) {
        int f_index = a_thread; 
        SDL_zero(AudioThreads[a_thread].spec);

        AudioThreads[a_thread].spec.freq = SAMPLE_RATE;
        AudioThreads[a_thread].spec.format =  AUDIO_F32SYS;  // AUDIO_F32;
        AudioThreads[a_thread].spec.channels = 2;
        AudioThreads[a_thread].spec.samples = AUDIO_SAMPLES;
        AudioThreads[a_thread].spec.callback = audio_callback;
        AudioThreads[a_thread].spec.userdata = &AudioThreads[a_thread];
        AudioThreads[a_thread].queue = g_async_queue_new();

        AudioThreads[a_thread].ladspa_channel = -1;
        AudioThreads[a_thread].athread = a_thread;
        // follow the convention of fluidsynth to make porting easier.
        // sfont_id is basically the index for the audio thread
        AudioThreads[a_thread].sfont_id = f_index + 1;  

        AudioThreads[a_thread].g_TinySoundFont = tsf_load_filename(sf_file[f_index]);
        if (!AudioThreads[a_thread].g_TinySoundFont) {
            fprintf(stderr,"Unable to load %s\n", sf_file[f_index]);
            return -1;
        }

     	// Set the SoundFont rendering output mode
	    tsf_set_output(
            AudioThreads[a_thread].g_TinySoundFont, 
            TSF_STEREO_INTERLEAVED, 
            AudioThreads[a_thread].spec.freq, 0);

        AudioThreads[a_thread].dev = SDL_OpenAudioDevice(
                NULL, 
                0, 
        &AudioThreads[a_thread].spec, 
                NULL, 
                0);
        if (AudioThreads[a_thread].dev == 0) {
            fprintf(stderr, "SDL_OpenAudioDevice failed: %s\n", SDL_GetError());
            return -1;
        }

        AudioThreads[a_thread].running = 1;
        if (pthread_mutex_init(&AudioThreads[a_thread].running_mutex, NULL) != 0) {
            perror("Mutex initialization failed");
            return 1;
        }
    
        // create deamon threads that terminate when the application exits
        pthread_attr_init(&AudioThreads[a_thread].attr);
        pthread_attr_setdetachstate(
            &AudioThreads[a_thread].attr,PTHREAD_CREATE_DETACHED);

        // launch audio thread 
        if (pthread_create(
            &AudioThreads[a_thread].thread, 
            &AudioThreads[a_thread].attr, 
            audio_thread, 
            &AudioThreads[a_thread]) != 0) 
        {
            perror("pthread_create");
            return -1;
        }
    }
    
    return 0;
}


/**
 * bind a channel with a particular audio thread for a given soundfont id
 */
int gcsynth_sf_select(int chan, int sfont_id, int bank, int preset)
{
    int ret = -1; 
    
    struct audio_thread* at = checkout(chan, sfont_id);
    if (at) {
        struct audio_thread_msg* msg = (struct audio_thread_msg*)
            calloc(sizeof(struct audio_thread_msg),1);
        if (msg != NULL) {
            msg->ev_type = SF_SELECT;
            msg->chan = chan;
            msg->bank = bank;
            msg->preset = preset;

            g_async_queue_push(at->queue, msg);
            ret = 0;
        }
    }

    return ret;
}

// noteon event
int gcsynth_sf_noteon(int chan, int midicode, int vel)
{
    int ret = -1;
    struct audio_thread* at = get_audio_thread(chan);

    if (at) {
        struct audio_thread_msg* msg = (struct audio_thread_msg*)
            calloc(sizeof(struct audio_thread_msg),1);
        if (msg != NULL) {
            msg->ev_type = SF_NOTEON;
            msg->chan = chan;
            msg->midicode = midicode;
            msg->vel = vel / 128.0;    

            g_async_queue_push(at->queue, msg);
            ret = 0;
        }
    } else {
        fprintf(stderr,"gcsynth_sf_noteon: audio thread has not been started!\n");
    }

    return ret;
}

// noteoff
int gcsynth_sf_noteoff(int chan, int midicode)
{
    int ret = -1;
    struct audio_thread* at = get_audio_thread(chan);

    if (at) {
        struct audio_thread_msg* msg = (struct audio_thread_msg*)
            calloc(sizeof(struct audio_thread_msg),1);
        if (msg != NULL) {
            msg->ev_type = SF_NOTEOFF;
            msg->chan = chan;
            msg->midicode = midicode;

            g_async_queue_push(at->queue, msg);
            ret = 0;
        }

    }
    return ret;
}

// change the pitch of a playing note
// this is how to mechanize a bend/slide guitar 
// effect.
int gcsynth_sf_pitchwheel(int chan, float semitones) 
{
    int ret = -1;
    struct audio_thread* at = get_audio_thread(chan);
    int pitchWheel;

    if (at) {
        float pr = tsf_channel_get_pitchrange(at->g_TinySoundFont, chan);
        float r = semitones / pr;

        pitchWheel = 8192 + (r * 8192);

        struct audio_thread_msg* msg = (struct audio_thread_msg*)
            calloc(sizeof(struct audio_thread_msg),1);
        if (msg != NULL) {
            msg->ev_type = SF_PITCH_WHEEL;
            msg->chan = chan;
            msg->pitchWheel = pitchWheel; 

            g_async_queue_push(at->queue, msg);
            ret = 0;
        }
    }
    return ret;
}

// set the sensitivity of the pitchwheel at the expense
// of the range. So we would want a large range for a whammy
// bar and small range for bend for precision.
int gcsynth_sf_pitchrange(int chan, float pitch_range) 
{
    int ret = -1;
    struct audio_thread* at = get_audio_thread(chan);

    if (at) {
        struct audio_thread_msg* msg = (struct audio_thread_msg*)
            calloc(sizeof(struct audio_thread_msg),1);
        if (msg != NULL) {
            msg->ev_type = SF_PITCH_RANGE;
            msg->chan = chan;
            msg->pitch_range = pitch_range; 

            g_async_queue_push(at->queue, msg);
            ret = 0;
        }
    }
    return ret;
}        

// reset all channels.
void gcsynth_sf_reset()
{
    int a_thread;
        
    for(a_thread =0; a_thread < MAX_ATHREADS; a_thread++) {
        struct audio_thread* at = &AudioThreads[a_thread];

        struct audio_thread_msg* msg = (struct audio_thread_msg*)
            calloc(sizeof(struct audio_thread_msg),1);
        if (msg != NULL) {
            msg->ev_type = SF_RESET;
            g_async_queue_push(at->queue, msg);
        }

        at->ladspa_channel = -1;
    }
    memset(ChannelAllocTable, 0, sizeof(ChannelAllocTable));
}


/*
    Clear the running flag for all threads.
*/
void gcsynth_sf_shutdown() {
    int i;
    for (i = 0; i < NumAudioThreads; i++) {
        struct audio_thread* at = &AudioThreads[i];
        pthread_mutex_lock(&at->running_mutex);
        at->running = 0;
        pthread_mutex_unlock(&at->running_mutex);
    }

    for (i = 0; i < NumAudioThreads; i++) {
        struct audio_thread* at = &AudioThreads[i];
        pthread_join(at->thread, NULL);
    }
}