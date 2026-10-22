"""A scan's points on disk: xyz (float64), rgb (uint16x3), intensity (uint16) and labels (uint8) as flat files,
appended chunk by chunk and read back as memmaps, so a 200 GB scan never has to fit in memory."""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

import numpy as np


class PointStore:
    def __init__(self, root: Path):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)
        self.n = 0
        self.has_rgb = False
        self.has_intensity = False
        self._f = {k: open(root / f"{k}.bin", "wb") for k in ("xyz", "rgb", "intensity")}
        self._rgb_seen = 0
        self._int_seen = 0

    # ---------- writing ----------
    def append(self, chunk: dict) -> int:
        xyz = np.ascontiguousarray(chunk["xyz"], dtype=np.float64)
        ok = np.isfinite(xyz).all(axis=1)
        if not ok.all():
            xyz = xyz[ok]
        n = len(xyz)
        if not n:
            return 0
        rgb = chunk.get("rgb")
        inten = chunk.get("intensity")
        if rgb is not None:
            rgb = np.asarray(rgb, dtype=np.uint16)[ok] if not ok.all() else np.asarray(rgb, dtype=np.uint16)
            self._rgb_seen += n
        else:
            rgb = np.zeros((n, 3), np.uint16)
        if inten is not None:
            inten = np.asarray(inten, dtype=np.uint16)[ok] if not ok.all() else np.asarray(inten, dtype=np.uint16)
            self._int_seen += n
        else:
            inten = np.zeros(n, np.uint16)
        self._f["xyz"].write(xyz.tobytes())
        self._f["rgb"].write(np.ascontiguousarray(rgb).tobytes())
        self._f["intensity"].write(np.ascontiguousarray(inten).tobytes())
        self.n += n
        return n

    def close(self) -> None:
        for f in self._f.values():
            f.close()
        # a file counts as coloured when most of its points came with colour
        self.has_rgb = self._rgb_seen > 0.5 * max(1, self.n)
        self.has_intensity = self._int_seen > 0.5 * max(1, self.n)
        self.labels = np.lib.format.open_memmap(self.root / "labels.npy", mode="w+", dtype=np.uint8, shape=(max(1, self.n),))

    # ---------- reading ----------
    @property
    def xyz(self) -> np.memmap:
        return np.memmap(self.root / "xyz.bin", dtype=np.float64, mode="r", shape=(self.n, 3))

    @property
    def rgb(self) -> np.memmap:
        return np.memmap(self.root / "rgb.bin", dtype=np.uint16, mode="r", shape=(self.n, 3))

    @property
    def intensity(self) -> np.memmap:
        return np.memmap(self.root / "intensity.bin", dtype=np.uint16, mode="r", shape=(self.n,))

    def chunks(self, size: int = 4_000_000) -> Iterator[tuple[int, int]]:
        for s in range(0, self.n, size):
            yield s, min(self.n, s + size)

    def voxel_sample(self, k: int, seed: int = 7) -> tuple[np.ndarray, float]:
        """Indices of about k points spread evenly over the scanned surfaces: one point per voxel, the voxel size chosen
        so about k voxels are occupied. A scanner station puts most of its points near itself; a random sample would
        too, and distant surfaces would look like noise. Returns (sorted indices, voxel size)."""
        if self.n <= k:
            return np.arange(self.n), 0.0
        probe = np.asarray(self.xyz[self.sample(min(self.n, 400_000), seed)])
        v = 0.05
        occ = len(np.unique(np.floor(probe / v).astype(np.int64), axis=0))
        # occupied voxels of a surface scale with 1/v²; the probe undercounts (it's sparse), so aim a little finer
        v = float(np.clip(v * np.sqrt(occ / k) * 0.8, 0.004, 1.0))
        lo = np.floor(np.asarray(self.xyz[:1])[0] / v).astype(np.int64) - (1 << 20)
        best_keys = np.zeros(0, np.int64)
        best_idx = np.zeros(0, np.int64)
        xyz = self.xyz
        for s, e in self.chunks():
            q = np.floor(xyz[s:e] / v).astype(np.int64) - lo
            q = np.clip(q, 0, (1 << 21) - 1)
            key = (q[:, 0] << 42) | (q[:, 1] << 21) | q[:, 2]
            uk, first = np.unique(key, return_index=True)
            keys = np.concatenate([best_keys, uk])
            idx = np.concatenate([best_idx, first + s])
            uk2, first2 = np.unique(keys, return_index=True)
            best_keys, best_idx = uk2, idx[first2]
        if len(best_idx) > 1.6 * k:  # too fine after all: thin it evenly
            rng = np.random.default_rng(seed)
            best_idx = rng.choice(best_idx, size=int(1.6 * k), replace=False)
        return np.sort(best_idx), v

    def sample(self, k: int, seed: int = 7) -> np.ndarray:
        """Indices of up to k points, uniformly at random, sorted (so reads walk the files forward)."""
        if self.n <= k:
            return np.arange(self.n)
        rng = np.random.default_rng(seed)
        return np.sort(rng.choice(self.n, size=k, replace=False))
