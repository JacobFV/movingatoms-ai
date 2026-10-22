import sys, olefile, zlib, base64, json
f = olefile.OleFileIO(sys.argv[1]); raw = f.openstream("Global/History").read()
i = raw.find(b"\x1f\x8b"); d = zlib.decompressobj(16 + 15); inflated = d.decompress(raw[i:])
print("prefix bytes:", raw[:i].hex(), "inflated:", len(inflated))
txt = inflated.decode("utf-16-le", "ignore")
old = "20230509_0315(x64)"; new = "20991231_2359(x64)"   # a build tag in the history, same length
enc = "utf-16-le" if old.encode("utf-16-le") in inflated else "ascii"; assert old.encode(enc) in inflated; print("encoding", enc)
patched = inflated.replace(old.encode(enc), new.encode(enc), 1)
json.dump({"patches": [{"stream_name": "Global/History", "new_decompressed_base64": base64.b64encode(patched).decode(), "framing": "CustomPrefix8"}]}, open("hist.json", "w"))
json.dump({"patches": [{"stream_name": "Global/ElemTable", "new_decompressed_base64": base64.b64encode(b"\x00" * 200000).decode(), "framing": "CustomPrefix8"}]}, open("elem.json", "w"))
