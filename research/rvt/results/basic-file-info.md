# BasicFileInfo: binary duplicates and variable-length identity edits

The earlier text-property patch left binary-prefix identity copies unchanged.
This audit identifies and updates all observed copies in six licensed fixtures,
while preserving opaque bytes. It does not claim a complete semantic decoder of
the BasicFileInfo header.

Before the readable `Worksharing:` property block, every fixture contains this
contiguous sequence:

1. A little-endian uint32 equal to `Unique Document Increments`.
2. A uint32 length of 36, followed by the UTF-16 document GUID.
3. A second length-36 UTF-16 copy of the same GUID.
4. A uint32 code-unit length and UTF-16 decimal copy of the increment counter.
5. A length-36 UTF-16 model identity GUID.

The first four records match the two counter and two GUID properties in the
text block. Therefore the stream contains four observed counter representations
and four observed document GUID representations. The matching History episode
relationship is documented in `save-identity.md`.

For RE1-Architecture, the uint32 counter is at byte 326, the two GUID records
occupy 330–405 and 406–481, and the decimal counter record occupies 482–489.
Those offsets are evidence for that fixture, not hard-coded parsing constants.
The decoder finds and validates the paired length-prefixed GUID records against
the named text properties, verifies both binary counters, checks the following
model identity record, and rejects missing, duplicated or inconsistent fields.
It also requires the observed first uint32 value 14; its semantic name remains
unestablished.

`basic_file_info_codec.decode` returns guarded identity framing with original
bytes. `encode` updates the uint32 counter, both GUID records, the decimal
record's length and value, and the four corresponding text properties. Growing
99 to 100 adds two bytes to the decimal record and two bytes to each text
counter, totaling six bytes. The observed text block has no per-property length
prefix, so its values end at UTF-16 CRLF delimiters. All unedited byte slices are
copied exactly. Changed streams are re-parsed, and reverse edits reconstruct the
original stream byte-for-byte.

The following model identity GUID is all-zero in every fixture. It numerically
matches History `m_previousUpgradeGUID`, which is also zero, but this null-value
equality provides no stable namespace or copy/fork identity evidence. The audit
records the relationship without assigning identity semantics.

## Validation

- Six licensed, SHA-256-pinned streams reproduce exactly through decode/encode.
- Twenty-four trials set counters to 99, 100, 1000 and 9 and replace the document
  GUID. Each independently passes the pinned public reader's full property
  comparison: exactly the four expected text values differ.
- Every trial reverses to the original bytes, including opaque fields.
- Five tests cover digit-width growth and shrinkage, zero, all duplicate copies,
  ambiguous layouts, mismatched binary/text values, malformed edits and stale
  parsed spans.

The public reader's BasicFileInfo parser verifies text properties; its success
does not independently prove binary-prefix semantics. Those fields are bound
by the repeated framing and cross-copy equality observed in all six files.
Other header values or record arrangements are explicitly unsupported, and
Autodesk acceptance remains untested.

```sh
python3 research/rvt/basic_file_info_audit.py --reader-source /home/brandonin/.cache/movingatoms-rvt-rs --target research/rvt/local/schema-target research/rvt/local > research/rvt/results/basic-file-info.json
python3 -m unittest discover -s research/rvt -p test_basic_file_info_codec.py
```
