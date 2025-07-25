/**
 * A simple wav reader with RMS metering using libsndfile and libsamplerate.
 */

#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

#include <jack/jack.h>
#include <sndfile.h>
#include <samplerate.h>

jack_port_t **output_port;
jack_client_t *client;

SNDFILE *audio_file;
SF_INFO audio_info;
unsigned int audio_position = 0;

#define DEFAULT_CONVERTER SRC_SINC_BEST_QUALITY
float *samplerate_buff_in;
SRC_STATE *samplerate_conv;
SRC_DATA samplerate_data;

unsigned int channels = 2;
double sample_rate;

void print_rms(float rms_l, float rms_r) {
    printf("\rAudio pos: %d (%.2f s) | L: %5.2f | R: %5.2f     ",
           audio_position, (double)audio_position / sample_rate, rms_l, rms_r);
    fflush(stdout);
}

int jack_callback(jack_nframes_t nframes, void *arg) {
    jack_default_audio_sample_t **out;
    int i, j, error;

    out = (jack_default_audio_sample_t **)malloc(channels * sizeof(jack_default_audio_sample_t *));
    for (i = 0; i < channels; i++)
        out[i] = (jack_default_audio_sample_t *)jack_port_get_buffer(output_port[i], nframes);

    if (samplerate_data.input_frames == 0) {
        samplerate_data.input_frames = sf_readf_float(audio_file, samplerate_buff_in, nframes);
        samplerate_data.data_in = samplerate_buff_in;
        if (samplerate_data.input_frames < nframes)
            samplerate_data.end_of_input = SF_TRUE;
    }

    if ((error = src_process(samplerate_conv, &samplerate_data))) {
        printf("\nError : %s\n", src_strerror(error));
        exit(1);
    }

    if (samplerate_data.end_of_input && samplerate_data.output_frames_gen == 0) {
        printf("\nFinished reading file.\n");
        sf_close(audio_file);
        src_delete(samplerate_conv);
        jack_client_close(client);
        exit(1);
    }

    float sum_l = 0.0f, sum_r = 0.0f;
    for (i = 0; i < nframes; i++) {
        for (j = 0; j < channels; j++) {
            if (samplerate_data.input_frames != nframes && i >= samplerate_data.input_frames) {
                out[j][i] = 0.0;
            } else {
                float sample = samplerate_data.data_out[i * channels + j];
                out[j][i] = sample;
                if (j == 0) sum_l += sample * sample;
                else if (j == 1) sum_r += sample * sample;
            }
        }
    }

    float rms_l = sqrt(sum_l / nframes);
    float rms_r = sqrt(sum_r / nframes);

    samplerate_data.data_in += samplerate_data.input_frames_used * channels;
    samplerate_data.input_frames -= samplerate_data.input_frames_used;

    audio_position += samplerate_data.output_frames_gen;
    print_rms(rms_l, rms_r);

    free(out);
    return 0;
}

void jack_shutdown(void *arg) {
    exit(1);
}

int main(int argc, char *argv[]) {
    if (argc != 2) {
        printf("Audio File Path not provided.\n");
        exit(1);
    }

    char audio_file_path[100];
    strcpy(audio_file_path, argv[1]);
    printf("Trying to open audio File: %s\n", audio_file_path);

    audio_file = sf_open(audio_file_path, SFM_READ, &audio_info);
    if (audio_file == NULL) {
        printf("%s\n", sf_strerror(NULL));
        exit(1);
    } else {
        printf("Audio file info:\n");
        printf("\tSample Rate: %d\n", audio_info.samplerate);
        printf("\tChannels: %d\n", audio_info.channels);
        SF_FORMAT_INFO audio_format_info;
        sf_command(NULL, SFC_GET_FORMAT_INFO, &audio_format_info, sizeof(SF_FORMAT_INFO));
        printf("\tFormat: %s\n", audio_format_info.name);
    }

    const char *client_name = "read_audio_file_samplerate";
    jack_options_t options = JackNoStartServer;
    jack_status_t status;

    client = jack_client_open(client_name, options, &status);
    if (client == NULL) {
        printf("jack_client_open() failed, status = 0x%2.0x\n", status);
        if (status & JackServerFailed) {
            printf("Unable to connect to JACK server.\n");
        }
        exit(1);
    }

    if (status & JackNameNotUnique) {
        client_name = jack_get_client_name(client);
        printf("Warning: `%s' has been assigned to us.\n", client_name);
    }

    jack_set_process_callback(client, jack_callback, 0);
    jack_on_shutdown(client, jack_shutdown, 0);

    sample_rate = (double)jack_get_sample_rate(client);
    printf("Engine sample rate: %0.0f\n", sample_rate);
    printf("Engine window size: %d\n", jack_get_buffer_size(client));

    printf("Creating the sample rate converter...\n");
    int samplerate_error;
    samplerate_conv = src_new(DEFAULT_CONVERTER, channels, &samplerate_error);
    if (samplerate_conv == NULL) {
        printf("%s\n", src_strerror(samplerate_error));
        exit(1);
    }

    samplerate_data.src_ratio = sample_rate / (double)audio_info.samplerate;
    printf("Using samplerate ratio: %f\n", samplerate_data.src_ratio);
    if (!src_is_valid_ratio(samplerate_data.src_ratio)) {
        printf("Error: Sample rate change out of valid range.\n");
        sf_close(audio_file);
        exit(1);
    }

    samplerate_buff_in = (float *)malloc(jack_get_buffer_size(client) * channels * sizeof(float));
    samplerate_data.data_in = samplerate_buff_in;
    samplerate_data.data_out = (float *)malloc(jack_get_buffer_size(client) * channels * sizeof(float));
    samplerate_data.input_frames = 0;
    samplerate_data.output_frames = jack_get_buffer_size(client);
    samplerate_data.end_of_input = 0;

    output_port = malloc(channels * sizeof(jack_port_t *));
    char port_name[50];
    for (int i = 0; i < channels; i++) {
        sprintf(port_name, "output_%d", i);
        output_port[i] = jack_port_register(client, port_name, JACK_DEFAULT_AUDIO_TYPE, JackPortIsOutput, 0);
        if (output_port[i] == NULL) {
            printf("no more JACK ports available after %d\n", i);
            exit(1);
        }
    }

    if (jack_activate(client)) {
        printf("Cannot activate client.\n");
        exit(1);
    }

    printf("Agent activated.\n");
    printf("Connecting ports... ");
    const char **serverports_names = jack_get_ports(client, NULL, NULL, JackPortIsPhysical | JackPortIsInput);
    if (serverports_names == NULL) {
        printf("no available physical playback (server input) ports.\n");
        exit(1);
    }

    for (int i = 0; i < channels; i++) {
        if (jack_connect(client, jack_port_name(output_port[i]), serverports_names[i])) {
            printf("cannot connect output ports\n");
            exit(1);
        }
    }
    free(serverports_names);
    printf("done.\n");

    sleep(-1);
    jack_client_close(client);
    return 0;
}