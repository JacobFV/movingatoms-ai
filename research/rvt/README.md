# Revit (.rvt) research scripts

See [docs/rvt-research.md](../../docs/rvt-research.md). Run with `uv run --with olefile --with xxhash --with crcmod python <script> <file.rvt>`.

- `rvtinspect.py` — list a file's OLE streams and print BasicFileInfo.
- `tail_probe.py` — split paged streams into 64,896 + 353-byte pages; entropy, constant bytes, digest search, duplicate-payload check.
- `tail_probe2.py` — more digests (xxhash, CRC variants, SHA-512, BLAKE2b) and stride-structure checks on one page's trailer.
- `hist_patch.py` — build an rvt-rs `rvt-write` patch manifest that edits the Global/History stream (the one semantic write that worked).
