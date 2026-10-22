// Independent current-record routing and full graph decode through pinned rvt-rs.
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args().collect();
    let id: u64 = args[2].parse()?;
    let mut file = rvt::RevitFile::open(std::path::Path::new(&args[1]))?;
    let options = rvt::native_document::Options {
        selected_ids: [id].into_iter().collect(),
        ..Default::default()
    };
    let mut records = Vec::new();
    let summary = rvt::native_document::extract_graphs(&mut file, &options, |record| {
        records.push(record);
        Ok(())
    })?;
    if records.len() != 1 || records[0].graph.is_none() || summary.current_records_outside_route != 0 {
        return Err("expected one complete graph with an exact revision route".into());
    }
    println!("{}", serde_json::to_string_pretty(&serde_json::json!({
        "record": records[0], "summary": summary
    }))?);
    Ok(())
}
