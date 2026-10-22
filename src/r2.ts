// Resumable multipart uploads into R2. Two ways for a part to arrive:
//  - relay (default): the browser PUTs to a signed URL on this site; the Worker streams it into R2 with the binding
//    and records the part in D1 (the binding has no ListParts).
//  - direct: with R2 S3 keys configured, a presigned URL to <account>.r2.cloudflarestorage.com (the bucket needs a
//    CORS rule for the site's origin that exposes ETag). Parts are listed with S3 ListParts.
import { AwsClient } from 'aws4fetch'
import type { Env } from './env'
import { HttpError, signToken, verifyToken } from './util'

export interface Part {
  PartNumber: number
  Size: number
  ETag: string
}

const s3 = (env: Env) =>
  env.R2_ACCESS_KEY_ID && env.R2_SECRET_ACCESS_KEY && env.R2_ACCOUNT_ID && env.R2_UPLOADS_BUCKET
    ? new AwsClient({ accessKeyId: env.R2_ACCESS_KEY_ID, secretAccessKey: env.R2_SECRET_ACCESS_KEY, service: 's3', region: 'auto' })
    : null

const objectUrl = (env: Env, key: string) =>
  `https://${env.R2_ACCOUNT_ID}.r2.cloudflarestorage.com/${env.R2_UPLOADS_BUCKET}/${key.split('/').map(encodeURIComponent).join('/')}`

export const directUploads = (env: Env) => Boolean(s3(env))

/** A URL the browser PUTs one part to (valid 6 hours). `relayPath` is this site's part endpoint. */
export async function partUrl(env: Env, key: string, uploadId: string, partNumber: number, relayPath: string): Promise<string> {
  const aws = s3(env)
  if (aws) {
    const u = new URL(objectUrl(env, key))
    u.searchParams.set('partNumber', String(partNumber))
    u.searchParams.set('uploadId', uploadId)
    u.searchParams.set('X-Amz-Expires', '21600')
    const signed = await aws.sign(new Request(u, { method: 'PUT' }), { aws: { signQuery: true } })
    return signed.url
  }
  const t = await signToken(env.SESSION_SECRET, { k: key, u: uploadId, n: partNumber, exp: Math.floor(Date.now() / 1000) + 21600, typ: 'part' })
  return `${relayPath}?t=${encodeURIComponent(t)}`
}

/** The relay: check the part token, stream the body into R2, record the part. */
export async function relayPart(env: Env, req: Request, token: string | null, expect?: { key: string; uploadId: string; partNumber: number }) {
  const t = await verifyToken<{ k: string; u: string; n: number; typ: string }>(env.SESSION_SECRET, token)
  if (!t || t.typ !== 'part') throw new HttpError(403, 'forbidden', 'This upload link has expired. Press upload again to resume.')
  if (expect && (expect.key !== t.k || expect.uploadId !== t.u || expect.partNumber !== t.n)) throw new HttpError(403, 'forbidden', 'Upload link mismatch.')
  return putPart(env, req, t.k, t.u, t.n)
}

export async function putPart(env: Env, req: Request, key: string, uploadId: string, partNumber: number) {
  const len = Number(req.headers.get('Content-Length') ?? 0)
  if (!req.body) throw new HttpError(400, 'empty_part', 'Empty part.')
  const up = env.UPLOADS.resumeMultipartUpload(key, uploadId)
  // the binding needs a known length: FixedLengthStream when the browser said it, else buffer
  const body = len > 0 ? req.body.pipeThrough(new FixedLengthStream(len)) : await req.arrayBuffer()
  const size = len > 0 ? len : (body as ArrayBuffer).byteLength
  const part = await up.uploadPart(partNumber, body)
  await env.DB.prepare(
    'INSERT INTO upload_parts (upload_id, part_number, etag, size) VALUES (?, ?, ?, ?) ON CONFLICT(upload_id, part_number) DO UPDATE SET etag = excluded.etag, size = excluded.size',
  )
    .bind(uploadId, partNumber, part.etag, size)
    .run()
  return new Response(null, { status: 200, headers: { ETag: `"${part.etag}"`, 'Access-Control-Expose-Headers': 'ETag' } })
}

/** The parts R2 holds for an upload (S3 ListParts when direct, else what the relay recorded). */
export async function listParts(env: Env, key: string, uploadId: string): Promise<Part[]> {
  const aws = s3(env)
  if (aws) {
    const out: Part[] = []
    let marker = 0
    for (;;) {
      const u = new URL(objectUrl(env, key))
      u.searchParams.set('uploadId', uploadId)
      if (marker) u.searchParams.set('part-number-marker', String(marker))
      const r = await aws.fetch(u.toString())
      if (r.status === 404) throw new HttpError(404, 'upload_not_found', 'That upload has expired. Start it again.')
      if (!r.ok) throw new HttpError(502, 'storage_error', `Storage answered ${r.status}.`)
      const xml = await r.text()
      for (const m of xml.matchAll(/<Part>([\s\S]*?)<\/Part>/g)) {
        const get = (tag: string) => new RegExp(`<${tag}>([^<]*)</${tag}>`).exec(m[1])?.[1] ?? ''
        out.push({ PartNumber: Number(get('PartNumber')), Size: Number(get('Size')), ETag: get('ETag').replace(/&quot;/g, '"') })
      }
      const next = /<NextPartNumberMarker>(\d+)<\/NextPartNumberMarker>/.exec(xml)?.[1]
      if (!/<IsTruncated>true<\/IsTruncated>/.test(xml) || !next) break
      marker = Number(next)
    }
    return out
  }
  const { results } = await env.DB.prepare('SELECT part_number, etag, size FROM upload_parts WHERE upload_id = ? ORDER BY part_number')
    .bind(uploadId)
    .all<{ part_number: number; etag: string; size: number }>()
  return results.map((p) => ({ PartNumber: p.part_number, Size: p.size, ETag: `"${p.etag}"` }))
}

export async function completeUpload(env: Env, key: string, uploadId: string, parts: { PartNumber?: number; ETag?: string }[]) {
  const up = env.UPLOADS.resumeMultipartUpload(key, uploadId)
  const clean = parts
    .filter((p) => p.PartNumber && p.ETag)
    .map((p) => ({ partNumber: Number(p.PartNumber), etag: String(p.ETag).replace(/"/g, '') }))
    .sort((a, b) => a.partNumber - b.partNumber)
  if (!clean.length) throw new HttpError(400, 'no_parts', 'No parts arrived. Press upload again.')
  const obj = await up.complete(clean)
  await env.DB.prepare('DELETE FROM upload_parts WHERE upload_id = ?').bind(uploadId).run()
  return obj
}

export async function abortUpload(env: Env, key: string, uploadId: string) {
  try {
    await env.UPLOADS.resumeMultipartUpload(key, uploadId).abort()
  } catch {
    /* already gone */
  }
  await env.DB.prepare('DELETE FROM upload_parts WHERE upload_id = ?').bind(uploadId).run()
}

/** Serve an R2 object with Range and conditional support. */
export async function serveObject(bucket: R2Bucket, key: string, req: Request, extra: { download?: string; cache?: string } = {}) {
  const obj = await bucket.get(key, { range: req.headers, onlyIf: req.headers })
  if (!obj) return new Response('Not found', { status: 404 })
  const headers = new Headers()
  obj.writeHttpMetadata(headers)
  headers.set('ETag', obj.httpEtag)
  headers.set('Accept-Ranges', 'bytes')
  headers.set('Cache-Control', extra.cache ?? 'private, max-age=3600')
  if (extra.download) headers.set('Content-Disposition', `attachment; filename*=UTF-8''${encodeURIComponent(extra.download)}`)
  if (!('body' in obj) || !obj.body) return new Response(null, { status: 304, headers })
  const r = (obj as R2ObjectBody).range as { offset?: number; length?: number } | undefined
  if (r && req.headers.has('Range')) {
    const offset = r.offset ?? 0
    const length = r.length ?? obj.size - offset
    headers.set('Content-Range', `bytes ${offset}-${offset + length - 1}/${obj.size}`)
    headers.set('Content-Length', String(length))
    return new Response(obj.body, { status: 206, headers })
  }
  headers.set('Content-Length', String(obj.size))
  return new Response(obj.body, { headers })
}
