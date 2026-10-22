import sys, olefile, hashlib, xxhash, crcmod.predefined as cp
f = olefile.OleFileIO(sys.argv[1]); P, PAY = 65249, 64896
data = f.openstream("Partitions/46").read(); pay, tail = data[:PAY], data[PAY:P]
tail1 = tail[1:]
digs = {"xxh32": xxhash.xxh32(pay).digest(), "xxh64": xxhash.xxh64(pay).digest(), "xxh3_64": xxhash.xxh3_64(pay).digest(),
        "xxh128": xxhash.xxh3_128(pay).digest(), "sha512": hashlib.sha512(pay).digest(), "blake2b": hashlib.blake2b(pay).digest()}
for n in ("crc-32c", "crc-64", "crc-64-we", "crc-64-jones", "crc-32-bzip2", "crc-32-mpeg", "crc-16", "crc-ccitt-false"):
    c = cp.mkPredefinedCrcFun(n)(pay); w = (c.bit_length() + 7) // 8 or 1
    digs[n] = c.to_bytes(max(w, 2), "little"); digs[n + "be"] = c.to_bytes(max(w, 2), "big")
for k, v in digs.items():
    for d in (v, v[::-1]):
        pos = tail.find(d[:4])
        if pos >= 0: print("HIT", k, pos)
print("checked", len(digs), "digests (both endiannesses): no hits" if True else "")
# block structure guess: does the tail split into equal records with a repeating small header?
for rec in (8, 11, 16, 22, 32, 44, 88):
    if 352 % rec == 0:
        cols = [len(set(tail1[i::rec])) for i in range(rec)]
        print(f"rec {rec:>3}: distinct values per column (low = structured):", cols[:12])
