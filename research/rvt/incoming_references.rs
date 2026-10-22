// Decode only byte-prefiltered, independently routed object bodies. No source modifications.
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args().collect();
    let registry = rvt::schema_registry::parse(&std::fs::read(&args[1])?)?;
    let catalog: rvt::native_extensible_storage::Catalog = serde_json::from_slice(&std::fs::read(&args[2])?)?;
    let paths: Vec<String> = serde_json::from_slice(&std::fs::read(&args[3])?)?;
    let mut records = Vec::new();
    for path in paths {
        let body = std::fs::read(&path)?;
        let result = rvt::native_parameters::decode_graph_with_catalog(&body, &registry, &rvt::native_parameters::GraphLimits { max_values: 10_000_000, max_objects: 500_000, ..Default::default() }, Some(&catalog));
        let value = match result {
            Ok(graph) => serde_json::json!({"complete":graph.consumed_bytes == body.len(),"graph":graph}),
            Err(error) => serde_json::json!({"complete":false,"diagnostic":error.to_string()}),
        };
        records.push(value);
    }
    println!("{}",serde_json::to_string(&serde_json::json!({"records":records,"declarations":registry.classes}))?);
    Ok(())
}
