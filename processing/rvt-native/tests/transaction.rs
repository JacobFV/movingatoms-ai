use ma_rvt_native::{
    paged,
    writer::{self, Manifest, Patch},
};
use std::{
    fs,
    io::{Read, Write},
    path::Path,
};
fn fixture(path: &Path) -> Vec<u8> {
    let data = vec![19; paged::PAYLOAD];
    let mut file = cfb::create(path).unwrap();
    file.create_storage("Global").unwrap();
    file.create_stream("Global/Latest")
        .unwrap()
        .write_all(&paged::encode(&data).unwrap())
        .unwrap();
    file.create_stream("UnknownMetadata")
        .unwrap()
        .write_all(b"must survive unchanged")
        .unwrap();
    file.flush().unwrap();
    data
}
fn plan(input: &Path, dir: &Path, data: &[u8]) -> Manifest {
    let mut file = cfb::open(input).unwrap();
    let mut stored = Vec::new();
    file.open_stream("UnknownMetadata")
        .unwrap()
        .read_to_end(&mut stored)
        .unwrap();
    fs::write(dir.join("logical.bin"), data).unwrap();
    Manifest {
        input_sha256: writer::hash(&fs::read(input).unwrap()),
        patches: vec![Patch {
            stream: "UnknownMetadata".into(),
            expected_stored_sha256: writer::hash(&stored),
            new_unpaged_file: Some("logical.bin".into()),
            new_payload_file: None,
        }],
    }
}
#[test]
fn grow_shrink_and_preserve_other_streams() {
    for size in [33, 5000, paged::PAYLOAD * 3 + 9] {
        let dir = tempfile::tempdir().unwrap();
        let input = dir.path().join("input.rvt");
        let output = dir.path().join("output.rvt");
        fixture(&input);
        let original = fs::read(&input).unwrap();
        let data: Vec<_> = (0..size).map(|x| (x * 17 + x / 253) as u8).collect();
        let report = writer::patch(
            &input,
            &output,
            &plan(&input, dir.path(), &data),
            dir.path(),
        )
        .unwrap();
        assert_eq!(report.changed_streams, ["/UnknownMetadata"]);
        assert_eq!(fs::read(&input).unwrap(), original);
        let mut file = cfb::open(&output).unwrap();
        let mut stored = Vec::new();
        file.open_stream("Global/Latest")
            .unwrap()
            .read_to_end(&mut stored)
            .unwrap();
        assert_eq!(paged::decode(&stored).unwrap(), vec![19; paged::PAYLOAD]);
        let mut metadata = Vec::new();
        file.open_stream("UnknownMetadata")
            .unwrap()
            .read_to_end(&mut metadata)
            .unwrap();
        assert_eq!(metadata, data);
    }
}
#[test]
fn identity_is_whole_file_identical() {
    let dir = tempfile::tempdir().unwrap();
    let input = dir.path().join("input.rvt");
    let output = dir.path().join("output.rvt");
    fixture(&input);
    let data = b"must survive unchanged".to_vec();
    let report = writer::patch(
        &input,
        &output,
        &plan(&input, dir.path(), &data),
        dir.path(),
    )
    .unwrap();
    assert!(report.changed_streams.is_empty());
    assert_eq!(fs::read(input).unwrap(), fs::read(output).unwrap());
}
#[test]
fn failures_never_publish_and_existing_outputs_survive() {
    let dir = tempfile::tempdir().unwrap();
    let input = dir.path().join("input.rvt");
    let output = dir.path().join("output.rvt");
    fixture(&input);
    let mut manifest = plan(&input, dir.path(), b"new data");
    manifest.input_sha256 = "bad".into();
    assert!(writer::patch(&input, &output, &manifest, dir.path()).is_err());
    assert!(!output.exists());
    manifest.input_sha256 = writer::hash(&fs::read(&input).unwrap());
    manifest.patches[0].expected_stored_sha256 = "bad".into();
    assert!(writer::patch(&input, &output, &manifest, dir.path()).is_err());
    assert!(!output.exists());
    fs::write(&output, b"existing output").unwrap();
    assert!(writer::patch(&input, &output, &manifest, dir.path()).is_err());
    assert_eq!(fs::read(output).unwrap(), b"existing output");
}

#[test]
fn paged_growth_and_invalid_final_page_rollback() {
    let dir = tempfile::tempdir().unwrap();
    let input = dir.path().join("input.rvt");
    let output = dir.path().join("grown.rvt");
    fixture(&input);
    let data = vec![77; paged::PAYLOAD * 3];
    let mut manifest = plan(&input, dir.path(), &data);
    manifest.patches[0].stream = "Global/Latest".into();
    manifest.patches[0].expected_stored_sha256 =
        writer::hash(&paged::encode(&vec![19; paged::PAYLOAD]).unwrap());
    let report = writer::patch(&input, &output, &manifest, dir.path()).unwrap();
    assert_eq!(report.parity_pages_verified, 3);
    assert_eq!(report.changed_streams, ["/Global/Latest"]);
    fs::write(dir.path().join("logical.bin"), b"invalid final page").unwrap();
    let bad = dir.path().join("bad.rvt");
    assert!(writer::patch(&input, &bad, &manifest, dir.path()).is_err());
    assert!(!bad.exists());
}

#[test]
fn complete_payload_growth_shrink_and_manifest_exclusivity() {
    for size in [
        1,
        97,
        4095,
        4096,
        paged::PAYLOAD - 1,
        paged::PAYLOAD + 1,
        2 * paged::PAYLOAD + 9,
    ] {
        let dir = tempfile::tempdir().unwrap();
        let input = dir.path().join("input.rvt");
        let output = dir.path().join("output.rvt");
        fixture(&input);
        let data: Vec<u8> = (0..size).map(|i| (i * 17 + 191) as u8).collect();
        let mut manifest = plan(&input, dir.path(), &data);
        let p = &mut manifest.patches[0];
        p.stream = "Global/Latest".into();
        p.expected_stored_sha256 = writer::hash(&paged::encode(&vec![19; paged::PAYLOAD]).unwrap());
        p.new_payload_file = p.new_unpaged_file.take();
        writer::patch(&input, &output, &manifest, dir.path()).unwrap();
        let mut file = cfb::open(&output).unwrap();
        let mut stored = Vec::new();
        file.open_stream("Global/Latest")
            .unwrap()
            .read_to_end(&mut stored)
            .unwrap();
        assert_eq!(ma_rvt_native::codec::decode(&stored).unwrap(), data);
        manifest.patches[0].new_unpaged_file = Some("logical.bin".into());
        let bad = dir.path().join("ambiguous.rvt");
        assert!(writer::patch(&input, &bad, &manifest, dir.path()).is_err());
        assert!(!bad.exists());
    }
}
