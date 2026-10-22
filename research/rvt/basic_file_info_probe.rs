// Verify only file bytes against the pinned public clean-room reader.
fn main() {
    let args: Vec<_> = std::env::args().collect();
    let original = rvt::basic_file_info::BasicFileInfo::from_bytes(&std::fs::read(&args[1]).unwrap()).unwrap();
    let changed = rvt::basic_file_info::BasicFileInfo::from_bytes(&std::fs::read(&args[2]).unwrap()).unwrap();
    let count: u32 = args[3].parse().unwrap();
    let guid = &args[4];
    let mut expected = original.properties.clone();
    for prop in &mut expected {
        if ["Unique Document Increments", "Central model's version number corresponding to the last reload latest"].contains(&prop.key.as_str()) {
            prop.value = count.to_string();
        }
        if ["Unique Document GUID", "Central model's episode GUID corresponding to the last reload latest"].contains(&prop.key.as_str()) {
            prop.value = guid.clone();
        }
    }
    assert_eq!(changed.properties, expected);
    assert_eq!(changed.document_increments(), Some(count));
    assert_eq!(changed.document_guid(), Some(guid.as_str()));
    println!("{}",serde_json::json!({"all_properties_equal_expected":true,"document_increments":count,"document_guid":guid}));
}
