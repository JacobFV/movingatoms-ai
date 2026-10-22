import sys, olefile, zlib, hashlib, collections, math
f = olefile.OleFileIO(sys.argv[1])
P, PAY = 65249, 64896
pages = []
for s in f.listdir():
    name = "/".join(s)
    if not (name.startswith("Partitions/") or name.startswith("Global/")): continue
    data = f.openstream(name).read()
    for i in range(len(data) // P):
        pg = data[i*P:(i+1)*P]
        pages.append((name, i, pg[:PAY], pg[PAY:]))
print("full pages:", len(pages))
name, i, pay, tail = pages[0]
print(name, i, "tail head:", tail[:48].hex())
def ent(b):
    c = collections.Counter(b); n = len(b)
    return -sum(v/n*math.log2(v/n) for v in c.values())
print("tail entropy bits/byte:", round(ent(tail), 3), "payload entropy:", round(ent(pay), 3))
# does any common digest of the payload appear inside the tail?
cands = {
  "crc32": zlib.crc32(pay).to_bytes(4, "little"), "crc32be": zlib.crc32(pay).to_bytes(4, "big"),
  "adler32": zlib.adler32(pay).to_bytes(4, "little"), "adler32be": zlib.adler32(pay).to_bytes(4, "big"),
  "md5": hashlib.md5(pay).digest(), "sha1": hashlib.sha1(pay).digest(), "sha256": hashlib.sha256(pay).digest(),
}
for k, v in cands.items():
    print(f"{k:10} in tail: {tail.find(v[:4])}")
# per-block checksums? try splitting payload into n blocks and crc each, look for them in tail
for n in (16, 32, 64, 88, 128, 169, 176, 338, 352):
    if PAY % n: continue
    bs = PAY // n
    hits = sum(1 for j in range(n) if tail.find(zlib.crc32(pay[j*bs:(j+1)*bs]).to_bytes(4, "little")) >= 0)
    if hits: print("per-block crc32 hits", n, hits)
# tail structure: is the same position correlated across pages? look at constant bytes across all tails
const = [all(p[3][k] == pages[0][3][k] for p in pages) for k in range(len(tail))]
print("tail byte positions constant across all pages:", sum(const), [k for k, c in enumerate(const) if c][:40])
# Is the tail a function of payload alone? find two pages with equal payload
seen = {}
for p in pages:
    h = hashlib.sha1(p[2]).digest()
    if h in seen and seen[h][3] != p[3]: print("same payload, different tail!", seen[h][:2], p[:2]); break
    seen[h] = p
# linearity test over GF(2): tail(a) xor tail(b) vs tail(a xor b) needs a third page; instead test for RS: tail length 353 prime
print("first 4 tail u32 values:", [int.from_bytes(tail[k:k+4], 'little') for k in range(0, 16, 4)])
