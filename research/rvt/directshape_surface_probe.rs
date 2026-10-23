// Complete body decode / public saved graphics. No current-document routing claim.
fn main()->Result<(),Box<dyn std::error::Error>> {
 let a:Vec<_>=std::env::args().collect();let(mode,schema,body)=if a[1]=="decode"{("decode",&a[2],&a[3])}else{("scene",&a[1],&a[2])};
 let registry=rvt::schema_registry::parse(&std::fs::read(schema)?)?;
 let graph=rvt::native_parameters::decode_graph_with_limits(&std::fs::read(body)?,&registry,&rvt::native_parameters::GraphLimits{max_values:10_000_000,max_objects:500_000,max_depth:128})?;
 if mode=="decode"{println!("{}",serde_json::to_string(&serde_json::json!({"graph":graph}))?);}else{println!("{}",serde_json::to_string(&rvt::native_saved_mesh::graphics(&graph))?);}Ok(())
}
