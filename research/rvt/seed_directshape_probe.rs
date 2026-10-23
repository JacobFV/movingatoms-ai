// Independent public-reader saved graphics and native records for explicit IDs.
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args().collect();
    if args[1] == "schema" {
        let registry = rvt::schema_registry::parse(&std::fs::read(&args[2])?)?;
        println!("{}", serde_json::to_string_pretty(&registry.classes)?);
        return Ok(());
    }
    let mut file = rvt::RevitFile::open(&args[1])?;
    let ids: std::collections::BTreeSet<u64> = args[2..].iter().map(|s| s.parse()).collect::<Result<_, _>>()?;
    let options = rvt::native_document::Options {
        selected_ids: ids,
        channels: [101, 102, 103].into_iter().collect(),
        ..Default::default()
    };
    let mut records = Vec::new();
    let summary = rvt::native_document::extract_graphs(&mut file, &options, |record| {
        records.push(serde_json::to_value(record)?);
        Ok(())
    })?;
    let mut graphics_file = rvt::RevitFile::open(&args[1])?;
    let scene = rvt::native_saved_scene::extract(&mut graphics_file, &options)?;
    println!("{}", serde_json::to_string_pretty(&serde_json::json!({
        "records": records, "summary": summary, "scene": scene
    }))?);
    Ok(())
}
