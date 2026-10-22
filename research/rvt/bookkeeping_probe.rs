// Inspect only file bytes with the pinned public clean-room schema decoder.
use std::collections::BTreeMap;
fn main() {
    let dir = std::path::PathBuf::from(std::env::args().nth(1).unwrap());
    let read = |name| std::fs::read(dir.join(name)).unwrap();
    let registry = rvt::schema_registry::parse(&read("schema.bin")).unwrap();
    let history = read("history.bin");
    let episodes = rvt::native_index::creation_episodes(&history, &registry).unwrap();
    let table = rvt::native_index::parse(&read("table.bin"), &registry, &episodes).unwrap();
    let increments = read("increments.bin");
    let storage = rvt::native_index::storage_increments(&increments, &registry).unwrap();
    let root = |data: &[u8]| {
        let tag = u16::from_le_bytes(data[..2].try_into().unwrap());
        rvt::native_parameters::decode_object_fields(data, &registry, 2, tag).unwrap()
    };
    let mut revisions = BTreeMap::<u32, usize>::new();
    let mut partitions = BTreeMap::<i64, usize>::new();
    for id in table.identities.values() {
        *revisions.entry(id.stored_revision).or_default() += 1;
        *partitions.entry(id.partition_id).or_default() += 1;
    }
    println!("{}", serde_json::to_string_pretty(&serde_json::json!({
        "episode_count": episodes.len(), "table_record_count": table.identities.len(),
        "graveyard_records": table.graveyard_rows.len(), "id_source": table.source_fields,
        "modification_episode_histogram": revisions, "partition_id_histogram": partitions,
        "increments": storage, "history_root": root(&history),
        "increment_root": root(&increments), "room_identity": table.identities.get(&348738)
    })).unwrap());
}
