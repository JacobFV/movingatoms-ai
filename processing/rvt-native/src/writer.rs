//! Transactional replacement of existing logical stream bytes. The caller owns
//! compression/member framing and semantic invariants; this layer owns parity,
//! CFB allocation, preconditions, unchanged-stream verification and atomic output.
use crate::{final_page, paged};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::{
    collections::BTreeMap,
    fs::{self, File},
    io::{Read, Write},
    path::{Path, PathBuf},
};

pub type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Manifest {
    pub input_sha256: String,
    pub patches: Vec<Patch>,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Patch {
    pub stream: String,
    pub expected_stored_sha256: String,
    pub new_unpaged_file: PathBuf,
}
#[derive(Serialize)]
pub struct Report {
    pub input_sha256: String,
    pub output_sha256: String,
    pub changed_streams: Vec<String>,
    pub streams_verified: usize,
    pub parity_pages_verified: usize,
    pub final_pages_verified: usize,
    pub validation: &'static str,
    pub revit_openability: &'static str,
}

pub fn hash(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

fn file_hash(path: &Path) -> Result<String> {
    let mut file = File::open(path)?;
    let mut h = Sha256::new();
    let mut buf = [0; 65536];
    loop {
        let n = file.read(&mut buf)?;
        if n == 0 {
            break;
        }
        h.update(&buf[..n]);
    }
    Ok(format!("{:x}", h.finalize()))
}

fn stream_bytes(cfb: &mut cfb::CompoundFile<File>, name: &str) -> Result<Vec<u8>> {
    let mut data = Vec::new();
    cfb.open_stream(name)?.read_to_end(&mut data)?;
    Ok(data)
}

fn inventory(path: &Path) -> Result<(BTreeMap<String, String>, usize, usize)> {
    let mut file = cfb::open(path)?;
    let names: Vec<_> = file
        .walk()
        .filter(|entry| entry.is_stream())
        .map(|entry| entry.path().to_string_lossy().into_owned())
        .collect();
    let mut hashes = BTreeMap::new();
    let mut pages = 0;
    let mut finals = 0;
    for name in names {
        let data = stream_bytes(&mut file, &name)?;
        if paged::is_paged(&name) {
            paged::decode(&data)?;
            pages += data.len() / paged::STORED;
            let tail = &data[data.len() / paged::STORED * paged::STORED..];
            if !tail.is_empty() {
                final_page::decode(tail)?;
                finals += 1;
            }
        }
        hashes.insert(name, hash(&data));
    }
    Ok((hashes, pages, finals))
}

pub fn verify(path: &Path) -> Result<Report> {
    let (streams, pages, finals) = inventory(path)?;
    let sha = file_hash(path)?;
    Ok(Report {
        input_sha256: sha.clone(),
        output_sha256: sha,
        changed_streams: vec![],
        streams_verified: streams.len(),
        parity_pages_verified: pages,
        final_pages_verified: finals,
        validation: "CFB streams and page parity only",
        revit_openability: "not_tested",
    })
}

pub fn patch(input: &Path, output: &Path, manifest: &Manifest, base: &Path) -> Result<Report> {
    if output.exists() {
        return Err("output already exists; refusing overwrite".into());
    }
    let parent = output
        .parent()
        .filter(|p| !p.as_os_str().is_empty())
        .unwrap_or(Path::new("."));
    let temp = tempfile::NamedTempFile::new_in(parent)?;
    fs::copy(input, temp.path())?;
    let input_sha = file_hash(temp.path())?;
    if input_sha != manifest.input_sha256 {
        return Err("input SHA-256 precondition failed".into());
    }
    let (mut expected, _, _) = inventory(temp.path())?;
    let mut replacements = BTreeMap::new();
    for p in &manifest.patches {
        let name = format!("/{}", p.stream.trim_start_matches('/'));
        if name.contains("//") || name.split('/').any(|s| s == "." || s == "..") {
            return Err(format!("noncanonical stream path: {name}").into());
        }
        let old = expected
            .get(&name)
            .ok_or_else(|| format!("stream not found: {name}"))?;
        if old != &p.expected_stored_sha256 {
            return Err(format!("stream SHA-256 precondition failed: {name}").into());
        }
        let logical = fs::read(base.join(&p.new_unpaged_file))?;
        let stored = if paged::is_paged(&name) {
            paged::encode(&logical)?
        } else {
            logical
        };
        if replacements.insert(name.clone(), stored).is_some() {
            return Err(format!("duplicate patch: {name}").into());
        }
    }
    let mut changed = Vec::new();
    {
        let mut file = cfb::open_rw(temp.path())?;
        for (name, stored) in replacements {
            let new_hash = hash(&stored);
            if expected[&name] == new_hash {
                continue;
            }
            // open_stream preserves entry metadata; set_len handles mini/FAT growth.
            let mut stream = file.open_stream(&name)?;
            stream.set_len(stored.len() as u64)?;
            stream.write_all(&stored)?;
            stream.flush()?;
            expected.insert(name.clone(), new_hash);
            changed.push(name);
        }
        file.flush()?;
    }
    let (actual, pages, finals) = inventory(temp.path())?;
    if actual != expected {
        return Err("post-write stream inventory/hash verification failed".into());
    }
    temp.as_file().sync_all()?;
    let output_sha = file_hash(temp.path())?;
    temp.persist_noclobber(output)?;
    File::open(parent)?.sync_all()?;
    Ok(Report {
        input_sha256: input_sha,
        output_sha256: output_sha,
        changed_streams: changed,
        streams_verified: actual.len(),
        parity_pages_verified: pages,
        final_pages_verified: finals,
        validation: "CFB streams, page parity, and unchanged-stream SHA-256",
        revit_openability: "not_tested",
    })
}
