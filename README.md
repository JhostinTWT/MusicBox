# MusicBox

Reproductor musical personal desarrollado con Python, FastAPI, Jinja2, SQLite, HTML, CSS y JavaScript.

## Funciones
- Subir archivos MP3 a la carpeta local `music/`.
- Mostrar las canciones más recientes primero.
- Buscar por nombre.
- Eliminar canciones y sus archivos.
- Reordenar la lista arrastrando las canciones.
- Reproducir audio desde el navegador.
- Controles de siguiente, repetir y aleatorio.

## Requisitos
Python 3.10 o superior.

## Instalación
```bash
python -m venv venv
```
En Windows:
```bash
venv\Scripts\activate
```
En macOS/Linux:
```bash
source venv/bin/activate
```
Instala las dependencias:
```bash
pip install -r requirements.txt
```

## Ejecutar
```bash
uvicorn main:app --reload
```
Abre http://127.0.0.1:8000

## Pruebas
```bash
pytest -v
```

## Organización
- `main.py`: aplicación FastAPI, rutas, validaciones y acceso a SQLite.
- `templates/index.html`: estructura de la interfaz Jinja2.
- `static/styles.css`: diseño visual.
- `static/script.js`: controles del reproductor y reordenamiento.
- `music/`: archivos MP3 subidos por el usuario.
- `tests/`: pruebas automatizadas.

## Nota sobre archivos
MusicBox guarda los archivos de audio dentro de `music/` y los metadatos en `musicbox.db`. La validación actual comprueba la extensión `.mp3`; para una versión de producción convendría validar también el contenido real del archivo.
