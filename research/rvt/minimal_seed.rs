// Read only licensed candidate seeds using the pinned public clean-room reader.
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args().collect();
    let mut file = rvt::RevitFile::open(std::path::Path::new(&args[1]))?;
    let basic = file.basic_file_info()?;
    let version = basic.version;
    let options = rvt::native_document::Options { channels: [101,102,103].into_iter().collect(), ..Default::default() };
    let mut selected = Vec::new();
    let result = rvt::native_document::extract_graphs(&mut file, &options, |record| {
        if record.channel == 102 && matches!(record.class_name.as_deref(),Some("Level"|"BasicWallType"|"ProjectPhase"|"DataStorage")) {
            selected.push(serde_json::json!({"element_id":record.identity.element_id,"unique_id":record.identity.unique_id,
                "class_name":record.class_name,"source":record.source,"status":record.status,
                "root_fields":record.graph.as_ref().and_then(|g|g.objects.first()).map(|o|&o.fields),
                "graph_objects":record.graph.as_ref().map(|g|g.objects.len()),"saved_metadata":record.saved_metadata}));
        }
        Ok(())
    });
    let output = match result {
        Ok(summary) => serde_json::json!({"revit_version":version,"summary":{
            "indexed_elements":summary.indexed_elements,"emitted_records":summary.emitted_records,
            "complete_graph_records":summary.complete_graph_records,"unsupported_graph_records":summary.unsupported_graph_records,
            "current_records_outside_route":summary.current_records_outside_route,"classes":summary.classes,
            "schema_sha256":summary.schema_sha256,"budgets":summary.budgets,
            "selected_ids_without_records":summary.selected_ids_without_records},"selected_records":selected,
            "all_current_graphs_complete":summary.unsupported_graph_records==0 && summary.current_records_outside_route==0
                && summary.emitted_records==3*summary.indexed_elements}),
        Err(error) => serde_json::json!({"revit_version":version,"native_inventory_diagnostic":error.to_string(),"all_current_graphs_complete":false}),
    };
    println!("{}",serde_json::to_string(&output)?);
    Ok(())
}
