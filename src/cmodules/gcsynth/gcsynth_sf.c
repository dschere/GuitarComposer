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
#include <glib.h>

#include "gcsynth.h"
#include "gcsynth_sf.h"
#include "gcsynth_channel.h"


#include "gcsynth_sf.h"


//#define AUDIO_SAMPLES 512
#define BUFSIZE       0xFFFF
//#define MAX_CHANNEL_NUM 128


#define MAX_ATHREADS 13 


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

static struct audio_thread* ChannelAllocTable[NUM_CHANNELS];


struct voice_render_result {
    int out_samples;
    float* outL;
    float* outR;
};

struct voice_render_result my_tsf_voice_render(tsf* f, struct tsf_voice* v, float* outputBuffer, int numSamples)
{
	struct tsf_region* region = v->region;
	float* input = f->fontSamples;
	float* outL = outputBuffer;
	float* outR = (f->outputmode == TSF_STEREO_UNWEAVED ? outL + numSamples : TSF_NULL);
    struct voice_render_result result;

    result.out_samples = 0;
    result.outL = outL;
    result.outR = outR;

	// Cache some values, to give them at least some chance of ending up in registers.
	TSF_BOOL updateModEnv = (region->modEnvToPitch || region->modEnvToFilterFc);
	TSF_BOOL updateModLFO = (v->modlfo.delta && (region->modLfoToPitch || region->modLfoToFilterFc || region->modLfoToVolume));
	TSF_BOOL updateVibLFO = (v->viblfo.delta && (region->vibLfoToPitch));
	TSF_BOOL isLooping    = (v->loopStart < v->loopEnd);
	unsigned int tmpLoopStart = v->loopStart, tmpLoopEnd = v->loopEnd;
	double tmpSampleEndDbl = (double)region->end, tmpLoopEndDbl = (double)tmpLoopEnd + 1.0;
	double tmpSourceSamplePosition = v->sourceSamplePosition;
	struct tsf_voice_lowpass tmpLowpass = v->lowpass;

	TSF_BOOL dynamicLowpass = (region->modLfoToFilterFc || region->modEnvToFilterFc);
	float tmpSampleRate = f->outSampleRate, tmpInitialFilterFc, tmpModLfoToFilterFc, tmpModEnvToFilterFc;

	TSF_BOOL dynamicPitchRatio = (region->modLfoToPitch || region->modEnvToPitch || region->vibLfoToPitch);
	double pitchRatio;
	float tmpModLfoToPitch, tmpVibLfoToPitch, tmpModEnvToPitch;

	TSF_BOOL dynamicGain = (region->modLfoToVolume != 0);
	float noteGain = 0, tmpModLfoToVolume;

	if (dynamicLowpass) tmpInitialFilterFc = (float)region->initialFilterFc, tmpModLfoToFilterFc = (float)region->modLfoToFilterFc, tmpModEnvToFilterFc = (float)region->modEnvToFilterFc;
	else tmpInitialFilterFc = 0, tmpModLfoToFilterFc = 0, tmpModEnvToFilterFc = 0;

	if (dynamicPitchRatio) pitchRatio = 0, tmpModLfoToPitch = (float)region->modLfoToPitch, tmpVibLfoToPitch = (float)region->vibLfoToPitch, tmpModEnvToPitch = (float)region->modEnvToPitch;
	else pitchRatio = tsf_timecents2Secsd(v->pitchInputTimecents) * v->pitchOutputFactor, tmpModLfoToPitch = 0, tmpVibLfoToPitch = 0, tmpModEnvToPitch = 0;

	if (dynamicGain) tmpModLfoToVolume = (float)region->modLfoToVolume * 0.1f;
	else noteGain = tsf_decibelsToGain(v->noteGainDB), tmpModLfoToVolume = 0;

	while (numSamples)
	{
		float gainMono, gainLeft, gainRight;
		int blockSamples = (numSamples > TSF_RENDER_EFFECTSAMPLEBLOCK ? TSF_RENDER_EFFECTSAMPLEBLOCK : numSamples);
		numSamples -= blockSamples;

		if (dynamicLowpass)
		{
			float fres = tmpInitialFilterFc + v->modlfo.level * tmpModLfoToFilterFc + v->modenv.level * tmpModEnvToFilterFc;
			float lowpassFc = (fres <= 13500 ? tsf_cents2Hertz(fres) / tmpSampleRate : 1.0f);
			tmpLowpass.active = (lowpassFc < 0.499f);
			if (tmpLowpass.active) tsf_voice_lowpass_setup(&tmpLowpass, lowpassFc);
		}

		if (dynamicPitchRatio)
			pitchRatio = tsf_timecents2Secsd(v->pitchInputTimecents + (v->modlfo.level * tmpModLfoToPitch + v->viblfo.level * tmpVibLfoToPitch + v->modenv.level * tmpModEnvToPitch)) * v->pitchOutputFactor;

		if (dynamicGain)
			noteGain = tsf_decibelsToGain(v->noteGainDB + (v->modlfo.level * tmpModLfoToVolume));

		gainMono = noteGain * v->ampenv.level;

		// Update EG.
		tsf_voice_envelope_process(&v->ampenv, blockSamples, tmpSampleRate);
		if (updateModEnv) tsf_voice_envelope_process(&v->modenv, blockSamples, tmpSampleRate);

		// Update LFOs.
		if (updateModLFO) tsf_voice_lfo_process(&v->modlfo, blockSamples);
		if (updateVibLFO) tsf_voice_lfo_process(&v->viblfo, blockSamples);

		switch (f->outputmode)
		{
			case TSF_STEREO_INTERLEAVED:
				gainLeft = gainMono * v->panFactorLeft, gainRight = gainMono * v->panFactorRight;
				while (blockSamples-- && tmpSourceSamplePosition < tmpSampleEndDbl)
				{
					unsigned int pos = (unsigned int)tmpSourceSamplePosition, nextPos = (pos >= tmpLoopEnd && isLooping ? tmpLoopStart : pos + 1);

					// Simple linear interpolation.
					float alpha = (float)(tmpSourceSamplePosition - pos), val = (input[pos] * (1.0f - alpha) + input[nextPos] * alpha);

					// Low-pass filter.
					if (tmpLowpass.active) val = tsf_voice_lowpass_process(&tmpLowpass, val);

					*outL++ += val * gainLeft;
					*outL++ += val * gainRight;

                    result.out_samples++;  

					// Next sample.
					tmpSourceSamplePosition += pitchRatio;
					if (tmpSourceSamplePosition >= tmpLoopEndDbl && isLooping) tmpSourceSamplePosition -= (tmpLoopEnd - tmpLoopStart + 1.0);
				}
				break;

			case TSF_STEREO_UNWEAVED:
				gainLeft = gainMono * v->panFactorLeft, gainRight = gainMono * v->panFactorRight;
				while (blockSamples-- && tmpSourceSamplePosition < tmpSampleEndDbl)
				{
					unsigned int pos = (unsigned int)tmpSourceSamplePosition, nextPos = (pos >= tmpLoopEnd && isLooping ? tmpLoopStart : pos + 1);

					// Simple linear interpolation.
					float alpha = (float)(tmpSourceSamplePosition - pos), val = (input[pos] * (1.0f - alpha) + input[nextPos] * alpha);

					// Low-pass filter.
					if (tmpLowpass.active) val = tsf_voice_lowpass_process(&tmpLowpass, val);


					*outL++ += val * gainLeft;
					*outR++ += val * gainRight;

                    result.out_samples++;

					// Next sample.
					tmpSourceSamplePosition += pitchRatio;
					if (tmpSourceSamplePosition >= tmpLoopEndDbl && isLooping) tmpSourceSamplePosition -= (tmpLoopEnd - tmpLoopStart + 1.0);
				}
				break;

			case TSF_MONO:
				while (blockSamples-- && tmpSourceSamplePosition < tmpSampleEndDbl)
				{
					unsigned int pos = (unsigned int)tmpSourceSamplePosition, nextPos = (pos >= tmpLoopEnd && isLooping ? tmpLoopStart : pos + 1);

					// Simple linear interpolation.
					float alpha = (float)(tmpSourceSamplePosition - pos), val = (input[pos] * (1.0f - alpha) + input[nextPos] * alpha);

					// Low-pass filter.
					if (tmpLowpass.active) val = tsf_voice_lowpass_process(&tmpLowpass, val);

					*outL++ += val * gainMono;
                    result.out_samples++;

					// Next sample.
					tmpSourceSamplePosition += pitchRatio;
					if (tmpSourceSamplePosition >= tmpLoopEndDbl && isLooping) tmpSourceSamplePosition -= (tmpLoopEnd - tmpLoopStart + 1.0);
				}
				break;
		}

		if (tmpSourceSamplePosition >= tmpSampleEndDbl || v->ampenv.segment == TSF_SEGMENT_DONE)
		{
			tsf_voice_kill(v);
			return result;
		}
	}

	v->sourceSamplePosition = tmpSourceSamplePosition;
	if (tmpLowpass.active || dynamicLowpass) v->lowpass = tmpLowpass;

    return result;
}

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
            float chan_buffer[AUDIO_SAMPLES * 2];
            //float* left, *right;
            struct voice_render_result vr;

            memset(chan_buffer, 0, sizeof(chan_buffer));

            vr = my_tsf_voice_render(f, v, chan_buffer, samples);
        
            if (gcsynth_channel_filter_is_enabled(v->playingChannel)) { 
                synth_filter_router(
                    v->playingChannel, vr.outL, vr.outR, samples);
            }

            // convert to interleaved output.
            for(i = 0; i < vr.out_samples; i++) {
                buffer[i * 2] += vr.outL[i];
                buffer[i * 2 + 1] += vr.outR[i];
            }                        
        }
    }

    //FUTURE
    // this is were I could create a master effects output 
    // or stream the audio to a file, at this point we have 
    // interleaved audio samples post per channel effects. 
}


static struct audio_thread* get_audio_thread(int chan) {
    return ChannelAllocTable[chan % NUM_CHANNELS];
}

static struct audio_thread* checkout(int chan, int sfont_id) {
    struct audio_thread* at = NULL; 
    int a_index;
    
    if (chan < 0 || chan >= NUM_CHANNELS) {
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
    SDL_CloseAudioDevice(at->dev);
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

        AudioThreads[a_thread].g_TinySoundFont = tsf_load_filename(sf_file[f_index]);
        if (!AudioThreads[a_thread].g_TinySoundFont) {
            fprintf(stderr,"Unable to load %s\n", sf_file[f_index]);
            return -1;
        }
        int sample_rate = (int) 
            AudioThreads[a_thread].g_TinySoundFont->outSampleRate;

        printf("%s sample_rate = %d\n", sf_file[f_index], sample_rate);    

        AudioThreads[a_thread].spec.freq = sample_rate;
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


     	// Set the SoundFont rendering output mode
	    tsf_set_output(
            AudioThreads[a_thread].g_TinySoundFont, 
            TSF_STEREO_UNWEAVED, 
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