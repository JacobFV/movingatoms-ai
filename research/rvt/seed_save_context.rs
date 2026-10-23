fn main()->Result<(),Box<dyn std::error::Error>>{
 let args:Vec<_>=std::env::args().collect();let schema=std::fs::read(&args[1])?;let raw=std::fs::read(&args[2])?;
 let registry=rvt::schema_registry::parse(&schema)?;let graph=rvt::native_parameters::decode_graph(&raw,&registry)?;
 let selected=graph.objects.iter().filter(|o|matches!(o.class_name.as_str(),"StructuralElemSetTracking"|"DatumTracking"|"ElementTrackingData"))
 .map(|o|rvt::native_parameters::decode_object_fields(&raw,&registry,o.start,o.class_tag)).collect::<Result<Vec<_>,_>>()?;
 println!("{}",serde_json::to_string(&serde_json::json!({"graph":graph,"objects":selected}))?);Ok(())
}
