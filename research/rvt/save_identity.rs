// File bytes plus the pinned public clean-room reader only.
fn main() {
    let dir = std::path::PathBuf::from(std::env::args().nth(1).unwrap());
    let read = |name| std::fs::read(dir.join(name)).unwrap();
    let schema = read("schema.bin");
    let registry = rvt::schema_registry::parse(&schema).unwrap();
    let grammar = rvt::formats::schema_classes(&schema);
    assert!(grammar.stopped.is_none() && grammar.parsed_bytes == schema.len());
    let declarations = rvt::formats::parse_schema(&schema).unwrap();
    let contents = read("contents.bin");
    let tag = u16::from_le_bytes(contents[..2].try_into().unwrap());
    let root = rvt::native_parameters::decode_object_fields(&contents, &registry, 2, tag).unwrap();
    let names = ["DocumentStorageIndexImpl", "DocumentStorageIndex"];
    let classes: Vec<_> = grammar.classes.iter().filter(|c| names.contains(&c.name.as_str())).collect();
    let fields: Vec<_> = declarations.classes.iter().filter(|c| names.contains(&c.name.as_str()) && !c.was_parent_only).collect();
    let bfi = rvt::basic_file_info::BasicFileInfo::from_bytes(&read("basic.bin")).unwrap();
    let latest = read("latest.bin");
    let latest_tag = u16::from_le_bytes(latest[..2].try_into().unwrap());
    let latest_audit = match rvt::native_parameters::decode_object_fields(&latest, &registry, 2, latest_tag) {
        Ok(fields) => {
            let value = serde_json::to_value(&fields.fields).unwrap();
            let names: Vec<_> = value.as_object().unwrap().keys().collect();
            let selected: serde_json::Map<String, serde_json::Value> = value.as_object().unwrap().iter()
                .filter(|(key, _)| ["guid", "increment", "episode", "sequence", "counter", "version", "history"].iter().any(|word| key.to_lowercase().contains(word)))
                .map(|(k,v)| (k.clone(),v.clone())).collect();
            serde_json::json!({"status":"root_fields_decoded", "class_tag":latest_tag,
                "class_name":fields.class_name, "end":fields.end, "inflated_bytes":latest.len(),
                "field_names":names, "selected_fields":selected, "field_spans":fields.field_spans})
        },
        Err(error) => serde_json::json!({"status":"root_decode_failed", "class_tag":latest_tag,
            "inflated_bytes":latest.len(), "error":error.to_string()})
    };
    let graph_body = latest.strip_suffix(&[0, 0, 0, 0]).unwrap_or(&latest);
    let latest_graph = match rvt::native_parameters::decode_graph(graph_body, &registry) {
        Ok(graph) => {
            let objects: Vec<_> = graph.objects.iter().map(|o| serde_json::json!({
                "class_name":o.class_name, "class_tag":o.class_tag, "start":o.start,
                "fields_end":o.fields_end,
                "field_names":o.fields.as_object().map(|m| m.keys().collect::<Vec<_>>()),
                "selected_fields":o.fields.as_object().map(|m| m.iter().filter(|(key,_)|
                    ["guid", "increment", "episode", "sequence", "counter", "version", "history"].iter().any(|word| key.to_lowercase().contains(word)))
                    .map(|(k,v)| (k.clone(),v.clone())).collect::<serde_json::Map<String,serde_json::Value>>())
            })).collect();
            serde_json::json!({"status":"graph_decoded", "consumed_bytes":graph.consumed_bytes,
                "inflated_bytes":latest.len(), "trailing_zero_bytes":latest.len()-graph_body.len(), "object_count":objects.len(),
                "identity_named_objects":objects.iter().filter(|o| !o["selected_fields"].as_object().unwrap().is_empty()).collect::<Vec<_>>(),
                "edges":graph.edges.len()})
        },
        Err(error) => serde_json::json!({"status":"graph_decode_failed", "error":error.to_string()})
    };
    println!("{}", serde_json::to_string_pretty(&serde_json::json!({
        "contents_root": root, "classes": classes, "declarations": fields,
        "document_guid": bfi.document_guid(), "document_increments": bfi.document_increments(),
        "properties": bfi.properties, "latest_audit": latest_audit, "latest_graph": latest_graph
    })).unwrap());
}
