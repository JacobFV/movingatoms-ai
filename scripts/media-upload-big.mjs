// Upload site media too big for `wrangler r2 object put` (over 300 MB) through the site's worker media endpoint.
// usage: WORKER_TOKEN=… node scripts/media-upload-big.mjs <site-url> <local-root> <key> [<key>…]
import { openSync, readSync, statSync, closeSync } from 'node:fs'
import { join } from 'node:path'
const [site, root, ...keys] = process.argv.slice(2)
const T = process.env.WORKER_TOKEN
const PART = 64 * 1024 * 1024
const H = { Authorization: `Bearer ${T}` }
for (const key of keys) {
  const file = join(root, key)
  const size = statSync(file).size
  const c = await (await fetch(`${site}/app/api/worker/media/create`, { method: 'POST', headers: { ...H, 'Content-Type': 'application/json' }, body: JSON.stringify({ key, type: key.endsWith('.zip') ? 'application/zip' : undefined }) })).json()
  const fd = openSync(file, 'r')
  const parts = []
  for (let n = 1, off = 0; off < size; n++, off += PART) {
    const len = Math.min(PART, size - off)
    const buf = Buffer.alloc(len)
    readSync(fd, buf, 0, len, off)
    for (let tries = 0; ; tries++) {
      const r = await fetch(`${site}/app/api/worker/media/part?key=${encodeURIComponent(key)}&uploadId=${encodeURIComponent(c.uploadId)}&n=${n}`, { method: 'PUT', headers: { ...H, 'Content-Length': String(len) }, body: buf })
      if (r.ok) { parts.push(await r.json()); break }
      if (tries >= 4) throw new Error(`part ${n}: ${r.status} ${await r.text()}`)
      await new Promise((res) => setTimeout(res, 2000 * (tries + 1)))
    }
    process.stdout.write(`\r${key} ${Math.round(((off + len) / size) * 100)}%`)
  }
  closeSync(fd)
  const done = await (await fetch(`${site}/app/api/worker/media/complete`, { method: 'POST', headers: { ...H, 'Content-Type': 'application/json' }, body: JSON.stringify({ key, uploadId: c.uploadId, parts }) })).json()
  console.log(`\n${done.key} ${done.size} bytes`)
}
