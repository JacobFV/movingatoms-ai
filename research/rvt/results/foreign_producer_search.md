# Search for a permissively licensed foreign-producer fixture

Research date: 2026-10-22. **No fixture met all three requirements in this
bounded search:** public access without an account, a permissive license
applicable to the model itself, and evidence that a third-party writer produced
its RVT bytes. No candidate was added to the licensed byte corpus, and no
foreign producer's SignatureMarker was decoded.

## Strongest producer evidence, but no qualified fixture

Safe Software's official tutorial, updated 2025-05-20, demonstrates an
FME-generated RVT opening in Revit 2023 after an origin warning. It provides
a workspace attachment containing `Architectural_Blank.rte`, which is input
to the writer; the source project is an Autodesk sample. The page does not
establish that this included template itself was written by FME, nor an
applicable permissive model license. Its Autodesk-content attribution is
noncommercial. Thus it is useful producer/acceptance documentation, not a
qualified foreign-output fixture.
[Safe Software tutorial](https://support.safe.com/hc/en-us/articles/25407471567757-Revit-Writing-in-FME-Form).

Safe's general legal page contains separate provisions for website materials,
user submissions, software sample data, and attributed open data. A clause
about user-submitted content does not establish the license or provenance of
this particular template. No executable or workspace was run, and no account
was created. [Safe Software legal page](https://www.safe.com/legal/).

## Explicit sample-license lead without native sample bytes

The DDC converter repository identifies sample content separately from its
proprietary converters. However, its stated workflow reads RVT and emits other
formats, so an RVT found there would still require writer-provenance evidence.
At inspected revision `0ec89e3fabaa272b41824eb31006ac3312ae2fd3`, the complete
GitHub tree contains 4,604 entries and zero `.rvt`, `.rfa`, or `.rte` paths.
The API reports no truncation. No proprietary converter was downloaded,
executed, or inspected.
[Repository](https://github.com/datadrivenconstruction/cad2data-Revit-IFC-DWG),
[pinned tree API](https://api.github.com/repos/datadrivenconstruction/cad2data-Revit-IFC-DWG/git/trees/0ec89e3fabaa272b41824eb31006ac3312ae2fd3?recursive=1).

## ODA material

ODA's public documentation describes RVT/RFA examples as part of SDK archives,
and its FAQ says new models start from templates. Those statements provide
neither a public permissive license for a specific output file nor an
identified foreign-produced downloadable RVT. SDK source/binaries and
account-gated archives were not inspected.
[ODA format/archive FAQ](https://www.opendesign.com/faq/question/how-work-different-file-formats-example-dwg-dgn-rvt-rfa-nwd-nwc-and-others-visualize),
[ODA BimRv FAQ](https://www.opendesign.com/faq/bimrv).

## Result and useful next input

The search does not establish that no suitable sample exists. It records why
these leads were excluded and prevents treating an input model, a marketing
claim, or a repository-level license as foreign-output provenance. The useful
next input would be an explicitly licensed, published tiny RVT written by
FME, ODA, Archicad, or another independent writer, with the author identifying
the writer/version and retaining any producer notices. That would allow the
existing strict page and partition probes to compare actual foreign framing.

Machine-readable search terms, URLs, eligibility checks and negative result
are in [foreign_producer_search.json](foreign_producer_search.json).
