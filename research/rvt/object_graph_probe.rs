// Independent validation through the pinned public clean-room reader.
fn main() {
    let args: Vec<_> = std::env::args().collect();
    let schema = std::fs::read(&args[1]).unwrap();
    let registry = rvt::schema_registry::parse(&schema).unwrap();
    let body = std::fs::read(&args[2]).unwrap();
    let graph = rvt::native_parameters::decode_graph(&body, &registry).unwrap();
    assert_eq!(graph.consumed_bytes, body.len());
    println!("{}", serde_json::to_string_pretty(&graph).unwrap());
}
