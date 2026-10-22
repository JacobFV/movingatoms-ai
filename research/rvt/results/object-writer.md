# Variable-length object writing

`object_writer.py` packs whole and split object envelopes into bounded gzip
members. It handles both ID widths, all three sequences, counts, repeated
lengths and Adler-32. Edits require exact original records and preserve IDs,
untouched sequences, other content groups and existing signature fields.
It does not claim Autodesk's compression boundaries or regenerate signatures.

Repacking all six licensed fixtures preserves **736,332 records in 523 groups**,
including every body byte and ID. All rebuilt partition envelopes round-trip.
See `object-repacking.json`; reproduce with `verify_object_writer.py` and the
same six fixture paths used by `verify_element_tables.py`.

The real RE1 Architecture experiment changes room 348738's floor finish from
`Wood` to `Polished concrete`. Its body grows from 2,531 to 2,557 bytes. The
transactional Rust writer regenerates page framing and verifies every stream.
The independent pinned reader reports exactly one field change among 154
exported elements and exactly one IFC property change (excluding timestamps).

A stricter independent check decodes the entire owning object graph: all 11
objects and 10 pointer edges remain intact. Only the requested parameter value,
26-byte body growth and corresponding cursor offsets differ. Unlike exported
property comparisons, this checks the other serialized fields in that body.
See `resized-graph.json`, `resized-reader.json`, `resized-plan.json` and
`resized-writer.json`.

```sh
python3 research/rvt/resized_parameter_experiment.py \
  research/rvt/local/RE1-Architecture.rvt research/rvt/local/resized-finish
processing/rvt-native/target/release/ma-rvt-native patch \
  research/rvt/local/RE1-Architecture.rvt research/rvt/local/resized-finish.rvt \
  research/rvt/local/resized-finish/manifest.json
research/rvt/local/rvt-elements research/rvt/local/resized-finish.rvt \
  > research/rvt/local/resized-elements.json
research/rvt/local/rvt-ifc research/rvt/local/resized-finish.rvt \
  -o research/rvt/local/resized-finish.ifc
python3 research/rvt/verify_resized_parameter.py research/rvt/local
python3 research/rvt/object_graph_probe.py \
  --reader-source /path/to/pinned/rvt-rs --target research/rvt/local/schema-target \
  research/rvt/local/RE1-Architecture.rvt research/rvt/local/resized-finish.rvt \
  > research/rvt/local/resized-graphs.json
python3 research/rvt/verify_resized_graph.py research/rvt/local/resized-graphs.json
```

Use fresh output paths. The independent comparison also requires the original
Architecture JSON/IFC exports described in the room-finish experiment.

No Autodesk installation/account is available. Autodesk acceptance, signature
generation, save bookkeeping and creation of new model elements remain
unverified or unimplemented. Re-reading with our own codecs or the public
reader does not prove those properties. This remains research, not native
production export.
