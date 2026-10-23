// Independently decode diagnostic mesh bodies under explicit resource bounds.
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = std::env::args().collect();
    let schema = std::fs::read(&args[1])?;
    let body = std::fs::read(&args[2])?;
    let registry = rvt::schema_registry::parse(&schema)?;
    let limits = rvt::native_parameters::GraphLimits { max_values: 1_000_000, max_objects: 100, max_depth: 128 };
    let graph = rvt::native_parameters::decode_graph_with_catalog(&body, &registry, &limits, None)?;
    let graphics = rvt::native_saved_mesh::graphics(&graph);
    println!("{}", serde_json::to_string(&serde_json::json!({"graph":graph,"graphics":graphics}))?);
    Ok(())
}
