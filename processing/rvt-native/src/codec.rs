//! Page framing inferred from licensed RVT fixtures and historical snapshots.
//! Dimension selection outside the observed corpus is experimental.
use crate::{
    final_page::{self, Layout, GENERATORS},
    paged::{self, PAYLOAD, STORED},
};
use std::io::{Error, ErrorKind, Result};
fn invalid(message: &str) -> Error {
    Error::new(ErrorKind::InvalidData, message)
}
fn bit(data: &[u8], i: usize) -> bool {
    data.get(i / 8).is_some_and(|b| (b >> (i % 8)) & 1 != 0)
}
fn set(data: &mut [u8], i: usize) {
    data[i / 8] |= 1 << (i % 8);
}
fn size(l: Layout) -> usize {
    (l.lanes * l.codeword_bits).div_ceil(8)
}
fn available(l: Layout) -> usize {
    l.data_bits() - (l.degree() + 1).max(7)
}
fn dimensions(length: usize) -> Result<Vec<Layout>> {
    if length == 0 || length > PAYLOAD {
        return Err(invalid("payload length outside 1..64896"));
    }
    let mut out = Vec::new();
    for generator in GENERATORS {
        let m = 15 - generator.leading_zeros() as usize;
        let k = (1 << m) - 1 - m;
        for reserve in [m + 1, (m + 1).max(7)] {
            let needed = length * 8 + reserve;
            let (lanes, rows) = if needed <= k * 65 {
                (65, needed.div_ceil(65))
            } else {
                (needed.div_ceil(k) | 1, k)
            };
            if lanes <= 255 {
                out.push(Layout {
                    lanes,
                    codeword_bits: rows + m,
                    generator,
                });
            }
        }
    }
    out.sort_by_key(|l| (size(*l), l.lanes, l.codeword_bits, l.generator));
    out.dedup();
    Ok(out)
}
fn padded(payload: &[u8], l: Layout) -> Result<Vec<u8>> {
    let a = available(l);
    let Some(padding) = a.div_ceil(8).checked_sub(payload.len()).map(|n| n * 8) else {
        return Err(invalid("payload exceeds layout"));
    };
    if padding >= 1 << (l.degree() + 1).max(7) || (a..payload.len() * 8).any(|i| bit(payload, i)) {
        return Err(invalid("payload overlaps length field"));
    }
    let mut data = vec![0; l.data_bits().div_ceil(8)];
    data[..payload.len()].copy_from_slice(payload);
    for i in 0..(l.degree() + 1).max(7) {
        if (padding >> i) & 1 != 0 {
            set(&mut data, a + i);
        }
    }
    Ok(data)
}
pub fn layout(payload: &[u8]) -> Result<Layout> {
    dimensions(payload.len())?
        .into_iter()
        .find(|l| padded(payload, *l).is_ok())
        .ok_or_else(|| invalid("no supported layout fits payload"))
}
pub fn encode_final_with_layout(payload: &[u8], l: Layout) -> Result<Vec<u8>> {
    if payload.is_empty()
        || payload.len() > PAYLOAD
        || !GENERATORS.contains(&l.generator)
        || !(65..=255).contains(&l.lanes)
        || l.lanes.is_multiple_of(2)
        || l.codeword_bits <= l.degree()
        || l.codeword_bits >= (1 << l.degree())
        || (l.lanes != 65 && l.codeword_bits != (1 << l.degree()) - 1)
    {
        return Err(invalid("unsupported final-page layout"));
    }
    final_page::encode(&padded(payload, l)?, l)
}
pub fn encode_final(payload: &[u8]) -> Result<Vec<u8>> {
    encode_final_with_layout(payload, layout(payload)?)
}
fn unpack(data: &[u8], l: Layout) -> Result<Vec<u8>> {
    let a = available(l);
    let padding = (a..l.data_bits())
        .enumerate()
        .fold(0, |v, (j, i)| v | ((bit(data, i) as usize) << j));
    if padding % 8 != 0 {
        return Err(invalid("fractional padding length"));
    }
    let length = a
        .div_ceil(8)
        .checked_sub(padding / 8)
        .filter(|n| *n > 0)
        .ok_or_else(|| invalid("invalid padding length"))?;
    if (length * 8..a).any(|i| bit(data, i)) {
        return Err(invalid("nonzero padding"));
    }
    let mut body = data[..length].to_vec();
    for i in a..length * 8 {
        body[i / 8] &= !(1 << (i % 8));
    }
    Ok(body)
}
pub fn decode_final(stored: &[u8]) -> Result<Vec<u8>> {
    let mut canonical = Vec::new();
    let mut alternatives = Vec::new();
    for (l, data) in final_page::candidates(stored)? {
        let Ok(body) = unpack(&data, l) else { continue };
        if encode_final_with_layout(&body, l).is_ok_and(|encoded| encoded == stored) {
            if layout(&body)? == l {
                canonical.push(body.clone());
            }
            alternatives.push(body);
        }
    }
    // The encoder policy disambiguates degenerate zero pages. Historical
    // layouts outside that policy require a unique exact interpretation.
    let mut matches = if canonical.is_empty() {
        alternatives
    } else {
        canonical
    };
    if matches.len() != 1 {
        return Err(invalid("invalid or ambiguous final-page framing"));
    }
    Ok(matches.remove(0))
}

pub fn encode(payload: &[u8]) -> Result<Vec<u8>> {
    let mut out = Vec::new();
    for block in payload.chunks(PAYLOAD) {
        out.extend(encode_final(block)?);
    }
    Ok(out)
}
pub fn decode(stored: &[u8]) -> Result<Vec<u8>> {
    let mut out = Vec::new();
    let mut chunks = stored.chunks(STORED).peekable();
    while let Some(page) = chunks.next() {
        if chunks.peek().is_none() {
            out.extend(decode_final(page)?);
        } else {
            out.extend(paged::decode(page)?);
        }
    }
    Ok(out)
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn boundaries_and_zero_payloads() {
        for n in (0..130).chain([
            182,
            294,
            774,
            1890,
            4096,
            16000,
            42093,
            64895,
            PAYLOAD,
            PAYLOAD + 1,
            2 * PAYLOAD,
        ]) {
            for zero in [true, false] {
                let data: Vec<u8> = (0..n)
                    .map(|i| {
                        if zero {
                            0
                        } else {
                            (i * 37 + i / 251 + 191) as u8
                        }
                    })
                    .collect();
                let stored = encode(&data).unwrap();
                assert_eq!(decode(&stored).unwrap(), data, "size {n}");
            }
        }
    }
    #[test]
    fn historical_noncanonical_layouts() {
        for (n, lanes, codeword_bits, generator) in [
            (308, 65, 44, 0x43),
            (739, 65, 98, 0x83),
            (1697, 65, 218, 0x211),
            (4136, 67, 511, 0x211),
        ] {
            let l = Layout {
                lanes,
                codeword_bits,
                generator,
            };
            let mut data: Vec<_> = (0..n).map(|i| (i * 37 + i / 251) as u8).collect();
            data[n - 1] = 0;
            assert_ne!(layout(&data).unwrap(), l);
            let stored = encode_final_with_layout(&data, l).unwrap();
            assert_eq!(decode_final(&stored).unwrap(), data);
            let mut bad = stored;
            bad[0] ^= 1;
            assert!(decode_final(&bad).is_err());
        }
    }
    #[test]
    fn rejects_padded_interior_page() {
        let mut bad = encode(&vec![0; PAYLOAD - 1]).unwrap();
        bad.extend(encode(b"next").unwrap());
        assert!(decode(&bad).is_err());
    }
    #[test]
    fn rejects_corruption() {
        let data = encode(b"payload").unwrap();
        for i in 0..data.len() * 8 {
            let mut bad = data.clone();
            bad[i / 8] ^= 1 << (i % 8);
            assert!(decode(&bad).is_err());
        }
    }
}
