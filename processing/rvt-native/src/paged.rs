//! Byte-derived Revit parity: 255 interleaved Hamming(2047,2036) codewords.
//! Generator x^11+x^2+1; LSB-first bit packing; 12 leading/7 trailing pad bits.
use std::io::{Error, ErrorKind, Result};

pub const PAYLOAD: usize = 64_896;
pub const TRAILER: usize = 353;
pub const STORED: usize = PAYLOAD + TRAILER;
type Word = [u64; 4];

pub(crate) fn read_word(data: &[u8], offset: usize) -> Word {
    let mut word = [0; 4];
    for (limb, value) in word.iter_mut().enumerate() {
        let bit = offset + limb * 64;
        let byte = bit / 8;
        let mut wide = 0u128;
        for i in 0..9 {
            wide |= u128::from(data.get(byte + i).copied().unwrap_or(0)) << (i * 8);
        }
        *value = (wide >> (bit % 8)) as u64;
    }
    word[3] &= u64::MAX >> 1;
    word
}

pub(crate) fn write_word(data: &mut [u8], offset: usize, word: Word) {
    for (limb, value) in word.iter().enumerate() {
        let bit = offset + limb * 64;
        let wide = u128::from(*value) << (bit % 8);
        for i in 0..9 {
            if let Some(byte) = data.get_mut(bit / 8 + i) {
                *byte |= (wide >> (i * 8)) as u8;
            }
        }
    }
}

pub fn trailer(payload: &[u8]) -> Result<[u8; TRAILER]> {
    if payload.len() != PAYLOAD {
        return Err(Error::new(
            ErrorKind::InvalidInput,
            "expected 64896 payload bytes",
        ));
    }
    let mut state = [[0; 4]; 11];
    for index in 0..2036 {
        let mut feedback = read_word(payload, index * 255);
        for (f, s) in feedback.iter_mut().zip(state[10]) {
            *f ^= s;
        }
        state.rotate_right(1);
        state[0] = feedback;
        for (s, f) in state[2].iter_mut().zip(feedback) {
            *s ^= f;
        }
    }
    let mut out = [0; TRAILER];
    for (index, word) in state.iter().rev().enumerate() {
        write_word(&mut out, 12 + index * 255, *word);
    }
    Ok(out)
}

pub fn encode(data: &[u8]) -> Result<Vec<u8>> {
    let capacity = data
        .len()
        .checked_add(data.len() / PAYLOAD * TRAILER)
        .ok_or_else(|| Error::new(ErrorKind::InvalidInput, "stream size overflow"))?;
    let mut stored = Vec::with_capacity(capacity);
    for block in data.chunks(PAYLOAD) {
        stored.extend_from_slice(block);
        if block.len() == PAYLOAD {
            stored.extend_from_slice(&trailer(block)?);
        }
    }
    Ok(stored)
}

pub fn decode(stored: &[u8]) -> Result<Vec<u8>> {
    let mut out = Vec::with_capacity(stored.len());
    let mut pages = stored.chunks_exact(STORED);
    for (index, page) in pages.by_ref().enumerate() {
        if page[PAYLOAD..] != trailer(&page[..PAYLOAD])? {
            return Err(Error::new(
                ErrorKind::InvalidData,
                format!("invalid parity/padding on page {index}"),
            ));
        }
        out.extend_from_slice(&page[..PAYLOAD]);
    }
    if pages.remainder().len() >= PAYLOAD {
        return Err(Error::new(
            ErrorKind::InvalidData,
            "truncated or ambiguous final page",
        ));
    }
    out.extend_from_slice(pages.remainder());
    Ok(out)
}

pub fn is_paged(name: &str) -> bool {
    let name = name.trim_start_matches('/');
    if let Some(part) = name.strip_prefix("Partitions/") {
        return !part.is_empty() && !part.contains('/');
    }
    matches!(
        name,
        "Formats/Latest"
            | "Global/ContentDocuments"
            | "Global/DocumentIncrementTable"
            | "Global/ElemTable"
            | "Global/History"
            | "Global/Latest"
            | "Global/PartitionTable"
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn boundaries_and_corruption() {
        for size in [
            0,
            1,
            PAYLOAD - 1,
            PAYLOAD,
            PAYLOAD + 1,
            PAYLOAD * 2,
            PAYLOAD * 2 + 7,
        ] {
            let data: Vec<_> = (0..size).map(|i| (i * 37 + i / 251) as u8).collect();
            let stored = encode(&data).unwrap();
            assert_eq!(stored.len(), size + size / PAYLOAD * TRAILER);
            assert_eq!(decode(&stored).unwrap(), data);
            if size >= PAYLOAD {
                for (position, mask) in [(0, 1), (PAYLOAD, 1), (PAYLOAD + 1, 16), (STORED - 1, 128)]
                {
                    let mut bad = stored.clone();
                    bad[position] ^= mask;
                    assert!(decode(&bad).is_err());
                }
            }
        }
    }
    #[test]
    fn scalar_polynomial_oracle() {
        let payload: Vec<_> = (0..PAYLOAD).map(|i| (i * 37 + i / 251) as u8).collect();
        let parity = trailer(&payload).unwrap();
        for lane in 0..255 {
            let mut remainder = 0u16;
            for row in 0..2036 {
                let bit = row * 255 + lane;
                let input = payload.get(bit / 8).map_or(0, |b| (b >> (bit % 8)) & 1);
                remainder = (remainder << 1) | u16::from(input);
                if remainder & 0x800 != 0 {
                    remainder ^= 0x805;
                }
            }
            for _ in 0..11 {
                remainder <<= 1;
                if remainder & 0x800 != 0 {
                    remainder ^= 0x805;
                }
            }
            let mut got = 0u16;
            for row in 0..11 {
                let bit = 12 + row * 255 + lane;
                got = (got << 1) | u16::from((parity[bit / 8] >> (bit % 8)) & 1);
            }
            assert_eq!(got, remainder, "lane {lane}");
        }
    }
}
