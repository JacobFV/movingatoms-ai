fn main()->Result<(),Box<dyn std::error::Error>> {
    let a:Vec<_>=std::env::args().collect();
    if a[1]=="schema" {
        let registry=rvt::schema_registry::parse(&std::fs::read(&a[2])?)?;
        println!("{}",serde_json::to_string_pretty(&registry.classes)?);return Ok(());
    }
    let mut file=rvt::RevitFile::open(&a[1])?;
    let mesh_mode=a.get(2).is_some_and(|s|s=="mesh");
    let selected=a.get(2).filter(|s|s.as_str()!="mesh").map(|s|s.parse::<u64>()).transpose()?;
    let options=rvt::native_document::Options{
        channels:[101,102,103].into_iter().collect(),
        selected_classes:if selected.is_none()&&!mesh_mode{["DirectShape".to_string(),"DirectShapeType".to_string()].into_iter().collect()}else{Default::default()},
        selected_ids:selected.into_iter().collect(),max_graph_values:10_000_000,max_graph_objects:500_000,..Default::default()
    };
    let mut rows=Vec::new();
    let summary=rvt::native_document::extract_graphs(&mut file,&options,|r|{
        if a.get(3).is_some_and(|s|s=="full"){rows.push(serde_json::to_value(r)?);return Ok(());}
        if mesh_mode&&!r.graph.as_ref().is_some_and(|g|g.objects.iter().any(|o|o.class_name=="GPolyMesh")){return Ok(());}
        if selected.is_some()||mesh_mode{
            fn trim(v:&serde_json::Value)->serde_json::Value {
                match v {
                    serde_json::Value::Array(a) if a.len()>8=>serde_json::json!({"array_length":a.len(),"first_items":a.iter().take(3).map(trim).collect::<Vec<_>>(),"truncated_for_report":true}),
                    serde_json::Value::Array(a)=>serde_json::Value::Array(a.iter().map(trim).collect()),
                    serde_json::Value::Object(o)=>serde_json::Value::Object(o.iter().map(|(k,v)|(k.clone(),trim(v))).collect()),
                    _=>v.clone()
                }
            }
            fn refs(v:&serde_json::Value,path:String,out:&mut std::collections::BTreeMap<i64,(usize,Vec<String>)>) {
                match v {
                    serde_json::Value::Object(o)=>for(k,v)in o {
                        let p=format!("{path}.{k}");
                        if k=="m_id64" {if let Some(id)=v.as_i64(){let entry=out.entry(id).or_default();entry.0+=1;if entry.1.len()<5{entry.1.push(p.clone());}}}
                        refs(v,p,out);
                    },
                    serde_json::Value::Array(a)=>for(i,v)in a.iter().enumerate(){refs(v,format!("{path}[{i}]"),out);},_=>{}
                }
            }
            let mut classes=std::collections::BTreeMap::<String,usize>::new();
            let mut samples=std::collections::BTreeMap::<String,serde_json::Value>::new();
            let mut references=std::collections::BTreeMap::new();
            if let Some(g)=&r.graph {for(i,o)in g.objects.iter().enumerate(){
                *classes.entry(o.class_name.clone()).or_default()+=1;
                samples.entry(o.class_name.clone()).or_insert_with(||serde_json::json!({"object_index":i,"object":trim(&serde_json::to_value(o).unwrap())}));
                refs(&o.fields,format!("objects[{i}]({})",o.class_name),&mut references);
            }}
            rows.push(serde_json::json!({"identity":r.identity,"channel":r.channel,"source":r.source,"status":r.status,"diagnostic":r.diagnostic,
                "objects":r.graph.as_ref().map(|g|g.objects.len()),"edges":r.graph.as_ref().map(|g|g.edges.len()),"consumed_bytes":r.graph.as_ref().map(|g|g.consumed_bytes),
                "class_counts":classes,"representative_objects":samples,"element_id_references":references}));
        }else{
            rows.push(serde_json::json!({"identity":r.identity,"channel":r.channel,"class_name":r.class_name,"source":r.source,
                "complete_graph":r.graph.is_some(),"objects":r.graph.as_ref().map(|g|g.objects.len()),"edges":r.graph.as_ref().map(|g|g.edges.len()),
                "consumed_bytes":r.graph.as_ref().map(|g|g.consumed_bytes)}));
        }
        Ok(())
    })?;
    println!("{}",serde_json::to_string_pretty(&serde_json::json!({"records":rows,"summary":summary}))?);
    Ok(())
}
