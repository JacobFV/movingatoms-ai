"""Local shape of every point in a sample: the eigen-features of its k nearest neighbours (PCA), the standard
descriptors for point-cloud classification (Weinmann et al. 2015): normal, linearity, planarity, scattering,
verticality, and the mean neighbour distance used for outlier removal."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree


@dataclass
class Features:
    xyz: np.ndarray  # (N,3) working frame
    tree: cKDTree
    normal: np.ndarray  # (N,3) unit, z >= 0 (sign is ambiguous for a surface)
    linearity: np.ndarray
    planarity: np.ndarray
    scattering: np.ndarray
    knn_dist: np.ndarray  # mean distance to the k neighbours
    spacing: np.ndarray  # distance to the nearest neighbour

    @property
    def nz(self) -> np.ndarray:
        return np.abs(self.normal[:, 2])


def compute(xyz: np.ndarray, k: int = 16, batch: int = 400_000) -> Features:
    xyz = np.ascontiguousarray(xyz, dtype=np.float64)
    n = len(xyz)
    tree = cKDTree(xyz, leafsize=32, balanced_tree=False, compact_nodes=False)
    normal = np.zeros((n, 3))
    lin = np.zeros(n)
    pla = np.zeros(n)
    sca = np.zeros(n)
    kd = np.zeros(n)
    sp = np.zeros(n)
    kk = min(k, max(2, n - 1))
    for s in range(0, n, batch):
        e = min(n, s + batch)
        d, idx = tree.query(xyz[s:e], k=kk + 1, workers=-1)
        d, idx = d[:, 1:], idx[:, 1:]
        kd[s:e] = d.mean(axis=1)
        sp[s:e] = d[:, 0]
        nb = xyz[idx]  # (b,k,3)
        nb = nb - nb.mean(axis=1, keepdims=True)
        cov = np.einsum("bki,bkj->bij", nb, nb) / kk
        w, v = np.linalg.eigh(cov)  # ascending
        w = np.maximum(w, 1e-12)
        l3, l2, l1 = w[:, 0], w[:, 1], w[:, 2]
        lin[s:e] = (l1 - l2) / l1
        pla[s:e] = (l2 - l3) / l1
        sca[s:e] = l3 / l1
        nrm = v[:, :, 0]
        nrm *= np.where(nrm[:, 2:3] < 0, -1.0, 1.0)
        normal[s:e] = nrm
    return Features(xyz, tree, normal, lin, pla, sca, kd, sp)
