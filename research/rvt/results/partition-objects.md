# Object envelopes and counts recovered

`partition_objects.py` strictly decodes all **736,332 object records** in the
six pinned fixtures: 245,444 records in each of sequences 101, 102, and 103.
`partition-objects.json` records each content group's checks. All encoded
object bytes reconstruct exactly. This includes 490,888 checked Adler-32
values in sequences 102/103 (including their empty terminal records).

For ID width W (4 bytes on the tested 2023 fixture; 8 on 2024/2025):

| Sequence | Wire envelope |
| --- | --- |
| 101 | `ID[W], u32 body_length, body, u32 body_length` |
| 102, 103 | `ID[W], u32 Adler32(body), u32 body_length, body, u32 body_length` |

Every one of the 523 content groups has three sequences with the **same ordered
ID list**, unique within the sequence. Each list contains the declared element
count plus one: its last ID is all ones and its body is empty. The count is not
an approximate scan result. The encoder recomputes both repeated lengths and
checksums, and its output equals the original inflated wire bytes.

On 2024+ sequence-101 records, the word at record offset +8 is the body length.
It must not be copied or modified as an unexplained flags word when constructing
an encoder. Class-specific contents remain opaque here.

The gzip member kind is a continuation bit field:

- 4: a counted list of whole objects.
- 6: one object's header and first body fragment.
- 7: a middle body fragment.
- 5: the last body fragment and repeated total body length.

The member `body_length` excludes these object-envelope bytes. The parser
checks each count/length, continuation ordering, assembled object size, repeated
size, checksum, sequence membership, and final sentinel. Synthetic tests also
exercise objects split over gzip boundaries in both ID widths.

The room-edit experiment now validates these object invariants before and after
editing. Only sequence 102's object 348738 changes; the recompression and
footer controls change no object. `parameter-object-validation.json` additionally
records complete object validation on all three generated RVT candidates.

These are object **envelope** encoders, not class-specific wall/floor/family
encoders or a native model exporter. The signature marker and save/reference
bookkeeping are not regenerated. SHA-512 of each sequence's concatenated
object bodies, or all bodies together, does not match any observed nonempty
signature field; this excludes only those concrete candidate inputs.

```sh
python3 research/rvt/verify_objects.py research/rvt/local/core2024.rvt research/rvt/local/einhoven.rvt research/rvt/local/RE1-*.rvt
python3 -m unittest discover -s research/rvt -p 'test_partition_objects.py'
```
