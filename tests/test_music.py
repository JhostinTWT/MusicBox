from io import BytesIO
from fastapi.testclient import TestClient
from main import create_app


def make_client(tmp_path):
    app = create_app(tmp_path / "test.db", tmp_path / "music")
    return TestClient(app)


def test_home_route_responds(tmp_path):
    client = make_client(tmp_path)
    response = client.get("/")
    assert response.status_code == 200
    assert "MusicBox" in response.text


def test_upload_mp3_adds_song_to_library(tmp_path):
    client = make_client(tmp_path)
    response = client.post(
        "/upload",
        files={"file": ("mi_cancion.mp3", BytesIO(b"fake mp3 data"), "audio/mpeg")},
        follow_redirects=False
    )
    assert response.status_code == 303
    page = client.get("/")
    assert "mi_cancion" in page.text


def test_non_mp3_is_rejected(tmp_path):
    client = make_client(tmp_path)
    response = client.post(
        "/upload",
        files={"file": ("documento.txt", BytesIO(b"texto"), "text/plain")}
    )
    assert response.status_code == 400


def test_delete_song_removes_it(tmp_path):
    client = make_client(tmp_path)
    client.post("/upload", files={"file": ("tema.mp3", BytesIO(b"audio"), "audio/mpeg")}, follow_redirects=False)
    import sqlite3
    db = sqlite3.connect(tmp_path / "test.db")
    song_id = db.execute("SELECT id FROM songs").fetchone()[0]
    db.close()
    response = client.post(f"/delete/{song_id}", follow_redirects=False)
    assert response.status_code == 303
    assert "tema" not in client.get("/").text
