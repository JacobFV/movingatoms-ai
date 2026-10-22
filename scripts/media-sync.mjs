#!/usr/bin/env node
// Upload the site's oversized files (too big for Pages' 25 MiB limit) to the public MEDIA bucket, keeping paths:
// <dir>/lidarsample/revit/X.zip → movingatoms-media/lidarsample/revit/X.zip, served at /lidarsample/revit/X.zip by
// functions/_middleware.ts.
//
//   node scripts/media-sync.mjs [dir] [--bucket movingatoms-media] [--dry-run]
//
// Files up to 300 MB go through `wrangler r2 object put`. Larger ones need the S3 API (multipart, 64 MiB parts):
// set R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY and R2_ACCOUNT_ID (an R2 API token with write access); without them
// they're listed as pending.
import { spawnSync } from 'node:child_process'
import { createReadStream, readdirSync, statSync } from 'node:fs'
import { join, relative, sep } from 'node:path'
import { AwsClient } from 'aws4fetch'

const args = process.argv.slice(2)
const flag = (name, d) => {
  const i = args.indexOf(name)
  return i >= 0 ? args.splice(i, 2)[1] : d
}
const dry = args.includes('--dry-run') && args.splice(args.indexOf('--dry-run'), 1)
const bucket = flag('--bucket', 'movingatoms-media')
const dir = args[0] ?? '/tmp/claude-1000/-home-brandonin-Documents-movingatoms-ai-pages-dev/95165d0a-8a34-4fdf-b270-d82863156105/scratchpad/big'

const WRANGLER_MAX = 300 * 1000 * 1000
const PART = 64 * 1024 * 1024
const TYPES = {
  zip: 'application/zip',
  glb: 'model/gltf-binary',
  gltf: 'model/gltf+json',
  bin: 'application/octet-stream',
  mp4: 'video/mp4',
  webm: 'video/webm',
  json: 'application/json',
  exr: 'image/x-exr',
  jpg: 'image/jpeg',
  png: 'image/png',
  webp: 'image/webp',
}
const typeOf = (f) => TYPES[f.split('.').pop().toLowerCase()] ?? 'application/octet-stream'

function walk(d) {
  return readdirSync(d, { withFileTypes: true }).flatMap((e) => (e.isDirectory() ? walk(join(d, e.name)) : e.isFile() ? [join(d, e.name)] : []))
}

const { R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ACCOUNT_ID } = process.env
const aws = R2_ACCESS_KEY_ID && R2_SECRET_ACCESS_KEY && R2_ACCOUNT_ID ? new AwsClient({ accessKeyId: R2_ACCESS_KEY_ID, secretAccessKey: R2_SECRET_ACCESS_KEY, service: 's3', region: 'auto' }) : null
const objUrl = (key) => `https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com/${bucket}/${key.split('/').map(encodeURIComponent).join('/')}`

async function readRange(file, start, end) {
  const chunks = []
  for await (const c of createReadStream(file, { start, end: end - 1 })) chunks.push(c)
  return Buffer.concat(chunks)
}

async function multipart(file, key, size) {
  const type = typeOf(file)
  let r = await aws.fetch(`${objUrl(key)}?uploads`, { method: 'POST', headers: { 'Content-Type': type } })
  if (!r.ok) throw new Error(`create ${r.status} ${await r.text()}`)
  const uploadId = /<UploadId>([^<]+)<\/UploadId>/.exec(await r.text())[1]
  const parts = []
  try {
    for (let n = 1, off = 0; off < size; n++, off += PART) {
      const body = await readRange(file, off, Math.min(size, off + PART))
      for (let attempt = 0; ; attempt++) {
        r = await aws.fetch(`${objUrl(key)}?partNumber=${n}&uploadId=${encodeURIComponent(uploadId)}`, { method: 'PUT', body })
        if (r.ok) break
        if (attempt >= 4) throw new Error(`part ${n}: ${r.status} ${await r.text()}`)
        await new Promise((res) => setTimeout(res, 1000 * 2 ** attempt))
      }
      parts.push({ n, etag: r.headers.get('ETag') })
      process.stdout.write(`\r  ${key}: ${Math.min(100, ((off + body.length) / size) * 100).toFixed(0)}%`)
    }
    const xml = `<CompleteMultipartUpload>${parts.map((p) => `<Part><PartNumber>${p.n}</PartNumber><ETag>${p.etag}</ETag></Part>`).join('')}</CompleteMultipartUpload>`
    r = await aws.fetch(`${objUrl(key)}?uploadId=${encodeURIComponent(uploadId)}`, { method: 'POST', body: xml })
    if (!r.ok) throw new Error(`complete ${r.status} ${await r.text()}`)
    process.stdout.write('\n')
  } catch (e) {
    await aws.fetch(`${objUrl(key)}?uploadId=${encodeURIComponent(uploadId)}`, { method: 'DELETE' }).catch(() => {})
    throw e
  }
}

const files = walk(dir)
const pending = []
let failed = 0
for (const file of files) {
  const key = relative(dir, file).split(sep).join('/')
  const size = statSync(file).size
  const mb = (size / 1e6).toFixed(1)
  if (size <= WRANGLER_MAX) {
    console.log(`put ${key} (${mb} MB)`)
    if (dry) continue
    const r = spawnSync('npx', ['wrangler', 'r2', 'object', 'put', `${bucket}/${key}`, '--file', file, '--remote', '--content-type', typeOf(file)], { stdio: 'inherit' })
    if (r.status !== 0) failed++
  } else if (aws) {
    console.log(`multipart ${key} (${mb} MB)`)
    if (dry) continue
    try {
      await multipart(file, key, size)
    } catch (e) {
      console.error(`  failed: ${e.message}`)
      failed++
    }
  } else pending.push(`${key} (${mb} MB)`)
}
if (pending.length) {
  console.log(`\n${pending.length} file(s) are over wrangler's 300 MB limit and need the S3 API.`)
  console.log('Create an R2 API token (R2 → Manage API tokens, Object Read & Write on this bucket), then rerun with')
  console.log('R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY and R2_ACCOUNT_ID set. Pending:')
  for (const p of pending) console.log(`  - ${p}`)
}
process.exit(failed ? 1 : 0)
