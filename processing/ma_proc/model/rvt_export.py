"""Offline experimental RVT export through a verified, separately built runtime.

This command does not enable native RVT delivery in customer build jobs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from .geometry import Model, all_parts
from .rvt_request import to_seed_model_request


def export_experimental(read: dict, bundle: Path, output: Path, *, load_mesh=None,
                        acknowledge_hypotheses: bool = False,
                        runtime_python: str = sys.executable) -> dict:
    if not acknowledge_hypotheses:
        raise ValueError("experimental native lifecycle hypotheses must be acknowledged")
    bundle, output = Path(bundle).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    launcher = bundle / "run.py"
    if not launcher.is_file():
        raise ValueError("verified runtime bundle run.py is missing")
    request = to_seed_model_request(read, all_parts(Model(read), load_mesh))
    with tempfile.TemporaryDirectory(prefix="ma-rvt-request-") as temporary:
        request_path = Path(temporary) / "request.json"
        request_path.write_text(json.dumps(request, ensure_ascii=False, allow_nan=False), encoding="utf-8")
        # The runtime validates its complete payload manifest before loading any
        # authoring modules and publishes only after independent saved-file audits.
        subprocess.run([runtime_python, str(launcher), "--request", str(request_path),
                        "--output", str(output), "--acknowledge-hypotheses"], check=True)
    report = json.loads((output / "run.json").read_bytes())
    candidate = output / "verified-candidate.rvt"
    if report.get("status") != "verified_research_candidate":
        raise ValueError("runtime did not finish independent research verification")
    actual_sha = hashlib.sha256(candidate.read_bytes()).hexdigest()
    if actual_sha != report.get("candidate_sha256"):
        raise ValueError("published candidate hash differs from verification report")
    if report.get("production_native_export") is not False:
        raise ValueError("runtime qualification differs from experimental contract")
    return {"candidate": str(candidate), "candidate_sha256": actual_sha,
            "report": str(output / "run.json"), "autodesk_acceptance": "not_tested",
            "production_native_export": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path, help="saved model-read JSON")
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mesh-directory", type=Path, help="local content-addressed SHA256.glb assets")
    parser.add_argument("--runtime-python", default=sys.executable)
    parser.add_argument("--acknowledge-hypotheses", action="store_true")
    args = parser.parse_args()

    def load_mesh(sha):
        if args.mesh_directory is None or not isinstance(sha, str) or re.fullmatch(r"[0-9a-f]{64}", sha) is None:
            raise ValueError("mesh asset requires a SHA256 and explicit local mesh directory")
        data = (args.mesh_directory / (sha + ".glb")).read_bytes()
        if hashlib.sha256(data).hexdigest() != sha:
            raise ValueError("mesh asset content hash differs")
        from .glb import read_glb_parts
        return read_glb_parts(data)

    result = export_experimental(json.loads(args.model.read_bytes()), args.bundle, args.output,
                                 load_mesh=load_mesh, runtime_python=args.runtime_python,
                                 acknowledge_hypotheses=args.acknowledge_hypotheses)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
