# Image Compressor

Compress images to a specific file size or percentage of their original size, right in the browser. Also supports flipping and rotating before compression. Built as a FastAPI backend + vanilla JS frontend, served together as one app.

**Live:** https://image-compressor-7px2.onrender.com/
*(Free-tier hosting — first load after inactivity can take 30-60s while the server spins up.)*

## Features

- **Target size (KB)** — compress down to a specific file size
- **Target percent** — compress down to a percentage of the original file size
  *(exactly one of the two, not both)*
- **Flip** — horizontal or vertical
- **Rotate** — right 90°, left 90°, or 180°
- **Output format** — JPEG or WebP, your choice

## How compression works

Rather than guessing a fixed quality setting, the backend binary-searches JPEG/WebP's `quality` parameter (0–100), re-encoding the image at each trial and checking the resulting byte size, converging on the highest quality that still fits the target. If even the lowest usable quality doesn't hit the target, it falls back to progressively downscaling the image's resolution.

## Tech stack

- **Backend:** FastAPI, Pillow (image processing)
- **Frontend:** Plain HTML/CSS/JS — no framework
- Frontend is served directly by FastAPI (`StaticFiles`), so it's one deployed service, not two.

## Project structure

```
Image-Compressor/
├── Backend/
│   ├── main.py          # FastAPI app, /compress route, serves Frontend/
│   ├── processor.py     # compression, flip, rotate logic
│   └── requirements.txt
└── Frontend/
    ├── index.html
    ├── style.css
    └── script.js
```

## Running locally

```
cd Backend
python -m venv venv

# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/` — the same server handles both the page and the `/compress` API. Interactive API docs are at `http://127.0.0.1:8000/docs`.