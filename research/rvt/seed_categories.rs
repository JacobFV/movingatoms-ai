// Independent saved-category/style/material inventory; no proprietary code.
fn main()->Result<(),Box<dyn std::error::Error>>{
 let a:Vec<_>=std::env::args().collect();let mut f=rvt::RevitFile::open(&a[1])?;
 let options=rvt::native_document::Options{channels:[102].into_iter().collect(),
  selected_classes:["GStyleElem","MaterialElem"].into_iter().map(String::from).collect(),..Default::default()};
 let mut styles=Vec::new();let mut materials=Vec::new();
 let summary=rvt::native_document::extract_graphs(&mut f,&options,|r|{
  let g=r.graph.as_ref().ok_or_else(||std::io::Error::other("incomplete context graph"))?;
  let root=&g.objects[0];let id=r.identity.element_id;
  if root.class_name=="GStyleElem"{
   let style=g.objects.iter().find(|o|o.class_name=="GStyle").ok_or_else(||std::io::Error::other("missing GStyle"))?;
   styles.push(serde_json::json!({"id":id,"class_name":root.class_name,"root_fields":root.fields,"style_fields":style.fields,"identity":r.identity,"source":r.source}));
  }else{
   let mat=g.objects.iter().find(|o|o.class_name=="Material").ok_or_else(||std::io::Error::other("missing Material"))?;
   materials.push(serde_json::json!({"id":id,"class_name":root.class_name,"name":mat.fields["m_name"],"color":mat.fields["m_color"],"identity":r.identity,"source":r.source}));
  }Ok(())
 })?;
 if summary.current_records_outside_route!=0||summary.unsupported_graph_records!=0{return Err("requires exact complete context records".into())}
 let mappings:Vec<_>=rvt::ifc::category_map::MAPPINGS.iter().map(|m|serde_json::json!({"revit_class":m.revit_class,"ifc_type":m.ifc_type,"predefined_type":m.predefined_type})).collect();
 println!("{}",serde_json::to_string(&serde_json::json!({"styles":styles,"materials":materials,"public_ifc_mappings":mappings,
  "public_category_names":rvt::partition_element_records::BUILTIN_CATEGORY_NAMES,
  "summary":{"indexed_elements":summary.indexed_elements,"records":summary.emitted_records,"complete_graphs":summary.complete_graph_records,"off_route":summary.current_records_outside_route,"schema_sha256":summary.schema_sha256}}))?);Ok(())
}
