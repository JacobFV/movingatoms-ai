fn main()->Result<(),Box<dyn std::error::Error>>{
 let a:Vec<_>=std::env::args().collect();
 if a[1]=="schema" {
  let r=rvt::schema_registry::parse(&std::fs::read(&a[2])?)?;
  println!("{}",serde_json::to_string(&r.classes)?);return Ok(())
 }
 if a[1]=="decode" {
  let r=rvt::schema_registry::parse(&std::fs::read(&a[2])?)?;
  let g=rvt::native_parameters::decode_graph(&std::fs::read(&a[3])?,&r)?;
  println!("{}",serde_json::to_string(&g)?);return Ok(())
 }
 let mut file=rvt::RevitFile::open(&a[1])?;
 let options=rvt::native_document::Options{channels:[102].into_iter().collect(),selected_ids: a.get(2).map(|s|s.parse::<u64>()).transpose()?.into_iter().collect(), selected_classes:if a.len()>2 {Default::default()} else {["GStyleElem","MaterialElem","BasicWallType","Level","ProjectPhase"].into_iter().map(String::from).collect()},..Default::default()};
 let mut records=Vec::new();
 let summary=rvt::native_document::extract_graphs(&mut file,&options,|r|{records.push(r);Ok(())})?;
 if summary.current_records_outside_route!=0 || summary.unsupported_graph_records!=0 {return Err("context requires complete exact-routed graphs".into())}
 println!("{}",serde_json::to_string(&serde_json::json!({"records":records,"summary":summary}))?);Ok(())
}
