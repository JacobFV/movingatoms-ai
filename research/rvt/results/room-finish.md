# Actual room-parameter edit and matched controls

The pinned MIT RE1 Architecture fixture contains room 348738, `Storage Narrow`
(number `RE-9`), whose `ROOM_FINISH_FLOOR` parameter (-1006903) is `Wood`.
`parameter_experiment.py` changes its four UTF-16 characters to `Cork` and
recomputes the enclosing data object's Adler-32. Exactly one gzip member
(member 20 in the base segment of `Partitions/80`) is recompressed. Object,
inflated-member, and parameter lengths remain unchanged; compressed lengths,
gzip CRC/ISIZE, and all page framing/parity are regenerated.

The strict transactional writer verifies the output and all unchanged streams
and directory metadata. The pinned independent rvt-rs reader reports:

- 154 elements before and after; exactly one field changes, on room 348738.
- Exactly one IFC line changes after normalizing its two exporter timestamps:
  `FloorCovering` changes from `Wood` to `Cork`.
- Every other element JSON value and IFC line is unchanged.

This is an actual model-data edit, **not** a complete Revit save or proof of
Autodesk acceptance. The unknown 64-byte partition footer is preserved and
has not been regenerated. Reference IDs, save counters, and History are not
changed. No new element is created. Do not advertise this as production RVT
editing merely because the independent reader sees the intended property.

Matched candidates were also generated:

| Candidate | Change | Independent reader |
| --- | --- | --- |
| `room-finish.rvt` | Parameter + object checksum + gzip + page parity | Exactly the intended property change |
| `recompress-control.rvt` | Recompress the same member with identical inflated bytes | Byte-identical element JSON |
| `footer-control.rvt` | Flip one bit of the base segment's 64-byte footer; regenerate page parity | Byte-identical element JSON |

Their distinct outcomes in Autodesk would help separate compressed-byte,
object-content, and footer enforcement. No Autodesk outcome has been observed.
The footer-control file is intentionally a negative integrity test, not a
proposed customer artifact. The public reader's acceptance does not validate
that footer.

Reproduce each mode into a fresh directory:

```sh
python3 research/rvt/parameter_experiment.py research/rvt/local/RE1-Architecture.rvt research/rvt/local/new-room-finish --mode room-finish
processing/rvt-native/target/release/ma-rvt-native patch research/rvt/local/RE1-Architecture.rvt research/rvt/local/new-room-finish.rvt research/rvt/local/new-room-finish/manifest.json
```

`verify_parameter_experiment.py` checks the independent JSON/IFC comparisons.
The `*-plan.json`, `*-writer.json`, and `room-finish-reader.json` files record
preconditions, changed member, exact property change, and explicit limits.

## Signature-field-empty variants

The schema follow-up identifies the footer as `SignatureMarker`. Two further
candidates, `unsigned-control` and `unsigned-room-finish`, clear both its
private binary value and public string on the base content group. Their
reader element JSON and IFC (apart from export timestamps) exactly match the
unchanged and edited references respectively. Acceptance of unsigned nonempty
content is still untested. `signature-validation.json` records all five
candidate hashes; `signature_bundle.py` packages them with the original,
fixture license, and concrete external-validation instructions.
