# tabby-image-to-3d

Convert an image into a 3D mesh with control over:
- triangle count (`target_faces`)
- depth strength (`depth_scale`)
- textured output or geometry-only output (`textured`)

Outputs:
- `textured=true` -> `.glb`
- `textured=false` -> `.ply`

## Quick local run

### Windows (CMD)
```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.app:app --host 0.0.0.0 --port 8000
```

### Windows (PowerShell)
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn src.app:app --host 0.0.0.0 --port 8000
```

### Linux/macOS
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.app:app --host 0.0.0.0 --port 8000
```

Health check:
```bash
curl http://localhost:8000/health
```

## Curl usage

If your host (like Railway) tracks `main`, push your latest code to `main` first:

```bash
git checkout main || git checkout -b main
git merge --ff-only work
git push -u origin main
```

### Textured GLB
```bash
curl -X POST "http://localhost:8000/image-to-3d" \
  -F "image=@./input.jpg" \
  -F "target_faces=30000" \
  -F "depth_scale=1.2" \
  -F "textured=true" \
  --output mesh.glb
```

### No texture (PLY)
```bash
curl -X POST "http://localhost:8000/image-to-3d" \
  -F "image=@./input.jpg" \
  -F "target_faces=12000" \
  -F "depth_scale=0.8" \
  -F "textured=false" \
  --output mesh.ply
```

## API

`POST /image-to-3d` form-data:
- `image` (file, required)
- `target_faces` (int, default `25000`)
- `depth_scale` (float, default `1.0`)
- `textured` (bool, default `true`)

`GET /health` -> `{ "ok": true, "model_loaded": true|false }`
