# Licensed paired-save source discovery

The existing MIT-licensed Core Interior dataset has six distinct RVT snapshots
in Git history. The earlier assumption that only one save was available was
incorrect. Five historical files are now downloaded under ignored local storage,
with their Git LFS SHA-256 and byte sizes verified. At every selected commit,
the repository LICENSE is the same MIT text with SHA-256
`0ab138580e235fd4024d9a0d7589a9fe6982aab1503356415cdef15d1e2cb4fc`.

The primary source is [the Core Interior path's Git history](https://api.github.com/repos/magnetar-io/revit-test-datasets/commits?path=Revit/2024_Core_Interior.rvt&per_page=100).
The machine-readable report records complete commit IDs, dates, LFS hashes,
pinned download URLs and commit-specific license URLs. Git-adjacent snapshots
are **not necessarily adjacent Revit saves**.

| Git snapshot | Bytes | History episodes | Increment entries |
|---|---:|---:|---:|
| bd8c0792, Aug 6 2023 | 17,731,584 | 31 | 48 |
| 21b61e69, Aug 6 2023 | 23,490,560 | 33 | 51 |
| 5859762b, Aug 6 2023 | 20,779,008 | 34 | 53 |
| ede6e635, Aug 12 2023 | 29,282,304 | 36 | 59 |
| 8946a8ca, Aug 13 2023 | 30,814,208 | 37 | 61 |
| fd755e18, Jun 2 2024 | 33,718,272 | 39 | 66 |

Across all six snapshots, adjacent histories share the same creation GUID,
retain the complete older episode sequence as the newer history's suffix, and
have different newest episodes. All five adjacent pairs pass these checks.
This establishes shared file lineage with real
later revisions. The smallest immediately usable pair is `bd8c0792` →
`21b61e69`; the next pair adds one History episode and two increment entries.
These files can support real stream and object transition analysis without
obtaining any new Autodesk service or installation.

The initial decoder rejected two streams: the 797-byte History stream in
`8946a8ca` and the 1,772-byte DocumentIncrementTable stream in `ede6e635`.
Those failures exposed valid historical page layouts excluded by the earlier
canonical layout selection. After the codec was corrected to accept a unique
parity-valid historical layout, all twelve History/increment streams decode
successfully through the strict transport path. No unchecked gzip fallback was
used. The initial failures remain recorded in the JSON report to preserve the
research sequence; they are resolved findings, not current blockers.

The same primary-source path-history search found one commit for Einhoven and
one commit for each of the four RE1 fixture paths. Those paths therefore did
not add paired saves in the inspected history. Exact query URLs and returned
commit metadata are retained in the JSON report; renamed paths, deleted branches
and other repositories have not been exhaustively searched.

```sh
python3 research/rvt/paired_save_sources.py research/rvt/local --fetch > research/rvt/results/paired-save-sources.json
```

`--fetch` verifies the pinned historical MIT license before any missing model
is downloaded, validates each file against its LFS SHA-256 and size, then runs
the strict History/increment audit. Without it, only local pinned files are
read. No proprietary or education-licensed sample was introduced.
