# GOL Playlist Builder

Aplicación Windows para pegar una captura de la parrilla de Excel, leerla con OCR, buscar el material recursivamente dentro de una carpeta raíz y generar un `.m3u`.

No necesita el enlace de SharePoint.

## GitHub gratis → EXE

1. Crea un repositorio vacío en GitHub.
2. Sube esta carpeta completa.
3. Añade el workflow de `.github/workflows/build-windows.yml` (incluido).
4. Ve a **Actions → Build Windows EXE → Run workflow**.
5. Descarga el artefacto generado.

El EXE se construye en un runner Windows de GitHub Actions e incluye Tesseract OCR.

## Uso

1. Abre la parrilla en Excel.
2. Haz una captura de las filas que necesitas.
3. Copia la captura al portapapeles.
4. Abre el programa y pulsa **Pegar captura**.
5. Selecciona `D:\PARRILLAS\GOL`.
6. Pulsa **Analizar**.
7. Revisa las coincidencias.
8. Pulsa **Generar M3U**.

El buscador usa `rglob`, por lo que recorre todas las subcarpetas de la carpeta raíz.

## Nota

La primera versión está enfocada al flujo real: screenshot → OCR → búsqueda recursiva → M3U. Las equivalencias de cortinillas se pueden ampliar en `app/config.json`.
