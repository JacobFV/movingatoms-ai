import sys, olefile, zlib, gzip, io, re
f = olefile.OleFileIO(sys.argv[1])
streams = f.listdir()
print(len(streams), "streams")
tot = {}
for s in streams:
    name = "/".join(s); size = f.get_size(name)
    top = s[0]
    tot[top] = tot.get(top, 0) + size
    if len(s) == 1 or size > 5_000_000: print(f"{size:>12}  {name}")
print("by top-level storage:", sorted(tot.items(), key=lambda x: -x[1])[:12])
b = f.openstream("BasicFileInfo").read()
txt = b.decode("utf-16-le", "ignore")
print("BasicFileInfo:", re.sub(r"[^\x20-\x7e\n]", " ", txt)[:900])
