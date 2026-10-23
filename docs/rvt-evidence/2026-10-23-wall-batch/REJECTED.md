# Rejected plot capture

Visual inspection found clipped second and third meshes. Matplotlib normalized the
shared aspect array in place, inadvertently changing subsequent panel bounds. The
underlying mesh arrays and validation reports are unchanged. The renderer now passes
an independent copy of the aspect array to each panel. Use the corrected capture in
`../2026-10-23-wall-batch-corrected/`; this directory preserves the original evidence
and original manifest hashes. This note was added after the original capture.
