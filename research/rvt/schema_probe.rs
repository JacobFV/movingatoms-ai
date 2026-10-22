// Uses only the pinned public clean-room rvt-rs parser and file-embedded metadata.
fn main() {
    let path = std::env::args().nth(1).expect("inflated Formats/Latest path");
    let data = std::fs::read(path).unwrap();
    let grammar = rvt::formats::schema_classes(&data);
    assert!(grammar.stopped.is_none() && grammar.parsed_bytes == data.len(), "incomplete schema grammar");
    let names = ["ContentKey", "ContentMarker", "SegmentMarker", "SegmentCheckback", "SignatureMarker"];
    let fields = rvt::formats::parse_schema(&data).unwrap();
    let selected: Vec<_> = grammar.classes.iter().filter(|c| names.contains(&c.name.as_str())).collect();
    let declarations: Vec<_> = fields.classes.iter().filter(|c| names.contains(&c.name.as_str()) && !c.was_parent_only).collect();
    println!("{}", serde_json::to_string_pretty(&serde_json::json!({
        "schema_bytes": data.len(), "class_count": grammar.classes.len(),
        "grammar_complete": true, "classes": selected, "declarations": declarations
    })).unwrap());
}
