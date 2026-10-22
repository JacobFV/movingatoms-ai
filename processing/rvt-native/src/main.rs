use ma_rvt_native::{codec, paged, writer};
use std::{env, fs, path::Path};
fn main() {
    if let Err(error) = run() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}
fn run() -> writer::Result<()> {
    let args: Vec<_> = env::args().skip(1).collect();
    match args.iter().map(String::as_str).collect::<Vec<_>>().as_slice() {
        ["verify", input] => println!("{}", serde_json::to_string_pretty(&writer::verify(Path::new(input))?)?),
        ["patch", input, output, manifest] => {
            let manifest_path = Path::new(manifest);
            let plan = serde_json::from_slice(&fs::read(manifest_path)?)?;
            let base = manifest_path.parent().unwrap_or(Path::new("."));
            let report = writer::patch(Path::new(input), Path::new(output), &plan, base)?;
            println!("{}", serde_json::to_string_pretty(&report)?);
        }
        [operation @ ("encode-pages" | "decode-pages" | "encode-stream" | "decode-stream"), input, output] => {
            let data = fs::read(input)?;
            let result = match *operation {
                "encode-stream" => codec::encode(&data)?,
                "decode-stream" => codec::decode(&data)?,
                "encode-pages" => paged::encode(&data)?,
                _ => paged::decode(&data)?,
            };
            use std::io::Write;
            fs::OpenOptions::new().write(true).create_new(true).open(output)?.write_all(&result)?;
        }
        _ => return Err("usage: ma-rvt-native verify INPUT | patch INPUT OUTPUT MANIFEST | encode-stream INPUT OUTPUT | decode-stream INPUT OUTPUT | encode-pages INPUT OUTPUT | decode-pages INPUT OUTPUT".into()),
    }
    Ok(())
}
