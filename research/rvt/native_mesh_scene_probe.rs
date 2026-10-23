// Public reader only: decode a diagnostic GElement/GPolyMesh body and tessellate it.
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = std::env::args().collect();
    let schema = std::fs::read(&args[1])?;
    let body = std::fs::read(&args[2])?;
    let registry = rvt::schema_registry::parse(&schema)?;
    let graph = rvt::native_parameters::decode_graph_with_catalog(&body, &registry, &Default::default(), None)?;
    let graphics = rvt::native_saved_mesh::graphics(&graph);
    println!("{}", serde_json::to_string(&graphics)?);
    Ok(())
}
