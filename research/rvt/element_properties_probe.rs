fn main()->Result<(),Box<dyn std::error::Error>>{
 let a:Vec<String>=std::env::args().collect();
 if a[1]=="saved" {
  let mut file=rvt::RevitFile::open(&a[2])?;
  let options=rvt::native_document::Options{selected_ids:[a[3].parse::<u64>()?].into_iter().collect(),channels:[101,102,103].into_iter().collect(),..Default::default()};
  let mut records=Vec::new();
  let summary=rvt::native_document::extract_graphs(&mut file,&options,|record|{records.push(serde_json::to_value(record)?);Ok(())})?;
  println!("{}",serde_json::json!({"records":records,"summary":summary}));return Ok(())
 }
 if a[1]=="esglobal" {
  let registry=rvt::schema_registry::parse(&std::fs::read(&a[2])?)?;
  let body=std::fs::read(&a[3])?;
  let (catalog,source)=rvt::native_es_catalog::decode(&body,&registry)?;
  let graph=rvt::native_parameters::decode_graph_with_limits(&body[..body.len()-4],&registry,
    &rvt::native_parameters::GraphLimits{max_values:2_000_000,..Default::default()})?;
  println!("{}",serde_json::json!({"graph":graph,"catalog":catalog,"source":source,"declarations":registry.classes}));return Ok(())
 }
 if a[1]=="esdecode" {
  let registry=rvt::schema_registry::parse(&std::fs::read(&a[2])?)?;
  let catalog:rvt::native_extensible_storage::Catalog=serde_json::from_slice(&std::fs::read(&a[4])?)?;
  let graph=rvt::native_parameters::decode_graph_with_catalog(&std::fs::read(&a[3])?,&registry,&Default::default(),Some(&catalog))?;
  println!("{}",serde_json::to_string(&graph)?);return Ok(())
 }
 if a[1]=="schema" {
  let registry=rvt::schema_registry::parse(&std::fs::read(&a[2])?)?;
  println!("{}",serde_json::to_string(&registry.classes)?);return Ok(())
 }
 if a[1]=="decode" {
  let registry=rvt::schema_registry::parse(&std::fs::read(&a[2])?)?;
  let graph=rvt::native_parameters::decode_graph(&std::fs::read(&a[3])?,&registry)?;
  println!("{}",serde_json::to_string(&graph)?);return Ok(())
 }
 let mut file=rvt::RevitFile::open(&a[1])?;
 let options=rvt::native_document::Options{channels:[102].into_iter().collect(),selected_classes:["SWall".into()].into_iter().collect(),..Default::default()};
 let mut items=Vec::new();let mut examples=Vec::new();let mut null_example=None;
 let summary=rvt::native_document::extract_graphs(&mut file,&options,|record|{
   if let Some(graph)=&record.graph{
     let sets:Vec<_>=graph.objects.iter().filter(|o|o.class_name=="ParamValueSetAString").collect();
     let cells:Vec<_>=graph.objects.iter().filter(|o|o.class_name=="ESEntityCell").map(|o|&o.fields).collect();
     items.push(serde_json::json!({"id":record.identity.element_id,"source":record.source,
        "string_pointer":graph.objects[0].fields["m_pParamValueSetAString"],"string_sets":sets,"es_cells":cells}));
     if record.identity.element_id==20826 {null_example=Some(serde_json::to_value(&record)?);}
     if !sets.is_empty() && examples.len()<5 {examples.push(record);}
   }Ok(())
 })?;
 println!("{}",serde_json::to_string(&serde_json::json!({"items":items,"examples":examples,"null_example":null_example,"summary":summary}))?);Ok(())
}
