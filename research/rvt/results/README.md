# Evidence provenance

`core2024-pages.json` is produced by `pages.py` from the SHA-256-pinned
MIT corpus sample specified in the handoff. It includes Formats/Latest,
which adds two pages to the original probe's 507-page set. Raw fixture and
page exports are in ignored `../local/`, outside temporary scratch storage.

The 509 payload vectors are linearly independent. Therefore every possible
assignment of their trailers fits some linear map; this sample supplies no
constraints with which to establish or refute general GF(2) linearity.
