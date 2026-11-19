const audio = document.getElementById("audio-player");
const titleDisplay = document.getElementById("current-title");
const mainPlay = document.getElementById("main-play");
const list = document.getElementById("song-list");
let currentId = null;
let currentTitle = "";
let repeatOne = false;
let shuffleMode = false;

function playSong(id, title) {
  currentId = Number(id);
  currentTitle = title;
  audio.src = `/play/${id}`;
  titleDisplay.textContent = title;
  audio.play().catch(() => {});
  mainPlay.textContent = "Ⅱ";
}
document.querySelectorAll(".play-track").forEach(button => {
  button.addEventListener("click", () => playSong(button.dataset.id, button.dataset.title));
});
mainPlay.addEventListener("click", () => {
  if (!audio.src) {
    const first = document.querySelector(".play-track");
    if (first) playSong(first.dataset.id, first.dataset.title);
    return;
  }
  if (audio.paused) { audio.play(); mainPlay.textContent = "Ⅱ"; }
  else { audio.pause(); mainPlay.textContent = "▶"; }
});
audio.addEventListener("ended", async () => {
  if (repeatOne) { audio.currentTime = 0; audio.play(); return; }
  await playNext();
});
async function playNext() {
  const tracks = [...document.querySelectorAll(".track")];
  if (!tracks.length) return;
  let target;
  if (shuffleMode) {
    const choices = tracks.filter(t => Number(t.dataset.id) !== currentId);
    target = choices[Math.floor(Math.random() * choices.length)] || tracks[0];
  } else {
    const response = await fetch(`/next/${currentId}`);
    if (!response.ok) return;
    const data = await response.json();
    target = tracks.find(t => Number(t.dataset.id) === data.id);
  }
  if (target) {
    const button = target.querySelector(".play-track");
    playSong(button.dataset.id, button.dataset.title);
  }
}
document.getElementById("next").addEventListener("click", playNext);
document.getElementById("previous").addEventListener("click", () => {
  audio.currentTime = 0;
  if (audio.src) audio.play();
});
document.getElementById("repeat").addEventListener("click", event => {
  repeatOne = !repeatOne;
  event.currentTarget.classList.toggle("active", repeatOne);
});
document.getElementById("shuffle").addEventListener("click", event => {
  shuffleMode = !shuffleMode;
  event.currentTarget.classList.toggle("active", shuffleMode);
});

// Reordenamiento mediante arrastrar y soltar
let dragged = null;
function refreshNumbers() {
  [...list.querySelectorAll(".track")].forEach((track, index) => {
    track.querySelector(".track-number").textContent = index + 1;
  });
}
list?.querySelectorAll(".track").forEach(track => {
  track.addEventListener("dragstart", () => { dragged = track; track.classList.add("dragging"); });
  track.addEventListener("dragend", async () => {
    track.classList.remove("dragging");
    dragged = null;
    refreshNumbers();
    const song_ids = [...list.querySelectorAll(".track")].map(item => Number(item.dataset.id));
    const response = await fetch("/reorder", {
      method: "POST", headers: {"Content-Type":"application/json"},
      body: JSON.stringify({song_ids})
    });
    if (!response.ok) alert("No se pudo guardar el nuevo orden.");
  });
  track.addEventListener("dragover", event => {
    event.preventDefault();
    if (!dragged || dragged === track) return;
    const rect = track.getBoundingClientRect();
    const after = event.clientY > rect.top + rect.height / 2;
    list.insertBefore(dragged, after ? track.nextSibling : track);
  });
});

// Enviar el formulario al seleccionar un MP3
document.querySelector('.upload-form input[type="file"]')?.addEventListener("change", event => {
  if (event.target.files.length) event.target.form.submit();
});
