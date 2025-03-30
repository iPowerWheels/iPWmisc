#include <stdio.h>
#include <stdlib.h>
#include <tesseract/capi.h>
#include <leptonica/allheaders.h>

int main(int argc, char *argv[]) {
    if (argc != 2) {
        printf("Uso: %s <imagen>\n", argv[0]);
        return 1;
    }

    char *image_path = argv[1];

    // Cargar la imagen
    PIX *image = pixRead(image_path);
    if (!image) {
        printf("Error al cargar la imagen %s\n", image_path);
        return 1;
    }

    // Inicializar Tesseract
    TessBaseAPI *api = TessBaseAPICreate();
    if (TessBaseAPIInit3(api, NULL, "eng") != 0) {
        printf("Error al inicializar Tesseract\n");
        pixDestroy(&image);
        TessBaseAPIDelete(api);
        return 1;
    }

    // Procesar la imagen
    TessBaseAPISetImage2(api, image);
    TessBaseAPIRecognize(api, NULL);

    // Obtener el texto
    char *text = TessBaseAPIGetUTF8Text(api);
    printf("\nTexto OCR:\n%s\n", text);

    // Liberar memoria
    TessDeleteText(text);
    TessBaseAPIDelete(api);
    pixDestroy(&image);

    return 0;
}
