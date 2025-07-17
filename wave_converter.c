// wave_converter.c
#include <stdio.h>
#include <stdlib.h>
#include <sndfile.h>
#include <samplerate.h>

#define INPUT_FILE "input.wav"
#define OUTPUT_FILE "output.wav"
#define TARGET_SR 48000

int main(void) {
    // Abrir archivo de entrada
    SF_INFO sfinfo_in;
    SNDFILE *infile = sf_open(INPUT_FILE, SFM_READ, &sfinfo_in);
    if (!infile) {
        fprintf(stderr, "Error abriendo '%s'\n", INPUT_FILE);
        return 1;
    }

    if (sfinfo_in.samplerate != 44100) {
        fprintf(stderr, "Este archivo no es de 44100 Hz. Es de %d Hz.\n", sfinfo_in.samplerate);
        sf_close(infile);
        return 1;
    }

    // Leer todo el audio
    sf_count_t num_frames = sfinfo_in.frames;
    float *input_data = malloc(num_frames * sfinfo_in.channels * sizeof(float));
    if (!input_data) {
        fprintf(stderr, "Memoria insuficiente\n");
        sf_close(infile);
        return 1;
    }

    sf_readf_float(infile, input_data, num_frames);
    sf_close(infile);

    // Calcular número de frames nuevos
    double ratio = (double)TARGET_SR / sfinfo_in.samplerate;
    sf_count_t output_frames = (sf_count_t)(num_frames * ratio + 1); // ceil-like
    float *output_data = malloc(output_frames * sfinfo_in.channels * sizeof(float));
    if (!output_data) {
        fprintf(stderr, "Memoria insuficiente para output\n");
        free(input_data);
        return 1;
    }

    // Configurar libsamplerate
    SRC_DATA src_data = {
        .data_in = input_data,
        .data_out = output_data,
        .input_frames = num_frames,
        .output_frames = output_frames,
        .src_ratio = ratio,
        .end_of_input = SF_TRUE
    };

    int error = src_simple(&src_data, SRC_SINC_BEST_QUALITY, sfinfo_in.channels);
    if (error) {
        fprintf(stderr, "Error en resampleo: %s\n", src_strerror(error));
        free(input_data);
        free(output_data);
        return 1;
    }

    // Guardar archivo de salida
    SF_INFO sfinfo_out = sfinfo_in;
    sfinfo_out.samplerate = TARGET_SR;
    sfinfo_out.frames = src_data.output_frames_gen;

    SNDFILE *outfile = sf_open(OUTPUT_FILE, SFM_WRITE, &sfinfo_out);
    if (!outfile) {
        fprintf(stderr, "No se pudo crear '%s'\n", OUTPUT_FILE);
        free(input_data);
        free(output_data);
        return 1;
    }

    sf_writef_float(outfile, output_data, src_data.output_frames_gen);
    sf_close(outfile);

    printf("Conversión completada: '%s' → '%s'\n", INPUT_FILE, OUTPUT_FILE);

    free(input_data);
    free(output_data);
    return 0;
}

