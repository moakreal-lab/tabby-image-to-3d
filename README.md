# tabby-image-to-3d

Lightweight **image → 3D mesh** service that runs locally and can be called with `curl`.

It uses a compact depth-estimation model (`Intel/dpt-hybrid-midas`) and reconstructs a triangle mesh with controls for:
- polygon/triangle count (`target_faces`)
- depth exaggeration (`depth_scale`)
- texture on/off (`textured`)

## Why this is lightweight + fast
- Single depth model loaded once in memory.
- Mesh decimation by grid resampling to match your face budget.
- Local FastAPI server for low-overhead inference.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run locally (API)

```bash
PYTHONPATH=src uvicorn app:app --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

## `curl` usage

### Textured GLB output

```bash
curl -X POST "http://localhost:8000/image-to-3d" \
  -F "image=@./input.jpg" \
  -F "target_faces=30000" \
  -F "depth_scale=1.2" \
  -F "textured=true" \
  --output mesh.glb
```

### No texture (PLY output)

```bash
curl -X POST "http://localhost:8000/image-to-3d" \
  -F "image=@./input.jpg" \
  -F "target_faces=12000" \
  -F "depth_scale=0.8" \
  -F "textured=false" \
  --output mesh.ply
```

## CLI usage

```bash
PYTHONPATH=src python src/app.py --input input.jpg --output mesh.glb --textured --target-faces 25000
```

## API parameters

`POST /image-to-3d` multipart form:
- `image` (file, required): input image.
- `target_faces` (int, default `25000`): target number of triangles.
- `depth_scale` (float, default `1.0`): depth intensity multiplier.
- `textured` (bool, default `true`):
  - `true` → textured `.glb`
  - `false` → `.ply` without texture

## Notes for quality
- Higher `target_faces` improves detail but costs speed/memory.
- `depth_scale` around `0.8-1.4` is usually stable.
- Accuracy depends on depth-model quality and image content.

## Run tests

```bash
pytest -q
```
