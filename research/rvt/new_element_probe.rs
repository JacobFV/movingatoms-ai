// Clean-room inventory of constructible-looking classes; no RVT mutation.
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args().collect();
    if args[1] == "identity" {
        let registry = rvt::schema_registry::parse(&std::fs::read(&args[2])?)?;
        let episodes = rvt::native_index::creation_episodes(&std::fs::read(&args[4])?, &registry)?;
        let index = rvt::native_index::parse(&std::fs::read(&args[3])?, &registry, &episodes)?;
        println!("{}", serde_json::to_string_pretty(&index)?);
        return Ok(());
    }
    if args[1] == "decode" {
        let schema = std::fs::read(&args[2])?;
        let registry = rvt::schema_registry::parse(&schema)?;
        let body = std::fs::read(&args[3])?;
        let catalog: Option<rvt::native_extensible_storage::Catalog> = args.get(4).map(|p| {
            let bytes = std::fs::read(p)?; Ok::<_,Box<dyn std::error::Error>> (serde_json::from_slice(&bytes)?)
        }).transpose()?;
        let graph = rvt::native_parameters::decode_graph_with_catalog(&body, &registry, &Default::default(), catalog.as_ref())?;
        let roots: Vec<_> = graph.objects.iter().filter(|o| o.start == 2 || matches!(o.class_name.as_str(), "ElemsSetWithCellsTracking" | "EStorageTracking")).map(|o|
            rvt::native_parameters::decode_object_fields(&body, &registry, o.start, o.class_tag)
        ).collect::<Result<_,_>>()?;
        let declarations = &registry.classes;
        println!("{}", serde_json::to_string_pretty(&serde_json::json!({"graph":graph,"objects":roots,"declarations":declarations}))?);
        return Ok(());
    }
    let mut file = rvt::RevitFile::open(std::path::Path::new(&args[1]))?;
    let options = rvt::native_document::Options {
        
        channels: [101,102,103].into_iter().collect(),
        selected_ids: args.get(2).filter(|s| !s.starts_with("class:")).map(|s| s.parse()).transpose()?.into_iter().collect(),
        selected_classes: args.get(2).and_then(|s| s.strip_prefix("class:")).map(String::from).into_iter().collect(),
        ..Default::default()
    };
    let mut selected = std::collections::BTreeMap::new();
    let summary = rvt::native_document::extract_graphs(&mut file, &options, |record| {
        let key = (record.class_name.clone(), record.channel, if args.get(2).is_some_and(|s| s.starts_with("class:")) {record.identity.element_id} else {0});
        let keep = selected.get(&key).map_or(true, |old: &rvt::native_document::Record| record.source.body_bytes < old.source.body_bytes);
        if keep { selected.insert(key, record); }
        Ok(())
    })?;
    println!("{}", serde_json::to_string_pretty(&serde_json::json!({"records":selected.into_values().collect::<Vec<_>>(),"summary":summary}))?);
    Ok(())
}
