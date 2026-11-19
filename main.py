from pathlib import Path
from uuid import uuid4
import sqlite3
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "musicbox.db"
MUSIC_DIR = ROOT / "music"
ALLOWED_EXTENSION = ".mp3"
MAX_UPLOAD_BYTES = 50 * 1024 * 1024


def connect_db(db_path=DB_PATH):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(db_path=DB_PATH):
    with connect_db(db_path) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                filename TEXT NOT NULL UNIQUE,
                position INTEGER NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()


def create_app(db_path=DB_PATH, music_dir=MUSIC_DIR):
    app = FastAPI(title="MusicBox", description="Reproductor musical personal")
    music_dir = Path(music_dir)
    music_dir.mkdir(parents=True, exist_ok=True)
    initialize_database(db_path)

    app.state.db_path = db_path
    app.state.music_dir = music_dir
    app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")
    templates = Jinja2Templates(directory=str(ROOT / "templates"))

    def get_songs(query=""):
        with connect_db(app.state.db_path) as db:
            if query.strip():
                return db.execute(
                    "SELECT * FROM songs WHERE title LIKE ? ORDER BY position ASC, id DESC",
                    (f"%{query.strip()}%",)
                ).fetchall()
            return db.execute(
                "SELECT * FROM songs ORDER BY position ASC, id DESC"
            ).fetchall()

    @app.get("/", response_class=HTMLResponse)
    async def home(request: Request, q: str = ""):
        songs = get_songs(q)
        return templates.TemplateResponse(
            request, "index.html",
            {"songs": songs, "query": q}
        )

    @app.post("/upload")
    async def upload_song(file: UploadFile = File(...)):
        original_name = Path(file.filename or "").name
        if Path(original_name).suffix.lower() != ALLOWED_EXTENSION:
            raise HTTPException(status_code=400, detail="Solo se permiten archivos MP3.")

        content = await file.read(MAX_UPLOAD_BYTES + 1)
        if not content:
            raise HTTPException(status_code=400, detail="El archivo está vacío.")
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="El archivo supera el límite de 50 MB.")

        safe_name = f"{uuid4().hex}.mp3"
        destination = app.state.music_dir / safe_name
        destination.write_bytes(content)
        title = Path(original_name).stem.strip() or "Canción sin título"

        try:
            with connect_db(app.state.db_path) as db:
                db.execute("UPDATE songs SET position = position + 1")
                db.execute(
                    "INSERT INTO songs (title, filename, position) VALUES (?, ?, 0)",
                    (title, safe_name)
                )
                db.commit()
        except Exception:
            destination.unlink(missing_ok=True)
            raise

        return RedirectResponse(url="/", status_code=303)

    @app.post("/delete/{song_id}")
    async def delete_song(song_id: int):
        with connect_db(app.state.db_path) as db:
            song = db.execute("SELECT * FROM songs WHERE id = ?", (song_id,)).fetchone()
            if song is None:
                raise HTTPException(status_code=404, detail="Canción no encontrada.")
            db.execute("DELETE FROM songs WHERE id = ?", (song_id,))
            db.commit()

        (app.state.music_dir / song["filename"]).unlink(missing_ok=True)
        return RedirectResponse(url="/", status_code=303)

    @app.get("/play/{song_id}")
    async def play_song(song_id: int):
        with connect_db(app.state.db_path) as db:
            song = db.execute("SELECT * FROM songs WHERE id = ?", (song_id,)).fetchone()
        if song is None:
            raise HTTPException(status_code=404, detail="Canción no encontrada.")
        path = app.state.music_dir / song["filename"]
        if not path.is_file():
            raise HTTPException(status_code=404, detail="El archivo de audio no existe.")
        return FileResponse(path, media_type="audio/mpeg", filename=song["filename"])

    @app.post("/reorder")
    async def reorder_songs(request: Request):
        data = await request.json()
        song_ids = data.get("song_ids", [])
        if not isinstance(song_ids, list) or not all(isinstance(x, int) for x in song_ids):
            raise HTTPException(status_code=400, detail="Orden de canciones inválido.")

        with connect_db(app.state.db_path) as db:
            existing = {row["id"] for row in db.execute("SELECT id FROM songs").fetchall()}
            if len(song_ids) != len(existing) or set(song_ids) != existing:
                raise HTTPException(status_code=400, detail="La lista debe contener todas las canciones una sola vez.")
            for position, song_id in enumerate(song_ids):
                db.execute("UPDATE songs SET position = ? WHERE id = ?", (position, song_id))
            db.commit()
        return JSONResponse({"ok": True})

    @app.get("/next/{song_id}")
    async def next_song(song_id: int):
        songs = get_songs()
        ids = [song["id"] for song in songs]
        if song_id not in ids or not ids:
            raise HTTPException(status_code=404, detail="No hay siguiente canción.")
        index = ids.index(song_id)
        next_id = ids[(index + 1) % len(ids)]
        return {"id": next_id, "url": f"/play/{next_id}", "title": songs[(index + 1) % len(ids)]["title"]}

    return app


app = create_app()
