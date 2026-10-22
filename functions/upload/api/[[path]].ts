// The homepage's older resumable uploader (/upload/api; public/home/app.js with ?app=0, and /upload).
// create → sign (part URLs) → PUT parts → list → complete → finish. Files land in the private UPLOADS bucket under
// submissions/<submissionId>/<uuid>/<name>. Parts go straight to R2 when R2 S3 keys are configured, else through
// /upload/api/part (which app.js also uses on its own when storage is blocked on the visitor's network).
import { Hono } from 'hono'
import { handle } from 'hono/cloudflare-pages'
import type { Env } from '../../../src/env'
import { currentUser, type User } from '../../../src/auth'
import { sendEmail } from '../../../src/email'
import { completeUpload, listParts, partUrl, putPart, relayPart } from '../../../src/r2'
import { HttpError, now, uuid } from '../../../src/util'

const app = new Hono<{ Bindings: Env }>().basePath('/upload/api')

// mirrors ALLOWED in public/home/app.js
const ALLOWED = new Set(
  (
    '.e57 .las .laz .pts .ptx .pcd .ply .xyz .rcp .rcs .pod .zfs .fls .lcc .lgsx .rdbx .bpf ' +
    '.obj .fbx .glb .gltf .stl .usd .usda .usdc .usdz .dae .3ds .x3d .3mf .blend .abc .drc ' +
    '.ifc .rvt .rfa .step .stp .iges .igs .dwg .dxf .skp .3dm ' +
    '.zip .7z .rar .tar .gz .tgz .bz2 .xz .zst ' +
    '.mp4 .mov .webm .mkv .avi .insv .360 .jpg .jpeg .png .tif .tiff .exr .heic .webp .pdf .csv .json .txt'
  ).split(' '),
)
const MAX_BYTES = 200e9
const MiB = 1024 * 1024
const ID = /^[0-9a-f-]{36}$/

const json = (data: Record<string, unknown>, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' } })
const fail = (status: number, error: string) => json({ ok: false, error }, status)

app.onError((e) => {
  if (e instanceof HttpError) return fail(e.status, e.message)
  console.error(e)
  return fail(500, 'Something went wrong on our side. Press upload again to resume.')
})

async function signedIn(env: Env, req: Request): Promise<User> {
  const u = await currentUser(env, req)
  if (!u) throw new HttpError(401, 'unauthorized', 'Sign in to upload.')
  return u
}

/** The submission (theirs) and, when given, that the key belongs to it. */
async function ownSubmission(env: Env, user: User, sid: string, key?: string) {
  if (!ID.test(sid)) throw new HttpError(404, 'not_found', 'Upload not found.')
  const s = await env.DB.prepare('SELECT id, user_id, status FROM submissions WHERE id = ?').bind(sid).first<{ id: string; user_id: string; status: string }>()
  if (!s || (s.user_id !== user.id && !user.is_admin)) throw new HttpError(404, 'not_found', 'Upload not found.')
  if (key !== undefined && !key.startsWith(`submissions/${sid}/`)) throw new HttpError(403, 'forbidden', 'That file isn’t part of this upload.')
  return s
}

const ext = (name: string) => {
  const i = name.lastIndexOf('.')
  return i < 0 ? '' : name.slice(i).toLowerCase()
}
const safeName = (name: string) => name.replace(/[\\/\x00-\x1f]/g, '_').slice(-200) || 'file'
const body = async (req: Request) => ((await req.json().catch(() => ({}))) ?? {}) as Record<string, any>

app.post('/create', async (c) => {
  const user = await signedIn(c.env, c.req.raw)
  const b = await body(c.req.raw)
  const f = b.file ?? {}
  const name = safeName(String(f.name ?? ''))
  const size = Number(f.size)
  if (!ALLOWED.has(ext(name))) return fail(400, `We can't take ${ext(name) || 'that kind of'} files. Zip it, or send point clouds, meshes, CAD or archives.`)
  if (!Number.isFinite(size) || size < 0) return fail(400, 'Unknown file size.')
  if (size > MAX_BYTES) return fail(400, 'Files can be up to 200 GB each. Split it, or book a call for larger scans.')

  let sid = typeof b.submissionId === 'string' && ID.test(b.submissionId) ? b.submissionId : uuid()
  const t = now()
  const existing = await c.env.DB.prepare('SELECT user_id FROM submissions WHERE id = ?').bind(sid).first<{ user_id: string }>()
  if (existing && existing.user_id !== user.id) sid = uuid()
  if (!existing || existing.user_id !== user.id) {
    const s = b.submitter ?? {}
    await c.env.DB.prepare('INSERT INTO submissions (id, user_id, email, name, company, notes, scope, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
      .bind(
        sid,
        user.id,
        user.email,
        String(s.name ?? user.name ?? '').slice(0, 120) || null,
        String(s.company ?? user.company ?? '').slice(0, 200) || null,
        String(s.notes ?? '').slice(0, 4000),
        JSON.stringify(b.scope ?? s.scope ?? {}),
        'uploading',
        t,
        t,
      )
      .run()
  }
  const key = `submissions/${sid}/${uuid()}/${name}`
  const type = String(f.type || 'application/octet-stream').slice(0, 120)
  const mp = await c.env.UPLOADS.createMultipartUpload(key, { httpMetadata: { contentType: type }, customMetadata: { submission: sid, user: user.id } })
  const partSize = Math.ceil(Math.max(32 * MiB, Math.ceil(size / 9500)) / MiB) * MiB
  await c.env.DB.prepare('INSERT INTO submission_files (submission_id, r2_key, upload_id, name, size_bytes, content_type, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)')
    .bind(sid, key, mp.uploadId, name, size, type, 'uploading', t)
    .run()
  return json({ ok: true, submissionId: sid, key, uploadId: mp.uploadId, partSize })
})

app.post('/sign', async (c) => {
  const user = await signedIn(c.env, c.req.raw)
  const b = await body(c.req.raw)
  const key = String(b.key ?? '')
  const uploadId = String(b.uploadId ?? '')
  const sid = key.split('/')[1] ?? ''
  await ownSubmission(c.env, user, sid, key)
  const parts: number[] = (Array.isArray(b.parts) ? b.parts : []).map(Number).filter((n: number) => Number.isInteger(n) && n >= 1 && n <= 10000).slice(0, 200)
  const urls: Record<number, string> = {}
  for (const n of parts) urls[n] = await partUrl(c.env, key, uploadId, n, '/upload/api/part')
  return json({ ok: true, urls })
})

app.get('/list', async (c) => {
  const user = await signedIn(c.env, c.req.raw)
  const key = c.req.query('key') ?? ''
  const uploadId = c.req.query('uploadId') ?? ''
  const sid = c.req.query('submissionId') ?? ''
  await ownSubmission(c.env, user, sid, key)
  const head = await c.env.UPLOADS.head(key)
  if (head) return json({ ok: true, complete: true, size: head.size, parts: [] })
  const row = await c.env.DB.prepare('SELECT upload_id FROM submission_files WHERE submission_id = ? AND r2_key = ?').bind(sid, key).first<{ upload_id: string }>()
  if (!row || row.upload_id !== uploadId) return fail(404, 'That upload has expired. Start it again.')
  return json({ ok: true, parts: await listParts(c.env, key, uploadId) })
})

// one part: a signed link (?t=) from /sign, or the relay app.js falls back to (?submissionId&key&uploadId&partNumber)
app.put('/part', async (c) => {
  const t = c.req.query('t')
  if (t) return relayPart(c.env, c.req.raw, t)
  const user = await signedIn(c.env, c.req.raw)
  const key = c.req.query('key') ?? ''
  const uploadId = c.req.query('uploadId') ?? ''
  const n = Number(c.req.query('partNumber'))
  if (!Number.isInteger(n) || n < 1 || n > 10000) return fail(400, 'Bad part number.')
  const sid = c.req.query('submissionId') ?? ''
  await ownSubmission(c.env, user, sid, key)
  const row = await c.env.DB.prepare('SELECT upload_id FROM submission_files WHERE submission_id = ? AND r2_key = ?').bind(sid, key).first<{ upload_id: string }>()
  if (!row || row.upload_id !== uploadId) return fail(404, 'That upload has expired. Start it again.')
  return putPart(c.env, c.req.raw, key, uploadId, n)
})

app.post('/complete', async (c) => {
  const user = await signedIn(c.env, c.req.raw)
  const b = await body(c.req.raw)
  const sid = String(b.submissionId ?? '')
  const key = String(b.key ?? '')
  await ownSubmission(c.env, user, sid, key)
  const obj = await completeUpload(c.env, key, String(b.uploadId ?? ''), Array.isArray(b.parts) ? b.parts : [])
  await c.env.DB.prepare("UPDATE submission_files SET status = 'ready', size_bytes = ? WHERE submission_id = ? AND r2_key = ?").bind(obj.size, sid, key).run()
  return json({ ok: true, key, size: obj.size })
})

app.post('/finish', async (c) => {
  const user = await signedIn(c.env, c.req.raw)
  const b = await body(c.req.raw)
  const sid = String(b.submissionId ?? '')
  const s = await ownSubmission(c.env, user, sid)
  const { results: files } = await c.env.DB.prepare('SELECT name, size_bytes, status FROM submission_files WHERE submission_id = ?').bind(sid).all<{ name: string; size_bytes: number; status: string }>()
  if (!files.length || files.some((f) => f.status !== 'ready')) return fail(409, 'Some files haven’t finished uploading. Press upload again to resume.')
  if (s.status !== 'received') {
    await c.env.DB.prepare("UPDATE submissions SET status = 'received', updated_at = ? WHERE id = ?").bind(now(), sid).run()
    if (c.env.TEAM_EMAIL) {
      const total = files.reduce((a, f) => a + (f.size_bytes ?? 0), 0)
      c.executionCtx.waitUntil(
        sendEmail(c.env, {
          to: c.env.TEAM_EMAIL,
          subject: `New scan from ${user.email}: ${files[0].name}${files.length > 1 ? ` + ${files.length - 1}` : ''}`,
          text: `${user.name ?? ''} <${user.email}>${user.company ? ` (${user.company})` : ''} uploaded ${files.length} file(s), ${(total / 1e9).toFixed(2)} GB.\n\n${files.map((f) => `- ${f.name} (${((f.size_bytes ?? 0) / 1e6).toFixed(1)} MB)`).join('\n')}\n\nSubmission: ${sid}`,
          replyTo: user.email,
        }).then(() => undefined),
      )
    }
  }
  return json({ ok: true, submissionId: sid })
})

app.all('*', () => fail(404, 'Not found.'))

export const onRequest = handle(app)
