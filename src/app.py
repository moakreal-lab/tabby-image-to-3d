from __future__ import annotations

import argparse
import logging
import os
import time
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from src.image_to_3d import DepthEstimator, MeshOptions, image_bytes_to_mesh

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("tabby-image-to-3d")

app = FastAPI(title="Lightweight Image to 3D", version="0.2.0")
_estimator: DepthEstimator | None = None


def get_estimator() -> DepthEstimator:
    global _estimator
    if _estimator is None:
        logger.info("Loading depth estimation model...")
        _estimator = DepthEstimator()
        logger.info("Depth model loaded")
    return _estimator


@app.middleware("http")
async def log_requests(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info("%s %s -> %s (%.2fms)", request.method, request.url.path, response.status_code, duration_ms)
    return response


@app.get("/health")
def health() -> dict:
    return {"ok": True, "model_loaded": _estimator is not None}


@app.post("/image-to-3d")
async def image_to_3d(
    image: UploadFile = File(...),
    target_faces: int = Form(25000),
    depth_scale: float = Form(1.0),
    textured: bool = Form(True),
):
    if target_faces < 100:
        raise HTTPException(status_code=400, detail="target_faces must be >= 100")
    if depth_scale <= 0:
        raise HTTPException(status_code=400, detail="depth_scale must be > 0")

    options = MeshOptions(target_faces=target_faces, depth_scale=depth_scale, textured=textured)
    payload = await image.read()
    out_path, media_type = image_bytes_to_mesh(payload, options=options, estimator=get_estimator())
    return FileResponse(path=out_path, media_type=media_type, filename=out_path.name)


def run_cli() -> None:
    parser = argparse.ArgumentParser(description="Convert 2D image to 3D mesh")
    parser.add_argument("--input", required=True, help="Input image path")
    parser.add_argument("--output", required=True, help="Output mesh path (.glb or .ply)")
    parser.add_argument("--target-faces", type=int, default=25000)
    parser.add_argument("--depth-scale", type=float, default=1.0)
    parser.add_argument("--textured", action="store_true", help="Enable textures")
    parser.add_argument("--model", default="Intel/dpt-hybrid-midas", help="HF depth-estimation model")
    args = parser.parse_args()

    local_estimator = DepthEstimator(model_name=args.model)
    options = MeshOptions(target_faces=args.target_faces, depth_scale=args.depth_scale, textured=args.textured)
    out_path, _ = image_bytes_to_mesh(Path(args.input).read_bytes(), options=options, estimator=local_estimator)
    Path(args.output).write_bytes(Path(out_path).read_bytes())
    print(f"Wrote mesh: {args.output}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("src.app:app", host="0.0.0.0", port=port, reload=False)
