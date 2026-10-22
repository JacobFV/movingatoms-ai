# Moving Atoms processing worker

Claims jobs from the site's worker API (`/app/api/worker/*`, bearer `WORKER_TOKEN`) and runs them:

| Job | Module | What it does |
|---|---|---|
| `ingest` | `ma_proc/ingest/job.py` | a scan file in R2 → decoded, measured, labelled, Potree layers, overview pictures, `ready` |
| `link_import` | `ma_proc/ingest/link_import.py` | a scan from a link → stored in R2 as the project's source → ingested |
| `model_fit`, `build`, `heatmap` | `ma_proc/model/` | fit to scan, model builds (GLB/IFC), scan-to-model heatmaps |

## Run

```sh
uv sync                                         # pye57 needs Xerces-C headers (apt: libxerces-c-dev) on aarch64
WORKER_TOKEN=… uv run python -m ma_proc.runner  # loop; --once for one job; --types ingest,link_import
```

or the image (builds natively for linux/arm64 and linux/amd64; see the Dockerfile header for how it cross-builds):

```sh
docker build -t ma-proc processing                          # this machine
docker build --platform linux/amd64 -t ma-proc processing   # e.g. for Cloudflare Containers from an arm64 host
docker run --rm -e WORKER_TOKEN=… -e MA_WORKER_NAME=$(hostname) -v /var/lib/movingatoms:/work ma-proc
```

The image runs as **uid 10001**: a host directory mounted at `/work` must be writable by it
(`chown 10001:10001 /var/lib/movingatoms`).

| Env | Default | |
|---|---|---|
| `WORKER_TOKEN` | — | required |
| `MA_SITE` | `https://movingatoms-ai.pages.dev` | |
| `MA_WORKER_NAME` | hostname | shown on claimed jobs |
| `MA_WORK_DIR` | temp dir (`/work` in the image) | each job gets its own directory, removed afterwards |
| `MA_MAX_SOURCE_BYTES` | unlimited | claim only ingest jobs whose source is at most this big (the claim's `max_size`); bigger ones are left for a bigger machine |
| `POTREE_CONVERTER` | `PotreeConverter` on PATH | must be an absolute path (PotreeConverter resolves itself from argv[0]) |
| `MA_LOG` | `json` | or `text` |

A heartbeat touches the job every 45 s (claims lapse after 15 min). SIGTERM/SIGINT release the job in hand back to
the queue (`POST /worker/jobs/:id/release`) instead of failing it. A failed ingest marks its scan `error` with a
message the customer can act on.

## Ingest

`inspecting → decoding → labelling → converting → overview → ready`, each reported to the scan
(`status`, `progress`, `stage_detail`) and the job.

- **Formats:** E57 (every scan position, posed, read in 2M-point chunks through libE57), LAS/LAZ, PLY (incl.
  Gaussian-splat PLY: colour from `f_dc_*`), PTS/PTX/XYZ/TXT/CSV, PCD (ASCII/binary), meshes (GLB/glTF/OBJ/STL…,
  surface-sampled), ZIPs of any of these. ReCap RCP/RCS are refused with "export as E57".
- **Memory:** points stream onto disk (`store.py`: memmapped float64 xyz, uint16 rgb/intensity, uint8 labels);
  analysis runs on an even ~2M-point voxel sample. A 27.8M-point single-station E57 measures and labels in ~20 s
  with a 3.4 GB peak.
- **Measurement** (`measure.py`): working frame (Y-up files turned Z-up; offset in whole metres so coordinates sit
  near the origin), bounds, floor/ceiling levels (peaks in the heights of horizontal surfaces; a floor has things
  above it, a ceiling below), footprint (occupied 25 cm cells), median point spacing → the scan's `brief`, which
  the estimate prices from.
- **Labels** (`classify.py`, scheme ma-v1, codes as in the app's `LABELS`): geometric classification on k-NN
  eigen-features — local statistical noise; floors and ceilings at their levels, grown across ramps and uneven slabs;
  walls as tall, long vertical planes grouped by facing direction and voxel connectivity; pipes by cylinder detection
  (axis = the direction the surface normals don't vary in, RANSAC circle, normals that face the centre and sweep
  round it, a run several diameters long); round columns (thick vertical floor-to-ceiling cylinders); ducts (box
  sections overhead); beams, railings, stairs (regular treads stepping one way), equipment vs furniture/clutter by
  size; outside = beyond the filled floor/ceiling footprint; then a k-NN majority vote. Every point takes its nearest
  sampled neighbour's label. No learned model: Open3D-ML's pretrained segmentation models need Open3D's PyTorch ops,
  which aren't built for aarch64.
- **Layers** (`potree.py`): LAS 1.4 (point format 7, classification = label) → PotreeConverter 2.1.1, uncompressed
  (`encoding: DEFAULT`), attributes `classification`, `rgb`, `intensity`:
  `projects/<pid>/scans/<scan>/potree-overview/` (≤ 2M points, uploaded first so the scan opens early) and
  `…/potree/` (every point), plus `…/labelled.las` (every point with its label, for the model jobs).
- **Pictures** (`render.py`): `…/overview-top.png` (under the ceiling) and `…/overview-iso_ne.png`, registered as
  project files (the projects page shows them on the card).

## Tests

```sh
uv run pytest -q    # needs PotreeConverter (or POTREE_CONVERTER=/abs/path) for the pipeline tests
```
