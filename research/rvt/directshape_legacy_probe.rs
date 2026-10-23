// Historical physical records only: no current routing or version substitution.
use anyhow::{Result,ensure};
use serde_json::json;
fn main()->Result<()> {
 let a:Vec<_>=std::env::args().collect();
 let registry=rvt::schema_registry::parse(&std::fs::read(&a[1])?)?;
 let mut records=Vec::new(); let mut stats=Vec::new();
 for file in &a[2..] {
  let bytes=std::fs::read(file)?;
  let result=rvt::native_segments::walk(&bytes,&registry,268435456,|source,body|{
   if ![101,102,103].contains(&source.channel) {return Ok(())}
   let header=if source.channel==101 {8}else{12};let mut pos=0;let mut count=0;let mut total=0;
   while pos<body.len(){
    ensure!(pos+header+4<=body.len(),"truncated legacy header");
    let id=u32::from_le_bytes(body[pos..pos+4].try_into()?);
    let len=u32::from_le_bytes(body[pos+header-4..pos+header].try_into()?)as usize;
    let start=pos+header;let end=start+len;
    ensure!(end+4<=body.len(),"legacy body bounds");
    ensure!(u32::from_le_bytes(body[end..end+4].try_into()?)as usize==len,"dual length mismatch");
    let tag=u16::from_le_bytes(body[start..start+2].try_into()?);
    let class=registry.class(tag).map(|c|c.name.as_str()).unwrap_or("UNKNOWN");
    records.push((id,source.channel,file.clone(),source.clone(),class.to_string(),body[start..end].to_vec()));
    pos=end+4;count+=1;total+=len;
   }
   ensure!(count==source.declared_objects&&total as u64+4*count==source.declared_body_bytes,"legacy group accounting mismatch: count {count}/{}, body {total}/{}, channel {}",source.declared_objects,source.declared_body_bytes,source.channel);Ok(())
  });
  stats.push(json!({"stream_file":file,"statistics":result.as_ref().ok(),"diagnostic":result.as_ref().err().map(|e|e.to_string())}));
 }
 let ids:std::collections::BTreeSet<_>=records.iter().filter(|r|r.4=="DirectShape"||r.4=="DirectShapeType").map(|r|r.0).collect();
 let rows:Vec<_>=records.iter().filter(|r|ids.contains(&r.0)).map(|r|{
 let g=rvt::native_parameters::decode_graph_with_limits(&r.5,&registry,&rvt::native_parameters::GraphLimits{max_values:10_000_000,max_objects:500_000,..Default::default()});
 json!({"element_id":r.0,"channel":r.1,"stream_file":r.2,"group":r.3,"root_class":r.4,"body_bytes":r.5.len(),"body_hex":r.5.iter().map(|v|format!("{v:02x}")).collect::<String>(),"graph":g.as_ref().ok(),"diagnostic":g.as_ref().err().map(|e|e.to_string())})}).collect();
 println!("{}",serde_json::to_string_pretty(&json!({"historical_only":true,"id_width_bytes":4,"physical_record_count":records.len(),"statistics":stats,"records":rows}))?);Ok(())
}
