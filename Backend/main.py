# backend/main.py

import os
from typing import Optional, Literal

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from processor import process_image

app = FastAPI()

# No longer strictly needed once frontend+backend share one origin, but
# harmless to leave — remove later if you want to trim dead config.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Final-Quality", "X-Final-Size-Bytes"],
)


@app.post("/compress")
async def compress(
    file: UploadFile = File(...),
    output_format: Literal["jpeg", "webp"] = Form(...),
    target_kb: Optional[int] = Form(None),
    target_percent: Optional[float] = Form(None),
    flip: Optional[Literal["horizontal", "vertical"]] = Form(None),
    rotate: Optional[Literal["right", "left", "180"]] = Form(None),
):
    if (target_kb is None) == (target_percent is None):
        raise HTTPException(
            400,
            "provide exactly one of target_kb or target_percent, not both or neither",
        )

    if target_kb is not None and target_kb <= 0:
        raise HTTPException(400, "target_kb must be positive")

    if target_percent is not None and not (0 < target_percent <= 100):
        raise HTTPException(400, "target_percent must be between 0 and 100")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(400, "empty file")

    if target_kb is not None:
        target_bytes = target_kb * 1024
    else:
        target_bytes = int(len(file_bytes) * (target_percent / 100))

    try:
        compressed_bytes, final_quality = process_image(
            file_bytes=file_bytes,
            output_format=output_format,
            target_bytes=target_bytes,
            flip=flip,
            rotate=rotate,
        )
    except Exception as e:
        raise HTTPException(400, f"could not process image: {e}")

    media_type = "image/jpeg" if output_format == "jpeg" else "image/webp"
    return Response(
        content=compressed_bytes,
        media_type=media_type,
        headers={
            "X-Final-Quality": str(final_quality),
            "X-Final-Size-Bytes": str(len(compressed_bytes)),
            "Content-Disposition": f'attachment; filename="compressed.{output_format}"',
        },
    )


# Absolute path, not "../frontend" directly — deployment platforms don't
# always launch uvicorn from inside backend/, so resolving relative to
# this file's own location (not the process's working directory) is what
# keeps this working regardless of where the start command runs from.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

# Must be the LAST thing registered — Starlette matches routes in
# registration order, and this mounts at "/" which would otherwise
# catch /compress requests before they reach the route above.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")