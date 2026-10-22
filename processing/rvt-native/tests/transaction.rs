use ma_rvt_native::{
    paged,
    writer::{self, Create, Manifest, Patch},
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
    file.set_state_bits("Global", 0x12345678).unwrap();
    file.set_state_bits("UnknownMetadata", 0x87654321).unwrap();
    for path in ["/", "Global", "Global/Latest", "UnknownMetadata"] {
        file.set_created_time(
            path,
            std::time::UNIX_EPOCH + std::time::Duration::from_secs(123456789),
        )
        .unwrap();
        file.set_modified_time(
            path,
            std::time::UNIX_EPOCH + std::time::Duration::from_secs(234567890),
        )
        .unwrap();
    }
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
        creates: vec![],
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

fn creation_plan(input: &Path, dir: &Path, data: &[u8]) -> Manifest {
    let mut file = cfb::open_rw(input).unwrap();
    file.create_storage("Partitions").unwrap();
    file.set_state_bits("Partitions", 0x13572468).unwrap();
    file.flush().unwrap();
    drop(file);
    let mut manifest = plan(input, dir, data);
    manifest.patches.clear();
    manifest.creates.push(Create {
        stream: "Partitions/123".into(),
        expected_absent: true,
        new_payload_file: "logical.bin".into(),
    });
    manifest
}

#[test]
fn create_partition_and_replace_atomically() {
    for size in [99, 5000, paged::PAYLOAD * 2 + 73] {
        let dir = tempfile::tempdir().unwrap();
        let input = dir.path().join("input.rvt");
        let output = dir.path().join("output.rvt");
        fixture(&input);
        let data: Vec<_> = (0..size).map(|i| (i * 31) as u8).collect();
        let mut manifest = creation_plan(&input, dir.path(), &data);
        manifest.patches.push(Patch {
            stream: "UnknownMetadata".into(),
            expected_stored_sha256: writer::hash(b"must survive unchanged"),
            new_payload_file: Some("logical.bin".into()),
            new_unpaged_file: None,
        });
        let original = fs::read(&input).unwrap();
        let report = writer::patch(&input, &output, &manifest, dir.path()).unwrap();
        assert_eq!(report.created_streams, ["/Partitions/123"]);
        assert_eq!(report.changed_streams, ["/UnknownMetadata"]);
        assert_eq!(report.streams_verified, 3);
        assert_eq!(fs::read(&input).unwrap(), original);
        let mut file = cfb::open(&output).unwrap();
        let mut stored = Vec::new();
        file.open_stream("Partitions/123")
            .unwrap()
            .read_to_end(&mut stored)
            .unwrap();
        assert_eq!(ma_rvt_native::codec::decode(&stored).unwrap(), data);
        assert_eq!(writer::verify(&output).unwrap().streams_verified, 3);
    }
}

#[test]
fn invalid_creation_never_publishes_or_alters_input() {
    for case in 0..11 {
        let dir = tempfile::tempdir().unwrap();
        let input = dir.path().join("input.rvt");
        let output = dir.path().join("output.rvt");
        fixture(&input);
        let mut manifest = creation_plan(&input, dir.path(), b"complete logical payload");
        match case {
            0 => manifest.input_sha256 = "stale".into(),
            1 => manifest.creates[0].expected_absent = false,
            2 => manifest.creates[0].stream = "Global/123".into(),
            3 => manifest.creates[0].stream = "Partitions/../123".into(),
            4 => manifest.creates[0].stream = "Partitions/0123".into(),
            5 => manifest.creates[0].stream = "//Partitions/123".into(),
            6 => fs::write(dir.path().join("logical.bin"), b"").unwrap(),
            7 => manifest.creates[0].new_payload_file = "missing.bin".into(),
            8 => manifest.creates.push(Create {
                stream: "/Partitions/123".into(),
                expected_absent: true,
                new_payload_file: "logical.bin".into(),
            }),
            9 => {
                let mut file = cfb::open_rw(&input).unwrap();
                file.create_stream("Partitions/123")
                    .unwrap()
                    .write_all(&ma_rvt_native::codec::encode(b"existing payload").unwrap())
                    .unwrap();
                file.flush().unwrap();
                drop(file);
                manifest.input_sha256 = writer::hash(&fs::read(&input).unwrap());
            }
            10 => {
                let mut file = cfb::open_rw(&input).unwrap();
                file.remove_storage("Partitions").unwrap();
                file.flush().unwrap();
                drop(file);
                manifest.input_sha256 = writer::hash(&fs::read(&input).unwrap());
            }
            _ => unreachable!(),
        }
        let original = fs::read(&input).unwrap();
        assert!(
            writer::patch(&input, &output, &manifest, dir.path()).is_err(),
            "case {case}"
        );
        assert!(!output.exists(), "case {case}");
        assert_eq!(fs::read(&input).unwrap(), original);
    }
}

#[test]
fn creation_is_opt_in_and_output_cannot_be_overwritten() {
    let old: Manifest = serde_json::from_str(r#"{"input_sha256":"x","patches":[]}"#).unwrap();
    assert!(old.creates.is_empty());
    assert!(serde_json::from_str::<Manifest>(r#"{"input_sha256":"x","patches":[],"creates":[{"stream":"Partitions/1","new_payload_file":"x"}]}"#).is_err());
    let dir = tempfile::tempdir().unwrap();
    let input = dir.path().join("input.rvt");
    let output = dir.path().join("output.rvt");
    fixture(&input);
    let manifest = creation_plan(&input, dir.path(), b"payload");
    fs::write(&output, b"do not overwrite").unwrap();
    assert!(writer::patch(&input, &output, &manifest, dir.path()).is_err());
    assert_eq!(fs::read(&output).unwrap(), b"do not overwrite");
}

#[test]
fn contents_payload_uses_page_framing_and_corruption_is_rejected() {
    let dir = tempfile::tempdir().unwrap();
    let input = dir.path().join("input.rvt");
    let output = dir.path().join("output.rvt");
    fixture(&input);
    let old = ma_rvt_native::codec::encode(b"original Contents logical bytes").unwrap();
    {
        let mut file = cfb::open_rw(&input).unwrap();
        file.create_stream("Contents")
            .unwrap()
            .write_all(&old)
            .unwrap();
        file.flush().unwrap();
    }
    let payload = b"replacement Contents logical bytes with a different length";
    fs::write(dir.path().join("contents.bin"), payload).unwrap();
    let manifest = Manifest {
        input_sha256: writer::hash(&fs::read(&input).unwrap()),
        creates: vec![],
        patches: vec![Patch {
            stream: "Contents".into(),
            expected_stored_sha256: writer::hash(&old),
            new_payload_file: Some("contents.bin".into()),
            new_unpaged_file: None,
        }],
    };
    let report = writer::patch(&input, &output, &manifest, dir.path()).unwrap();
    assert_eq!(report.final_pages_verified, 1);
    let mut stored = Vec::new();
    {
        let mut file = cfb::open_rw(&output).unwrap();
        file.open_stream("Contents")
            .unwrap()
            .read_to_end(&mut stored)
            .unwrap();
        assert_eq!(ma_rvt_native::codec::decode(&stored).unwrap(), payload);
        assert_ne!(stored, payload);
        stored[0] ^= 1;
        file.create_stream("Contents")
            .unwrap()
            .write_all(&stored)
            .unwrap();
        file.flush().unwrap();
    }
    assert!(writer::verify(&output).is_err());
}
