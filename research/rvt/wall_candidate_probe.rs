// Clean-room inventory of constructible-looking classes; no RVT mutation.
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args().collect();
    if args[1] == "material-route" {
        let mut file=rvt::RevitFile::open(&args[2])?;
        let ids=[20826,133210].into_iter().collect();
        let orientations=rvt::partition_compound_structure::scan_wall_orientations(&mut file,2024,&ids)?;
        let lines=rvt::partition_compound_structure::scan_wall_lines(&mut file,2024,&ids)?;
        let rows:Vec<_>=ids.iter().map(|id|serde_json::json!({"id":id,"orientation":orientations.get(id).map(|o|serde_json::json!({"location_line":o.location_line,"word":o.word,"flip":o.flip})),"has_line":lines.contains_key(id)})).collect();
        println!("{}",serde_json::to_string_pretty(&rows)?);return Ok(());
    }
    if args[1] == "projection" {
        use rvt::ifc::{Exporter,RvtDocExporter};
        use rvt::ifc::entities::IfcEntity;
        let mut file=rvt::RevitFile::open(&args[2])?;
        let model=RvtDocExporter.export(&mut file)?;
        if let Some(output)=args.get(3) {
            use std::io::Write;
            let step=rvt::ifc::step_writer::write_step_with_options(&model,&rvt::ifc::step_writer::StepOptions{timestamp:Some(1792627200)});
            std::fs::OpenOptions::new().write(true).create_new(true).open(output)?.write_all(step.as_bytes())?;
        }
        let entities:Vec<_>=model.entities.iter().filter(|e| matches!(e, IfcEntity::BuildingElement{..})).collect();
        let native_ids:std::collections::BTreeMap<_,_>=model.entities.iter().enumerate().filter_map(|(i,e)|match e {
            IfcEntity::BuildingElement{type_guid:Some(id),..}=>model.global_ids.elements.get(&i).map(|guid|(id,guid)),_=>None
        }).collect();
        println!("{}",serde_json::to_string_pretty(&serde_json::json!({"entities":entities,"layers":model.element_layers,"native_ids":native_ids}))?);
        return Ok(());
    }
    if args[1] == "incoming" {
        fn visit(v:&serde_json::Value, path:String, id:i64, out:&mut Vec<String>) {
            match v {
                serde_json::Value::Object(m)=>for (k,v) in m {
                    let p=format!("{path}.{k}");
                    if matches!(k.as_str(),"m_id64"|"m_elementId") && v.as_i64()==Some(id) {out.push(p.clone());}
                    visit(v,p,id,out);
                },
                serde_json::Value::Array(a)=>for (i,v) in a.iter().enumerate(){visit(v,format!("{path}[{i}]"),id,out);},
                _=>{}
            }
        }
        let mut file=rvt::RevitFile::open(&args[2])?;
        let id=args[3].parse::<i64>()?;
        let options=rvt::native_document::Options{channels:[101,102,103].into_iter().collect(),..Default::default()};
        let mut hits=Vec::new();
        let summary=rvt::native_document::extract_graphs(&mut file,&options,|record|{
            if let Some(g)=&record.graph {
                for (i,o) in g.objects.iter().enumerate() {
                    let mut paths=Vec::new();visit(&o.fields,String::new(),id,&mut paths);
                    if !paths.is_empty(){hits.push(serde_json::json!({"element":record.identity.element_id,"channel":record.channel,"class":record.class_name,"object":i,"object_class":o.class_name,"paths":paths}));}
                }
            }
            Ok(())
        })?;
        println!("{}",serde_json::to_string_pretty(&serde_json::json!({"hits":hits,"summary":summary}))?);
        return Ok(());
    }
    if args[1] == "geometry" {
        use rvt::ifc::{Exporter,RvtDocExporter};
        use rvt::ifc::entities::IfcEntity;
        let mut file=rvt::RevitFile::open(&args[2])?;
        let model=RvtDocExporter.export(&mut file)?;
        let selected:Vec<_>=model.entities.iter().filter(|e| matches!(e, IfcEntity::BuildingElement{type_guid:Some(id),..} if id == &args[3])).collect();
        if selected.len()!=1 {return Err("expected one IFC element".into());}
        println!("{}",serde_json::to_string_pretty(&serde_json::json!({"entity":selected[0],"layers":model.element_layers.get(&args[3].parse::<u32>()?)}))?);
        return Ok(());
    }
    if args[1] == "identity" {
        let registry = rvt::schema_registry::parse(&std::fs::read(&args[2])?)?;
        let episodes = rvt::native_index::creation_episodes(&std::fs::read(&args[4])?, &registry)?;
        let index = rvt::native_index::parse(&std::fs::read(&args[3])?, &registry, &episodes)?;
        println!("{}", serde_json::to_string_pretty(&index)?);
        return Ok(());
    }
    if args[1] == "decode" {
        let schema = std::fs::read(&args[2])?;
        let registry = rvt::schema_registry::parse(&schema)?;
        let body = std::fs::read(&args[3])?;
        let catalog: Option<rvt::native_extensible_storage::Catalog> = args.get(4).map(|p| {
            let bytes = std::fs::read(p)?; Ok::<_,Box<dyn std::error::Error>> (serde_json::from_slice(&bytes)?)
        }).transpose()?;
        let graph = rvt::native_parameters::decode_graph_with_catalog(&body, &registry, &Default::default(), catalog.as_ref())?;
        let roots: Vec<_> = graph.objects.iter().filter(|o| o.start == 2 || matches!(o.class_name.as_str(), "StructuralElemSetTracking")).map(|o|
            rvt::native_parameters::decode_object_fields(&body, &registry, o.start, o.class_tag)
        ).collect::<Result<_,_>>()?;
        let declarations = &registry.classes;
        println!("{}", serde_json::to_string_pretty(&serde_json::json!({"graph":graph,"objects":roots,"declarations":declarations}))?);
        return Ok(());
    }
    let mut file = rvt::RevitFile::open(std::path::Path::new(&args[1]))?;
    let options = rvt::native_document::Options {
        
        channels: [101,102,103].into_iter().collect(),
        selected_ids: args.get(2).filter(|s| !s.starts_with("class:")).map(|s| s.parse()).transpose()?.into_iter().collect(),
        selected_classes: args.get(2).and_then(|s| s.strip_prefix("class:")).map(String::from).into_iter().collect(),
        ..Default::default()
    };
    let mut selected = std::collections::BTreeMap::new();
    let summary = rvt::native_document::extract_graphs(&mut file, &options, |record| {
        let key = (record.class_name.clone(), record.channel, if args.get(2).is_some_and(|s| s.starts_with("class:")) {record.identity.element_id} else {0});
        let keep = selected.get(&key).map_or(true, |old: &rvt::native_document::Record| record.source.body_bytes < old.source.body_bytes);
        if keep { selected.insert(key, record); }
        Ok(())
    })?;
    println!("{}", serde_json::to_string_pretty(&serde_json::json!({"records":selected.into_values().collect::<Vec<_>>(),"summary":summary}))?);
    Ok(())
}
