# Save actor fields: observed equality and distinct labels

The candidate sets the new increment's `m_userName` to a research identity while
preserving BasicFileInfo and ProjectInformation actor fields. The expanded
11-fixture audit finds **no equality rule requiring those fields to match**.
It does not establish a universal save policy from their names.

The audit covers the original six licensed files plus five historical Core
Interior snapshots. It decodes increment tables with the verified codec and
uses the pinned public reader `b6086d41b9758fd9b92f42f0a47b8345b9c58056` to
parse all named BasicFileInfo properties. XML extraction reuses the sibling
`ancillary_transitions_xml.py::leaves` traversal to avoid a competing parser.

Observed across all 11 files:

- BasicFileInfo has named `Username` and `Author` properties. `Username` is empty
  in **every file**; latest-increment `m_userName` is nonempty in every file.
- `Author` is the same nonempty 14-character value in every file and never
  equals latest-increment `m_userName`. The report retains its hash, not its
  text. A label of “Author” therefore does not justify treating it as the
  current human editor.
- No named BasicFileInfo property equals the latest-increment username.
  No additional `Last Saved By`/`LastSavedBy` property was observed; the complete
  property-name inventory is recorded without values.
- No author leaf was found in the ProjectInformation XML paths examined in
  any fixture. This is absence in the observed XML, not a claim about every
  possible author field elsewhere in the RVT.
- The actor values in the primary and local increment arrays match for every
  row in every fixture.

The Core Interior snapshots and Einhoven each contain one distinct increment
username. Architecture, Mechanical and Plumbing each contain three; Electrical
contains four. The latest username occurs in 15 of Architecture's 85 increments,
7 of Mechanical's 80, 6 of Plumbing's 63 and 35 of Electrical's 121. The
historical actor entries are preserved; these are not overwritten to make all
rows name the latest actor.

The findings support retaining the distinction between increment user metadata
and the other named properties. They do **not** prove that preserving the empty
BasicFileInfo Username is required, nor that a particular user identity string
is accepted by Revit. There is no basis in this corpus for copying the new
increment actor into BasicFileInfo Author or for creating an absent XML author.
The complete native save remains experimental.

## Redaction and reproduction

`save-actors.json` contains property names, SHA-256 hashes of UTF-8 values,
character lengths, empty flags, equality results and counts. It contains no
actual usernames, author strings, filesystem paths or XML leaf text. Hashes
support equality comparisons; they are not a claim of cryptographic anonymity.

```sh
python3 research/rvt/save_actor_audit.py \
  --reader-source /path/to/pinned/rvt-rs \
  --target research/rvt/local/schema-target \
  research/rvt/local research/rvt/results/paired-save-sources.json \
  > research/rvt/results/save-actors.json
PYTHONPATH=research/rvt python3 -m unittest research/rvt/test_save_actor_audit.py -v
```

Two tests verify empty/different actor comparisons and that raw synthetic actor
values and private paths do not appear in serialized reports. The audit writes
no RVT and inspects no proprietary implementation. Autodesk acceptance remains
untested.
