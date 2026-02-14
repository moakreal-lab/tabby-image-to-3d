# tabby-image-to-3d

Convert an image into a 3D mesh with control over:
- triangle count (`target_faces`)
- depth strength (`depth_scale`)
- textured output or geometry-only output (`textured`)

Outputs:
- `textured=true` -> `.glb`
- `textured=false` -> `.ply`

---

## 1) Quick local run (Windows fix included)

Your error happened because `source` is Linux/macOS only.

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

---

## 2) Curl usage

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

---

## 3) Run globally (public URL) with Docker deploy

If you want to `curl` without running your own local server each time, deploy once to a cloud host.

This repo includes a `Dockerfile`, so you can deploy to services like Railway, Render, Fly.io, etc.

### Example (Railway)
1. Push this repo to GitHub.
2. In Railway: **New Project -> Deploy from GitHub Repo**.
3. Railway builds from `Dockerfile` automatically.
4. After deploy, use your public domain:

```bash
curl https://YOUR_PUBLIC_DOMAIN/image-to-3d \
  -F "image=@./input.jpg" \
  -F "target_faces=20000" \
  -F "depth_scale=1.0" \
  -F "textured=true" \
  --output mesh.glb
```

---

## API

`POST /image-to-3d` form-data:
- `image` (file, required)
- `target_faces` (int, default `25000`)
- `depth_scale` (float, default `1.0`)
- `textured` (bool, default `true`)

`GET /health` -> `{ "ok": true }`

---

## CLI

```bash
python src/app.py --input input.jpg --output mesh.glb --textured --target-faces 25000
```

---

## Tests

```bash
pytest -q
```
