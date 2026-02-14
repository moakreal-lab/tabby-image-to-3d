from __future__ import annotations

import io
import math
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import trimesh
from PIL import Image
from transformers import pipeline


@dataclass
class MeshOptions:
    target_faces: int = 25000
    depth_scale: float = 1.0
    textured: bool = True


class DepthEstimator:
    """Lightweight depth model wrapper loaded once per process."""

    def __init__(self, model_name: str = "Intel/dpt-hybrid-midas") -> None:
        self._pipe = pipeline(task="depth-estimation", model=model_name)

    def estimate(self, image: Image.Image) -> np.ndarray:
        result = self._pipe(image)
        depth = np.array(result["depth"], dtype=np.float32)
        depth -= depth.min()
        denom = max(depth.max(), 1e-6)
        depth /= denom
        return depth


def _grid_stride_for_target(height: int, width: int, target_faces: int) -> int:
    total_faces = 2 * max(height - 1, 1) * max(width - 1, 1)
    if target_faces <= 0:
        return 1
    return max(1, int(math.ceil(math.sqrt(total_faces / target_faces))))


def _resample_for_faces(depth: np.ndarray, image: Image.Image, target_faces: int) -> Tuple[np.ndarray, Image.Image]:
    h, w = depth.shape
    stride = _grid_stride_for_target(h, w, target_faces)
    if stride == 1:
        return depth, image

    target_w = max(2, w // stride)
    target_h = max(2, h // stride)
    res_depth = np.array(
        Image.fromarray(depth).resize((target_w, target_h), Image.Resampling.BILINEAR),
        dtype=np.float32,
    )
    res_image = image.resize((target_w, target_h), Image.Resampling.BICUBIC)
    return res_depth, res_image


def mesh_from_depth(depth: np.ndarray, texture: Optional[Image.Image], options: MeshOptions) -> trimesh.Trimesh:
    depth, texture = _resample_for_faces(depth, texture if texture else Image.new("RGB", (depth.shape[1], depth.shape[0])), options.target_faces)

    h, w = depth.shape
    y, x = np.mgrid[0:h, 0:w]

    x_norm = (x / max(w - 1, 1)) * 2.0 - 1.0
    y_norm = -((y / max(h - 1, 1)) * 2.0 - 1.0)
    z = (1.0 - depth) * options.depth_scale

    vertices = np.stack([x_norm, y_norm, z], axis=-1).reshape(-1, 3)

    faces = []
    for j in range(h - 1):
        row = j * w
        next_row = (j + 1) * w
        for i in range(w - 1):
            a = row + i
            b = row + i + 1
            c = next_row + i
            d = next_row + i + 1
            faces.append([a, c, b])
            faces.append([b, c, d])
    faces_np = np.asarray(faces, dtype=np.int64)

    if options.textured and texture is not None:
        uv = np.stack([
            x.reshape(-1) / max(w - 1, 1),
            1.0 - (y.reshape(-1) / max(h - 1, 1)),
        ], axis=-1)
        material = trimesh.visual.material.SimpleMaterial(image=texture)
        visual = trimesh.visual.texture.TextureVisuals(uv=uv, material=material)
        return trimesh.Trimesh(vertices=vertices, faces=faces_np, visual=visual, process=False)

    return trimesh.Trimesh(vertices=vertices, faces=faces_np, process=False)


def image_bytes_to_mesh(
    image_bytes: bytes,
    options: MeshOptions,
    estimator: Optional[DepthEstimator] = None,
) -> Tuple[Path, str]:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    estimator = estimator or DepthEstimator()
    depth = estimator.estimate(image)
    mesh = mesh_from_depth(depth, image, options)

    tmpdir = Path(tempfile.mkdtemp(prefix="image-to-3d-"))
    if options.textured:
        out_path = tmpdir / "mesh.glb"
        mesh.export(out_path)
        return out_path, "model/gltf-binary"

    out_path = tmpdir / "mesh.ply"
    mesh.export(out_path)
    return out_path, "application/octet-stream"
