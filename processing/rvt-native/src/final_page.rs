//! Shortened final-page layouts observed in the two licensed fixtures.
//! Algebraic detection verifies bytes; it does not infer Revit's canonical
//! layout-selection policy for a newly sized payload.
use crate::paged::{read_word, write_word, STORED};
use std::io::{Error, ErrorKind, Result};

pub const GENERATORS: [u16; 6] = [0x13, 0x25, 0x43, 0x83, 0x211, 0x805];
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Layout {
    pub lanes: usize,
    pub codeword_bits: usize,
    pub generator: u16,
}
impl Layout {
    pub fn degree(self) -> usize {
        15 - self.generator.leading_zeros() as usize
    }
    pub fn data_bits(self) -> usize {
        (self.codeword_bits - self.degree()) * self.lanes
    }
    fn valid(self) -> bool {
        GENERATORS.contains(&self.generator)
            && (65..=255).contains(&self.lanes)
            && self.codeword_bits > self.degree()
            && self.codeword_bits < (1 << self.degree())
    }
}

pub fn encode(data: &[u8], layout: Layout) -> Result<Vec<u8>> {
    if !layout.valid() {
        return Err(Error::new(
            ErrorKind::InvalidInput,
            "unsupported final-page layout",
        ));
    }
    let bits = layout.data_bits();
    if data.len() != bits.div_ceil(8)
        || (!bits.is_multiple_of(8) && data[data.len() - 1] >> (bits % 8) != 0)
    {
        return Err(Error::new(
            ErrorKind::InvalidInput,
            "final-page data length/pad bits mismatch",
        ));
    }
    let degree = layout.degree();
    let mut state = vec![[0u64; 4]; degree];
    for row in 0..layout.codeword_bits - degree {
        let mut feedback = read_word(data, row * layout.lanes);
        for (limb, f) in feedback.iter_mut().enumerate() {
            let count = layout.lanes.saturating_sub(limb * 64).min(64);
            *f &= if count == 64 {
                u64::MAX
            } else {
                (1u64 << count) - 1
            };
            *f ^= state[degree - 1][limb];
        }
        state.rotate_right(1);
        state[0] = [0; 4];
        for (tap, word) in state.iter_mut().enumerate() {
            if (layout.generator >> tap) & 1 != 0 {
                for (s, f) in word.iter_mut().zip(feedback) {
                    *s ^= f;
                }
            }
        }
    }
    let mut stored = vec![0; (layout.lanes * layout.codeword_bits).div_ceil(8)];
    stored[..data.len()].copy_from_slice(data);
    for (row, word) in state.iter().rev().enumerate() {
        write_word(&mut stored, bits + row * layout.lanes, *word);
    }
    Ok(stored)
}

pub fn candidates(stored: &[u8]) -> Result<Vec<(Layout, Vec<u8>)>> {
    if stored.is_empty() || stored.len() > STORED {
        return Err(Error::new(
            ErrorKind::InvalidInput,
            "expected nonempty short final page",
        ));
    }
    let mut found = Vec::new();
    for padding in 0..8 {
        let Some(bits) = (stored.len() * 8).checked_sub(padding) else {
            continue;
        };
        for lanes in 65..=255 {
            if bits % lanes != 0 {
                continue;
            }
            for generator in GENERATORS {
                let layout = Layout {
                    lanes,
                    codeword_bits: bits / lanes,
                    generator,
                };
                if !layout.valid() {
                    continue;
                }
                let data_bits = layout.data_bits();
                let mut data = stored[..data_bits.div_ceil(8)].to_vec();
                if !data_bits.is_multiple_of(8) {
                    *data.last_mut().unwrap() &= (1 << (data_bits % 8)) - 1;
                }
                if encode(&data, layout)? == stored {
                    found.push((layout, data));
                }
            }
        }
    }
    Ok(found)
}

pub fn decode(stored: &[u8]) -> Result<(Layout, Vec<u8>)> {
    let mut matches = candidates(stored)?;
    if matches.len() != 1 {
        return Err(Error::new(
            ErrorKind::InvalidData,
            "invalid or ambiguous final-page parity",
        ));
    }
    Ok(matches.pop().unwrap())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn identify_roundtrip_and_reject_corruption() {
        for (generator, rows, lanes) in [
            (0x13, 15, 71),
            (0x25, 28, 65),
            (0x43, 43, 65),
            (0x83, 103, 65),
            (0x211, 242, 65),
            (0x805, 1669, 65),
            (0x805, 2047, 237),
        ] {
            let layout = Layout {
                generator,
                codeword_bits: rows,
                lanes,
            };
            let bits = layout.data_bits();
            let mut data: Vec<_> = (0..bits.div_ceil(8))
                .map(|i| (i * 37 + i / 251) as u8)
                .collect();
            if !bits.is_multiple_of(8) {
                *data.last_mut().unwrap() &= (1 << (bits % 8)) - 1;
            }
            let stored = encode(&data, layout).unwrap();
            assert_eq!(decode(&stored).unwrap(), (layout, data));
            for pos in [0, stored.len() / 2, stored.len() - 1] {
                let mut bad = stored.clone();
                bad[pos] ^= 1;
                assert!(decode(&bad).is_err(), "corrupt {layout:?} at {pos}");
            }
        }
    }
}
