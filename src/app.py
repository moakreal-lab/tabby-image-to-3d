from __future__ import annotations

import argparse
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse

from src.image_to_3d import DepthEstimator, MeshOptions, image_bytes_to_mesh

app = FastAPI(title="Lightweight Image to 3D", version="0.1.0")
estimator = DepthEstimator()


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/image-to-3d")
async def image_to_3d(
    image: UploadFile = File(...),
    target_faces: int = Form(25000),
    depth_scale: float = Form(1.0),
    textured: bool = Form(True),
):
    options = MeshOptions(target_faces=target_faces, depth_scale=depth_scale, textured=textured)
    out_path, media_type = image_bytes_to_mesh(await image.read(), options=options, estimator=estimator)
    return FileResponse(
        path=out_path,
        media_type=media_type,
        filename=out_path.name,
    )


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
    options = MeshOptions(
        target_faces=args.target_faces,
        depth_scale=args.depth_scale,
        textured=args.textured,
    )

    out_path, _ = image_bytes_to_mesh(Path(args.input).read_bytes(), options=options, estimator=local_estimator)
    Path(args.output).write_bytes(Path(out_path).read_bytes())
    print(f"Wrote mesh: {args.output}")


if __name__ == "__main__":
    uvicorn.run("src.app:app", host="0.0.0.0", port=8000, reload=False)
