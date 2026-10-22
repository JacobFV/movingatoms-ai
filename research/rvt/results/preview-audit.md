# Native source preview framing and visual changes

All 11 licensed source files contain one embedded PNG in `RevitPreview4.0`.
The audit verifies every PNG chunk CRC, the wrapper's image-length word, exact
image termination and wrapper/PNG pixel dimensions. PNG bytes are extracted
unchanged; decoded RGBA pixels are hashed only for comparison. These are
**original source thumbnails**, not previews rendered from an experimental
writer output and not Autodesk acceptance evidence.

Observed framing:

| Fixtures | PNG starts at byte | Bytes after PNG |
| --- | ---: | ---: |
| Original Core Interior and Einhoven | 302 | 40 |
| Four RE1 fixtures | 235 | 40 |
| Five historical Core Interior fixtures | 386 | 40 |

A little-endian u32 immediately before the PNG equals its complete byte length.
The prefix contains length-prefixed embedded field declarations in this order:
`m_compressedImage` (descriptor `0x5002`), `m_dpiX`, `m_dpiY`,
`m_widthInFeet`, `m_heightInFeet` (descriptor 7), and `m_width`, `m_height`
(descriptor 4). Their offsets are reported per source. The 40-byte suffix fits
four little-endian doubles followed by two signed i32 dimensions in that order.
The dimensions independently match the PNG's **128 × 128** pixels in every file.
The audit does not claim to decode the entire prefix or all wrapper variants.

Wrapper DPI is 72 for Core Interior, 143.9926 for Einhoven and 95.9866 for RE1;
width/height-in-feet fields are zero throughout. PNG physical-resolution
metadata is not always bitwise equivalent: Pillow reports 71.9836 for historical
Core PNGs with `pHYs`, 143.9672 for Einhoven, and 95.9866 for RE1. Do not force
wrapper and PNG DPI equality. Chunk inventory and decoded DPI/gamma/sRGB
metadata are recorded without treating their changes as model geometry changes.

## Historical comparisons

All five Git-adjacent historical comparisons have **different decoded RGBA
pixels**, different PNG bytes and different full preview streams. Thus none of
these pairs supplies an example of a preview revision advancing with an
identical image. This does not establish that such an unchanged-image save is
impossible.

The prefix excluding the image-length word is byte-identical across the first
four pairs; it changes in the last pair. The suffix is byte-identical across
all five. Preview revisions advance 47 → 50 → 52 → 58 → 60 → 65 while the
image changes. Existing history evidence shows these Git snapshots can span
multiple saves and operations; they do not isolate a single rendering rule.

All 11 pixel hashes are distinct. Historical Core PNG metadata changes from
`pHYs` to sRGB/gamma/chromaticity chunks near the end of the series, but the
pixel comparison establishes that the images also change, not only metadata.

## Known-value searches and candidate consequence

The prefix and suffix were searched only for known History GUID bytes,
nonzero stream revisions, episode/increment counts and latest-increment low
32-bit timestamps. No tested GUID or timestamp byte sequence occurs in those
wrapper regions. Some small integers match schema/string-length or other
wrapper bytes; all offsets are recorded explicitly as **byte coincidences**,
not semantic bindings. Zero-valued revisions are excluded as uninformative.
No field is patched based on a value match.

The candidate currently preserves its original preview bytes and preview
revision. That remains an explicit limitation: the thumbnail has not been
regenerated from edited geometry or material appearance. This audit provides
safe extraction and evidence, not a thumbnail renderer or a rule establishing
when Revit requires a new image.

## Reproduce and capture

```sh
python3 research/rvt/preview_audit.py \
  research/rvt/local research/rvt/results/paired-save-sources.json \
  --extract-dir research/rvt/local/preview-images \
  > research/rvt/results/preview-audit.json
PYTHONPATH=research/rvt python3 -m unittest research/rvt/test_preview_audit.py -v
```

The JSON binds each extracted filename to the source fixture SHA-256, complete
preview-stream hash, PNG offset/length/hash and decoded pixel hash. Extracted
images under ignored local storage are exact source bytes. A browser contact
sheet can use these PNGs directly and be captured as a screenshot; captions
must identify source fixtures and state that these are original thumbnails.
No image generation, repainting or image-editing step is needed.

Two tests cover byte-exact PNG extraction and rejection of bad CRCs, bad image
lengths, mismatched dimensions, wrong embedded descriptors and invalid ending
sizes. No RVT is modified by this audit.
