// The app's web API (CONTRACTS §4), at /app/api/*. Sign-in, projects, uploads, chat, the viewer manifest, billing,
// sharing, admin, and the processing worker's endpoints. The live model and agent turns run in the project's
// Durable Object (workers/realtime); see docs/INTERNAL.md.
import { Hono, type Context } from 'hono'
import { handle } from 'hono/cloudflare-pages'
import type { Env } from '../../../src/env'
import {
  accessToken,
  currentUser,
  publicUser,
  sessionCookie,
  sessionFromCookie,
  passwordSignIn,
  signOut,
  upsertUser,
  type User,
} from '../../../src/auth'
import { addMessage, getMessage, listMessages, setBody } from '../../../src/messages'
import { estimate, normScope, readEstimate, writeEstimate, type Estimate } from '../../../src/estimate'
import {
  accountSummary,
  assetBase,
  billingSettings,
  currentTurn,
  emit,
  fileLink,
  loadProject,
  members,
  platformSettings,
  postLedger,
  projectCards,
  projectOut,
  projectRevisions,
  projectScans,
  requireProject,
  room,
  SCAN_JSON,
  touchProject,
  type ProjectRow,
  type Role,
} from '../../../src/projects'
import { abortUpload, completeUpload, listParts, partUrl, relayPart, serveObject } from '../../../src/r2'
import { HttpError, errorResponse, now, parseRow, parseRows, randomToken, round2, uuid } from '../../../src/util'

type C = Context<{ Bindings: Env; Variables: { user: User } }>
const app = new Hono<{ Bindings: Env; Variables: { user: User } }>().basePath('/app/api')

const POINT_CLOUD_RE = /\.(e57|las|laz|ply|pts|xyz|ptx|rcp|rcs|zip)$/i
const isPointCloud = (name: string) => POINT_CLOUD_RE.test(name)
const MAX_UPLOAD = 200 * 1024 ** 3

app.onError((e) => errorResponse(e))
app.notFound(() => errorResponse(new HttpError(404, 'not_found', 'Not found.')))

async function body<T = any>(c: C): Promise<T> {
  try {
    return (await c.req.json()) as T
  } catch {
    return {} as T
  }
}

function me(c: C) {
  return c.get('user')
}

/** The account a person spends from (their own). */
async function myAccount(c: C) {
  const r = await c.env.DB.prepare('SELECT account_id FROM account_members WHERE user_id = ? LIMIT 1').bind(me(c).id).first<{ account_id: string }>()
  if (!r) throw new HttpError(404, 'no_account', 'No account.')
  return r.account_id
}

function requireAdmin(c: C) {
  if (!me(c).is_admin) throw new HttpError(403, 'forbidden', 'Admins only.')
}

// ---------------------------------------------------------------- sign-in (no session needed)

app.get('/auth/session', async (c) => {
  const s = await sessionFromCookie(c.env, c.req.raw)
  if (!s) return c.json({ signed_in: false }, 401)
  return c.json({ signed_in: true, ...(await accessToken(c.env, s.user, s.sid)), user: publicUser(s.user) })
})

// email + password (no reset or recovery). `mode`: login | register | auto (sign in, or create the account)
app.post('/auth/password', async (c) => {
  const b = await body(c)
  const r = await passwordSignIn(c.env, c.req.raw, b)
  c.header('Set-Cookie', r.cookie)
  return c.json({ ...(await accessToken(c.env, r.user, r.sid)), user: publicUser(r.user), new_account: r.isNew })
})

// the emailed-code sign-in is off: there's no email provider (see src/auth.ts startCode/verifyCode to restore it)
app.post('/auth/code/start', (c) => c.json({ error: 'use_password', message: 'Sign in with your email and password at /app/sign-in.' }, 410))
app.post('/auth/code/verify', (c) => c.json({ error: 'use_password', message: 'Sign in with your email and password at /app/sign-in.' }, 410))

// Supabase sessions from the old platform can't be carried over: the person signs in again.
app.post('/auth/session/adopt', (c) => c.json({ error: 'not_supported', message: 'Sign in again.' }, 400))

app.post('/auth/signout', async (c) => {
  c.header('Set-Cookie', await signOut(c.env, c.req.raw))
  return c.json({ ok: true })
})

// ---------------------------------------------------------------- the view-only link (§20), no session

/** A share token's project, or 404 (the link is off or was replaced). */
async function shared(c: C, token: string) {
  const p = parseRow<ProjectRow>(await c.env.DB.prepare('SELECT * FROM projects WHERE share_token = ?').bind(token).first(), ['settings'])
  if (!p || p.status === 'archived') throw new HttpError(404, 'not_found', 'This link isn’t available.')
  return p
}

app.get('/public/:token', async (c) => {
  const p = await shared(c, c.req.param('token'))
  const [scans, revisions, turn, seq] = await Promise.all([projectScans(c.env, p.id), projectRevisions(c.env, p.id), currentTurn(c.env, p.id), modelSeq(c.env, p.id)])
  const counts = await c.env.DB.prepare(
    "SELECT (SELECT COUNT(*) FROM files WHERE project_id = ?1 AND status = 'ready') AS f, (SELECT MAX(updated_at) FROM scans WHERE project_id = ?1) AS s, (SELECT COUNT(*) FROM revisions WHERE project_id = ?1) AS r",
  )
    .bind(p.id)
    .first<{ f: number; s: string | null; r: number }>()
  const sig = [counts?.f, counts?.s, counts?.r, seq.seq].join(':')
  return c.json({ project: { id: p.id, name: p.name }, scans, revisions, running: Boolean(turn), model_seq: seq.seq, sig })
})

app.get('/public/:token/files/:fid/url', async (c) => {
  const p = await shared(c, c.req.param('token'))
  const f = await c.env.DB.prepare("SELECT * FROM files WHERE id = ? AND project_id = ? AND status = 'ready'").bind(c.req.param('fid'), p.id).first<any>()
  if (!f) throw new HttpError(404, 'not_found', 'File not found.')
  return c.json(await fileLink(c.env, f, c.req.query('download') === '1'))
})

// the project's reads on a view-only link: the same handlers, as a viewer, with nothing private
app.get('/public/:token/*', async (c) => {
  const p = await shared(c, c.req.param('token'))
  const rest = c.req.path.split(`/public/${c.req.param('token')}`)[1] || ''
  const visitor = { id: 'public', email: '', name: 'Visitor', is_admin: 0 } as unknown as User
  return projectRead(c, p, 'viewer', visitor, rest, true)
})

// ---------------------------------------------------------------- the processing worker (bearer WORKER_TOKEN)

const worker = new Hono<{ Bindings: Env; Variables: { user: User } }>()
worker.use('*', async (c, next) => {
  const t = c.req.header('Authorization')?.replace(/^Bearer /, '')
  if (!c.env.WORKER_TOKEN || t !== c.env.WORKER_TOKEN) throw new HttpError(401, 'unauthorized', 'Worker token required.')
  await next()
})

// claim the oldest queued job (of the given types); the claim lapses after 15 minutes without an update
worker.post('/jobs/claim', async (c) => {
  const b = await body(c)
  const types: string[] = Array.isArray(b.types) && b.types.length ? b.types : ['ingest', 'link_import', 'model_fit', 'estimate', 'build', 'heatmap']
  const stale = Date.now() - 15 * 60_000
  const job = await c.env.DB.prepare(
    `UPDATE jobs SET status = 'running', claimed_by = ?, claimed_at = ?, updated_at = ?
     WHERE id = (SELECT id FROM jobs WHERE type IN (${types.map(() => '?').join(',')})
                 AND (status = 'queued' OR (status = 'running' AND claimed_at < ?))
                 AND (? IS NULL OR COALESCE(json_extract(input, '$.size'), 0) <= ?)
                 ORDER BY created_at LIMIT 1)
     RETURNING *`,
  )
    // max_size: a worker with little disk (a Cloudflare container) leaves big scans to a bigger machine
    .bind(String(b.worker ?? 'worker'), Date.now(), now(), ...types, stale, b.max_size ?? null, b.max_size ?? null)
    .first()
  if (!job) return c.body(null, 204)
  const j = parseRow<any>(job, ['input', 'result'])!
  const [project, scans, files] = await Promise.all([
    loadProject(c.env, j.project_id),
    projectScans(c.env, j.project_id),
    c.env.DB.prepare("SELECT * FROM files WHERE project_id = ? AND status = 'ready'").bind(j.project_id).all(),
  ])
  return c.json({ job: j, project: project && projectOut(project), scans, files: parseRows(files.results, ['meta']) })
})

worker.patch('/jobs/:id', async (c) => {
  const b = await body(c)
  const job = await c.env.DB.prepare('SELECT * FROM jobs WHERE id = ?').bind(c.req.param('id')).first<any>()
  if (!job) throw new HttpError(404, 'not_found', 'No such job.')
  const status = b.status ?? job.status
  await c.env.DB.prepare('UPDATE jobs SET status = ?, stage = ?, progress = ?, result = ?, error = ?, claimed_at = ?, updated_at = ? WHERE id = ?')
    .bind(status, b.stage ?? job.stage, Number(b.progress ?? job.progress), b.result !== undefined ? JSON.stringify(b.result) : job.result, b.error ?? job.error, Date.now(), now(), job.id)
    .run()
  await emit(c.env, job.project_id, {
    type: 'job.updated',
    id: job.id,
    type_: job.type,
    status,
    stage: b.stage ?? job.stage,
    progress: Number(b.progress ?? job.progress),
    job: { id: job.id, type: job.type, status, stage: b.stage ?? job.stage, progress: Number(b.progress ?? job.progress), error: b.error ?? null },
  })
  return c.json({ ok: true })
})

// a scan's progress and results: status, stage_detail, progress, point_count, bounds, frame, labels, viewer, brief…
worker.patch('/scans/:id', async (c) => {
  const b = await body(c)
  const s = await c.env.DB.prepare('SELECT * FROM scans WHERE id = ?').bind(c.req.param('id')).first<any>()
  if (!s) throw new HttpError(404, 'not_found', 'No such scan.')
  const cols = ['status', 'stage_detail', 'progress', 'point_count', 'copc_key', 'potree_prefix', 'error', ...SCAN_JSON]
  const sets: string[] = []
  const vals: unknown[] = []
  for (const k of cols)
    if (k in b) {
      sets.push(`${k} = ?`)
      vals.push(SCAN_JSON.includes(k) ? JSON.stringify(b[k]) : b[k])
    }
  if (sets.length) await c.env.DB.prepare(`UPDATE scans SET ${sets.join(', ')}, updated_at = ? WHERE id = ?`).bind(...vals, now(), s.id).run()
  const scan = parseRow<any>(await c.env.DB.prepare('SELECT * FROM scans WHERE id = ?').bind(s.id).first(), SCAN_JSON)
  await emit(c.env, s.project_id, { type: 'scan.updated', scan })
  if (b.status === 'ready' && s.status !== 'ready') await scanReady(c.env, s.project_id, scan)
  // measured (bounds or a footprint arrive before labelling): price it now, not at the end
  else if ((b.bounds || b.brief?.footprint_m2) && !s.bounds) {
    const p = await loadProject(c.env, s.project_id)
    if (p) c.executionCtx.waitUntil(estimate(c.env, p.id, p.settings?.scope))
  }
  if (b.status === 'error' && s.status !== 'error')
    await addMessage(c.env, s.project_id, { role: 'system', body: { text: `We couldn’t read **${s.name}**: ${b.error ?? 'the file is unreadable'}. Our team has been told.` } })
  return c.json({ scan })
})

/** A scan is ready: the project becomes active, the estimate is priced, and (outside onboarding) the agent starts. */
async function scanReady(env: Env, pid: string, scan: any) {
  const p = (await loadProject(env, pid))!
  if (p.status === 'setup' || p.status === 'processing') {
    await env.DB.prepare("UPDATE projects SET status = 'active', updated_at = ? WHERE id = ?").bind(now(), pid).run()
    await emit(env, pid, { type: 'project.updated', project: { id: pid, status: 'active' } })
  }
  await estimate(env, pid, p.settings?.scope)
  if (p.settings?.onboarding && !p.settings?.started) {
    await addMessage(env, pid, { role: 'system', body: { text: `Scan ready: **${scan.name}**.`, first: true } })
    return
  }
  const m = await addMessage(env, pid, { role: 'system', body: { text: `Scan ready: **${scan.name}**.`, kickoff: true, for_agent: true } })
  await startTurn(env, pid, m.id, { id: 'system', email: '', name: 'Moving Atoms' })
}

// register an output in R2 (a deliverable, an overview image, an asset) as a project file
worker.post('/projects/:pid/files', async (c) => {
  const pid = c.req.param('pid')
  const b = await body(c)
  if (!String(b.r2_key ?? '').startsWith(`projects/${pid}/`)) throw new HttpError(400, 'bad_key', 'Files live under projects/<pid>/.')
  const head = await c.env.UPLOADS.head(b.r2_key)
  if (!head) throw new HttpError(404, 'not_in_storage', 'Upload the object first.')
  const f = {
    id: uuid(),
    project_id: pid,
    kind: b.kind ?? 'deliverable',
    name: b.name ?? b.r2_key.split('/').pop(),
    r2_key: b.r2_key,
    size_bytes: head.size,
    content_type: b.content_type ?? head.httpMetadata?.contentType ?? null,
    status: 'ready',
    meta: b.meta ?? null,
    created_by: null,
    created_at: now(),
  }
  await c.env.DB.prepare('INSERT INTO files (id, project_id, kind, name, r2_key, size_bytes, content_type, status, meta, created_by, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)')
    .bind(f.id, pid, f.kind, f.name, f.r2_key, f.size_bytes, f.content_type, f.status, f.meta ? JSON.stringify(f.meta) : null, null, f.created_at)
    .run()
  await emit(c.env, pid, { type: 'file.created', file: f })
  return c.json({ file: f })
})

worker.post('/projects/:pid/revisions', async (c) => {
  const pid = c.req.param('pid')
  const b = await body(c)
  const n = ((await c.env.DB.prepare('SELECT MAX(number) AS n FROM revisions WHERE project_id = ?').bind(pid).first<{ n: number | null }>())?.n ?? 0) + 1
  const r = {
    id: uuid(),
    project_id: pid,
    number: n,
    title: b.title ?? null,
    notes: b.notes ?? null,
    status: b.status ?? 'ready',
    model_seq: b.model_seq ?? null,
    graph_key: b.graph_key ?? null,
    glb_key: b.glb_key ?? null,
    view_key: b.view_key ?? null,
    ifc_key: b.ifc_key ?? null,
    heatmap: b.heatmap ?? {},
    heatmaps: b.heatmaps ?? {},
    renders: b.renders ?? [],
    created_by: 'agent',
    created_at: now(),
  }
  await c.env.DB.prepare(
    'INSERT INTO revisions (id, project_id, number, title, notes, status, model_seq, graph_key, glb_key, view_key, ifc_key, heatmap, heatmaps, renders, created_by, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
  )
    .bind(r.id, pid, n, r.title, r.notes, r.status, r.model_seq, r.graph_key, r.glb_key, r.view_key, r.ifc_key, JSON.stringify(r.heatmap), JSON.stringify(r.heatmaps), JSON.stringify(r.renders), r.created_by, r.created_at)
    .run()
  await emit(c.env, pid, { type: 'revision.created', revision: r })
  return c.json({ revision: r })
})

worker.patch('/projects/:pid/revisions/:n', async (c) => {
  const pid = c.req.param('pid')
  const b = await body(c)
  const cols = ['title', 'notes', 'status', 'model_seq', 'graph_key', 'glb_key', 'view_key', 'ifc_key', 'heatmap', 'heatmaps', 'renders']
  const json = ['heatmap', 'heatmaps', 'renders']
  const sets: string[] = []
  const vals: unknown[] = []
  for (const k of cols)
    if (k in b) {
      sets.push(`${k} = ?`)
      vals.push(json.includes(k) ? JSON.stringify(b[k]) : b[k])
    }
  if (!sets.length) throw new HttpError(400, 'nothing', 'Nothing to change.')
  await c.env.DB.prepare(`UPDATE revisions SET ${sets.join(', ')} WHERE project_id = ? AND number = ?`).bind(...vals, pid, Number(c.req.param('n'))).run()
  const r = parseRow<any>(await c.env.DB.prepare('SELECT * FROM revisions WHERE project_id = ? AND number = ?').bind(pid, Number(c.req.param('n'))).first(), ['heatmap', 'heatmaps', 'renders'])
  await emit(c.env, pid, { type: 'revision.updated', revision: r })
  return c.json({ revision: r })
})

worker.put('/projects/:pid/estimate', async (c) => {
  const b = (await body(c)) as Estimate
  const prev = await readEstimate(c.env, c.req.param('pid'))
  return c.json({ estimate: await writeEstimate(c.env, c.req.param('pid'), { ...b, measured: true, version: prev.version + 1 }) })
})

worker.post('/projects/:pid/messages', async (c) => {
  const b = await body(c)
  return c.json({ message: await addMessage(c.env, c.req.param('pid'), { role: b.role === 'agent' ? 'agent' : 'system', body: b.body ?? { text: String(b.text ?? '') } }) })
})

worker.post('/projects/:pid/events', async (c) => {
  const b = await body(c)
  await emit(c.env, c.req.param('pid'), ...(Array.isArray(b.events) ? b.events : [b]))
  return c.json({ ok: true })
})

// R2 for the processing worker: `bucket` is uploads (default, private project files) or media (public site files).
// Reads stream with Range; writes are a single PUT (up to ~95 MB) or multipart through the binding.
const bucketOf = (env: Env, b?: string | null) => (b === 'media' ? env.MEDIA : env.UPLOADS)
const cleanKey = (k: unknown) => {
  const key = String(k ?? '').replace(/^\/+/, '')
  if (!key || key.includes('..')) throw new HttpError(400, 'bad_key', 'A key is needed.')
  return key
}
worker.get('/r2', async (c) => serveObject(bucketOf(c.env, c.req.query('bucket')), cleanKey(c.req.query('key')), c.req.raw, { cache: 'no-store' }))
worker.on('HEAD', '/r2', async (c) => {
  const h = await bucketOf(c.env, c.req.query('bucket')).head(cleanKey(c.req.query('key')))
  return h ? c.body(null, 200, { 'Content-Length': String(h.size), ETag: h.httpEtag }) : c.body(null, 404)
})
worker.get('/r2/list', async (c) => {
  const r = await bucketOf(c.env, c.req.query('bucket')).list({ prefix: cleanKey(c.req.query('prefix')), cursor: c.req.query('cursor') || undefined, limit: 1000 })
  return c.json({ objects: r.objects.map((o) => ({ key: o.key, size: o.size })), cursor: r.truncated ? r.cursor : null })
})
worker.put('/r2', async (c) => {
  const len = Number(c.req.header('Content-Length') ?? 0)
  const obj = await bucketOf(c.env, c.req.query('bucket')).put(cleanKey(c.req.query('key')), len > 0 ? c.req.raw.body!.pipeThrough(new FixedLengthStream(len)) : await c.req.arrayBuffer(), {
    httpMetadata: { contentType: c.req.header('Content-Type') || 'application/octet-stream' },
  })
  return c.json({ key: obj?.key, size: obj?.size })
})
worker.post('/r2/create', async (c) => {
  const b = await body(c)
  const up = await bucketOf(c.env, b.bucket).createMultipartUpload(cleanKey(b.key), { httpMetadata: { contentType: b.type || 'application/octet-stream' } })
  return c.json({ key: up.key, uploadId: up.uploadId })
})
worker.put('/r2/part', async (c) => {
  const up = bucketOf(c.env, c.req.query('bucket')).resumeMultipartUpload(cleanKey(c.req.query('key')), c.req.query('uploadId') ?? '')
  const len = Number(c.req.header('Content-Length') ?? 0)
  const part = await up.uploadPart(Number(c.req.query('n')), len > 0 ? c.req.raw.body!.pipeThrough(new FixedLengthStream(len)) : await c.req.arrayBuffer())
  return c.json({ PartNumber: part.partNumber, ETag: part.etag })
})
worker.post('/r2/complete', async (c) => {
  const b = await body(c)
  const obj = await bucketOf(c.env, b.bucket).resumeMultipartUpload(cleanKey(b.key), b.uploadId).complete(b.parts.map((p: any) => ({ partNumber: p.PartNumber, etag: p.ETag })))
  return c.json({ key: obj.key, size: obj.size })
})
// the old names, used by scripts/media-upload-big.mjs
worker.post('/media/create', async (c) => {
  const b = await body(c)
  const up = await c.env.MEDIA.createMultipartUpload(cleanKey(b.key), { httpMetadata: { contentType: b.type || 'application/octet-stream' } })
  return c.json({ key: up.key, uploadId: up.uploadId })
})
worker.put('/media/part', async (c) => {
  const up = c.env.MEDIA.resumeMultipartUpload(cleanKey(c.req.query('key')), c.req.query('uploadId') ?? '')
  const len = Number(c.req.header('Content-Length') ?? 0)
  const part = await up.uploadPart(Number(c.req.query('n')), len > 0 ? c.req.raw.body!.pipeThrough(new FixedLengthStream(len)) : await c.req.arrayBuffer())
  return c.json({ PartNumber: part.partNumber, ETag: part.etag })
})
worker.post('/media/complete', async (c) => {
  const b = await body(c)
  const obj = await c.env.MEDIA.resumeMultipartUpload(cleanKey(b.key), b.uploadId).complete(b.parts.map((p: any) => ({ partNumber: p.PartNumber, etag: p.ETag })))
  return c.json({ key: obj.key, size: obj.size })
})

// the live model, for fits, builds and heatmaps: read it whole, apply ops as a named author, set a finished build
const roomCall = async (env: Env, pid: string, path: string, init?: { method: string; body?: unknown }) => {
  const r = await room(env, pid).fetch(`https://room${path}${path.includes('?') ? '&' : '?'}project_id=${pid}`, {
    method: init?.method ?? 'GET',
    headers: { 'Content-Type': 'application/json' },
    body: init?.body === undefined ? undefined : JSON.stringify({ project_id: pid, ...(init.body as object) }),
  })
  return new Response(r.body, { status: r.status, headers: { 'Content-Type': 'application/json' } })
}
worker.get('/projects/:pid/model', async (c) => {
  const pid = c.req.param('pid')
  const q = new URL(c.req.url).searchParams
  return roomCall(c.env, pid, `/model${q.toString() ? `?${q}` : ''}`)
})
worker.get('/projects/:pid/model/seq', (c) => roomCall(c.env, c.req.param('pid'), '/model/seq'))
worker.post('/projects/:pid/model/ops', async (c) => {
  const b = await body(c)
  return roomCall(c.env, c.req.param('pid'), '/model/ops', {
    method: 'POST',
    body: { batch_id: b.batch_id ?? uuid(), ops: b.ops, note: b.note ?? null, author: b.author ?? { kind: 'agent', id: 'agent:processing', name: 'Moving Atoms' } },
  })
})
worker.post('/projects/:pid/model/base', async (c) => roomCall(c.env, c.req.param('pid'), '/model/base', { method: 'POST', body: await body(c) }))
worker.get('/projects/:pid', async (c) => {
  const p = await loadProject(c.env, c.req.param('pid'))
  if (!p) throw new HttpError(404, 'not_found', 'No such project.')
  const [scans, revisions, files] = await Promise.all([
    projectScans(c.env, p.id),
    projectRevisions(c.env, p.id),
    c.env.DB.prepare("SELECT * FROM files WHERE project_id = ? AND status = 'ready'").bind(p.id).all(),
  ])
  return c.json({ project: projectOut(p), scans, revisions, files: parseRows(files.results, ['meta']) })
})
// the live heatmap (§9 heatmap_live), one per scan, kept on the project and served in the viewer manifest
worker.put('/projects/:pid/live-heatmaps/:scan', async (c) => {
  const pid = c.req.param('pid')
  const p = await loadProject(c.env, pid)
  if (!p) throw new HttpError(404, 'not_found', 'No such project.')
  const settings = { ...(p.settings ?? {}), live_heatmaps: { ...(p.settings?.live_heatmaps ?? {}), [c.req.param('scan')]: await body(c) } }
  await c.env.DB.prepare('UPDATE projects SET settings = ? WHERE id = ?').bind(JSON.stringify(settings), pid).run()
  return c.json({ ok: true })
})
// a file's status once its bytes are in R2 (a link import finished)
worker.post('/files/:id', async (c) => {
  const b = await body(c)
  const f = await c.env.DB.prepare('SELECT * FROM files WHERE id = ?').bind(c.req.param('id')).first<any>()
  if (!f) throw new HttpError(404, 'not_found', 'No such file.')
  await c.env.DB.prepare('UPDATE files SET status = COALESCE(?, status), size_bytes = COALESCE(?, size_bytes), content_type = COALESCE(?, content_type) WHERE id = ?')
    .bind(b.status ?? null, b.size_bytes ?? null, b.content_type ?? null, f.id)
    .run()
  const file = parseRow(await c.env.DB.prepare('SELECT * FROM files WHERE id = ?').bind(f.id).first(), ['meta'])
  await emit(c.env, f.project_id, { type: 'file.updated', file })
  return c.json({ file })
})
// hand a claimed job back to the queue (a worker too small for it, or shutting down)
worker.post('/jobs/:id/release', async (c) => {
  await c.env.DB.prepare("UPDATE jobs SET status = 'queued', claimed_by = NULL, claimed_at = NULL, updated_at = ? WHERE id = ? AND status = 'running'").bind(now(), c.req.param('id')).run()
  return c.json({ ok: true })
})
// queue work from the processing side too (e.g. a build after a fit)
worker.post('/projects/:pid/jobs', async (c) => {
  const b = await body(c)
  const id = uuid()
  const t = now()
  await c.env.DB.prepare("INSERT INTO jobs (id, project_id, type, status, input, created_at, updated_at) VALUES (?, ?, ?, 'queued', ?, ?, ?)")
    .bind(id, c.req.param('pid'), String(b.type), JSON.stringify(b.input ?? {}), t, t)
    .run()
  c.executionCtx.waitUntil(jobQueued(c.env, c.req.param('pid')))
  return c.json({ job: { id, type: b.type, status: 'queued' } })
})

app.route('/worker', worker)

// ---------------------------------------------------------------- everything below needs a signed-in person

app.use('*', async (c, next) => {
  const u = await currentUser(c.env, c.req.raw)
  if (!u) throw new HttpError(401, 'unauthorized', 'Sign in to continue.')
  c.set('user', u)
  await next()
})

// ---------- me

app.get('/me', async (c) => {
  const u = me(c)
  const acc = await myAccount(c).catch(() => null)
  const { results } = await c.env.DB.prepare(
    `SELECT p.id, p.name, p.status, m.role, p.updated_at, p.created_at FROM project_members m JOIN projects p ON p.id = m.project_id
     WHERE m.user_id = ? AND p.status != 'archived' ORDER BY p.last_active_at DESC`,
  )
    .bind(u.id)
    .all()
  return c.json({
    profile: { id: u.id, email: u.email, name: u.name, is_admin: Boolean(u.is_admin) },
    prefs: { chat_show_text: true, ...JSON.parse(u.prefs || '{}') },
    account: acc ? await accountSummary(c.env, acc) : null,
    projects: results,
  })
})

app.patch('/me/prefs', async (c) => {
  const b = await body(c)
  const prefs = { chat_show_text: true, ...JSON.parse(me(c).prefs || '{}') }
  if (typeof b.chat_show_text === 'boolean') prefs.chat_show_text = b.chat_show_text
  await c.env.DB.prepare('UPDATE users SET prefs = ? WHERE id = ?').bind(JSON.stringify(prefs), me(c).id).run()
  return c.json({ prefs })
})

app.post('/me/about', async (c) => {
  const b = await body(c)
  await c.env.DB.prepare('UPDATE users SET company = COALESCE(?, company), role = COALESCE(?, role), name = COALESCE(?, name) WHERE id = ?')
    .bind(b.company?.trim().slice(0, 200) || null, b.role?.trim().slice(0, 80) || null, b.name?.trim().slice(0, 120) || null, me(c).id)
    .run()
  return c.json({ ok: true })
})

// ---------- projects

app.get('/projects', async (c) => {
  const { results } = await c.env.DB.prepare(
    "SELECT p.* FROM project_members m JOIN projects p ON p.id = m.project_id WHERE m.user_id = ? AND p.status != 'archived'",
  )
    .bind(me(c).id)
    .all()
  const cards = await projectCards(c.env, parseRows<ProjectRow>(results, ['settings']))
  return c.json({ projects: cards.sort((a, b) => Date.parse(b.updated) - Date.parse(a.updated)) })
})

app.post('/projects', async (c) => {
  const b = await body(c)
  const name = String(b.name ?? '').trim().slice(0, 200) || 'Untitled project'
  const acc = await myAccount(c)
  const id = uuid()
  const t = now()
  const settings: Record<string, unknown> = {}
  if (b.onboarding) settings.onboarding = true
  if (b.scope) settings.scope = normScope(b.scope)
  const model = c.env.AGENT_MODEL || 'claude-opus-5-5'
  await c.env.DB.batch([
    c.env.DB.prepare(
      "INSERT INTO projects (id, account_id, name, status, model, spend_cap_usd, spend_usd, settings, created_by, created_at, updated_at, last_active_at) VALUES (?, ?, ?, 'setup', ?, ?, 0, ?, ?, ?, ?, ?)",
    ).bind(id, acc, name, model, b.spend_cap_usd ?? null, JSON.stringify(settings), me(c).id, t, t, t),
    c.env.DB.prepare("INSERT INTO project_members (project_id, user_id, role, added_at) VALUES (?, ?, 'owner', ?)").bind(id, me(c).id, t),
  ])
  return c.json({ project: projectOut((await loadProject(c.env, id))!) })
})

app.get('/files/:fid/url', async (c) => {
  const f = await c.env.DB.prepare("SELECT * FROM files WHERE id = ? AND status != 'deleted'").bind(c.req.param('fid')).first<any>()
  if (!f) throw new HttpError(404, 'not_found', 'File not found.')
  await requireProject(c.env, me(c), f.project_id)
  return c.json(await fileLink(c.env, f, c.req.query('download') === '1'))
})

app.patch('/points/:id', async (c) => {
  const pt = await c.env.DB.prepare('SELECT * FROM points WHERE id = ?').bind(c.req.param('id')).first<any>()
  if (!pt) throw new HttpError(404, 'not_found', 'Point not found.')
  await requireProject(c.env, me(c), pt.project_id, 'editor')
  const b = await body(c)
  if (!['open', 'addressed', 'dismissed'].includes(b.status)) throw new HttpError(400, 'bad_status', 'Unknown status.')
  await c.env.DB.prepare('UPDATE points SET status = ? WHERE id = ?').bind(b.status, pt.id).run()
  const point = pointOut(await c.env.DB.prepare('SELECT * FROM points WHERE id = ?').bind(pt.id).first())
  await emit(c.env, pt.project_id, { type: 'point.updated', point })
  return c.json(point)
})

const pointOut = (r: any) => parseRow<any>(r, ['world', 'camera'])

/** Everything under /projects/:pid — reads also serve the view-only link. */
app.all('/projects/:pid/*', async (c) => {
  const pid = c.req.param('pid')
  const { project, role } = await requireProject(c.env, me(c), pid)
  const rest = c.req.path.slice(`/app/api/projects/${pid}`.length)
  if (c.req.method === 'GET') return projectRead(c, project, role, me(c), rest, false)
  return projectWrite(c, project, role, rest)
})
app.get('/projects/:pid', async (c) => {
  const { project, role } = await requireProject(c.env, me(c), c.req.param('pid'))
  return projectRead(c, project, role, me(c), '', false)
})
app.patch('/projects/:pid', async (c) => {
  const { project, role } = await requireProject(c.env, me(c), c.req.param('pid'), 'editor')
  return projectWrite(c, project, role, '')
})

async function modelSeq(env: Env, pid: string): Promise<{ seq: number; base: any }> {
  try {
    const r = await room(env, pid).fetch(`https://room/model/seq?project_id=${pid}`)
    if (r.ok) return (await r.json()) as { seq: number; base: any }
  } catch (e) {
    console.error('model seq', e)
  }
  return { seq: 0, base: null }
}

/** Forward to the project's room (the model API). */
async function toRoom(c: C, pid: string, path: string, init?: { method: string; body?: unknown }) {
  const qs = new URL(c.req.url).search
  const sep = qs ? '&' : '?'
  const r = await room(c.env, pid).fetch(`https://room${path}${qs}${sep}project_id=${pid}`, {
    method: init?.method ?? 'GET',
    headers: { 'Content-Type': 'application/json' },
    body: init?.body === undefined ? undefined : JSON.stringify({ project_id: pid, ...(init.body as object) }),
  })
  return new Response(r.body, { status: r.status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' } })
}

/** A job was queued: the project's room wakes a Cloudflare container if no machine claims it soon. */
async function jobQueued(env: Env, pid: string) {
  try {
    await room(env, pid).fetch('https://room/jobs/queued', { method: 'POST', body: JSON.stringify({ project_id: pid }) })
  } catch (e) {
    console.error('jobQueued', pid, e)
  }
}

async function startTurn(env: Env, pid: string, messageId: number, user: { id: string; email: string; name: string | null }) {
  const r = await room(env, pid).fetch('https://room/turn', { method: 'POST', body: JSON.stringify({ project_id: pid, message_id: messageId, user }) })
  if (!r.ok && r.status !== 202) console.error('turn', pid, r.status, await r.text().catch(() => ''))
}

async function projectRead(c: C, p: ProjectRow, role: Role, user: User, rest: string, isPublic: boolean): Promise<Response> {
  const env = c.env
  const pid = p.id
  const q = (k: string) => c.req.query(k)

  if (rest === '' || rest === '/') {
    if (isPublic) throw new HttpError(404, 'not_found', 'Not on a view-only link.')
    const [scans, revisions, mem, turn, acc] = await Promise.all([
      projectScans(env, pid),
      projectRevisions(env, pid),
      members(env, pid),
      currentTurn(env, pid),
      accountSummary(env, p.account_id),
    ])
    const cap = p.spend_cap_usd == null ? null : Number(p.spend_cap_usd)
    return c.json({
      project: projectOut(p),
      role,
      members: mem,
      scans,
      revisions,
      usage: { project_spent: round2(Number(p.spend_usd)), project_cap: cap, account_balance: acc?.balance ?? null },
      turn: turn ?? null,
    })
  }
  if (rest === '/files') {
    const { results } = await env.DB.prepare("SELECT * FROM files WHERE project_id = ? AND status != 'deleted' ORDER BY created_at DESC").bind(pid).all()
    return c.json(parseRows(results, ['meta']))
  }
  if (rest === '/scans') return c.json(await projectScans(env, pid))
  if (rest === '/revisions') return c.json(await projectRevisions(env, pid))
  if (rest === '/jobs') {
    const { results } = await env.DB.prepare("SELECT id, type, status, stage, progress, error, created_at, updated_at FROM jobs WHERE project_id = ? ORDER BY created_at DESC LIMIT 50").bind(pid).all()
    return c.json(results)
  }
  const job = /^\/jobs\/([^/]+)$/.exec(rest)
  if (job) {
    const j = await env.DB.prepare('SELECT * FROM jobs WHERE id = ? AND project_id = ?').bind(job[1], pid).first()
    if (!j) throw new HttpError(404, 'not_found', 'No such job.')
    return c.json(parseRow(j, ['input', 'result']))
  }
  if (rest === '/messages') {
    const list = await listMessages(env, pid, { before: Number(q('before')) || undefined, limit: Number(q('limit')) || 50 })
    return c.json(list)
  }
  if (rest === '/points') {
    const { results } = await env.DB.prepare('SELECT * FROM points WHERE project_id = ? ORDER BY created_at DESC').bind(pid).all()
    return c.json(results.map(pointOut))
  }
  if (rest === '/views') {
    const { results } = await env.DB.prepare('SELECT * FROM views WHERE project_id = ? ORDER BY created_at').bind(pid).all()
    return c.json(parseRows(results, ['state']))
  }
  if (rest === '/viewer') return c.json(await viewerManifest(env, p, isPublic))
  if (rest === '/model' || rest.startsWith('/model/elements/')) return toRoom(c, pid, rest)
  if (rest === '/estimate') {
    if (isPublic) throw new HttpError(404, 'not_found', 'Not on a view-only link.')
    return c.json({ estimate: await readEstimate(env, pid) })
  }
  if (rest === '/share') {
    if (isPublic) throw new HttpError(404, 'not_found', 'Not on a view-only link.')
    const can = role === 'owner' || Boolean(user.is_admin)
    return c.json({ can_share: can, link: shareLink(env, p) })
  }
  const parts = /^\/uploads\/([^/]+)\/parts$/.exec(rest)
  if (parts && !isPublic) {
    if (role === 'viewer') throw new HttpError(403, 'forbidden', 'Viewers can’t upload.')
    const u = await env.DB.prepare('SELECT * FROM uploads WHERE upload_id = ? AND project_id = ?').bind(decodeURIComponent(parts[1]), pid).first<any>()
    if (!u) return c.json([])
    return c.json(await listParts(env, u.r2_key, u.upload_id))
  }
  throw new HttpError(404, 'not_found', 'Not found.')
}

function shareLink(env: Env, p: ProjectRow) {
  return p.share_token ? { url: `${env.SITE_URL}/app/s/${p.share_token}`, created_at: p.share_created_at, created_by: p.share_created_by } : null
}

/** §11: what the viewer draws — scans' layers, checkpoints, open points, the live model's base. */
async function viewerManifest(env: Env, p: ProjectRow, isPublic: boolean) {
  const pid = p.id
  const [scans, revisions, points, model] = await Promise.all([
    projectScans(env, pid),
    projectRevisions(env, pid),
    isPublic ? Promise.resolve({ results: [] as any[] }) : env.DB.prepare("SELECT * FROM points WHERE project_id = ? AND status = 'open'").bind(pid).all(),
    modelSeq(env, pid),
  ])
  const base = await assetBase(env, pid, isPublic ? 'public' : undefined)
  const prefix = `projects/${pid}/`
  const rel = (k: string | null | undefined) => (k ? k.replace(prefix, '') : null)
  const layer = (l?: { potree_prefix?: string | null; points?: number | null; has_labels?: boolean } | null) =>
    l?.potree_prefix ? { potree: `${rel(l.potree_prefix)}/metadata.json`, points: l.points ?? null, has_labels: Boolean(l.has_labels) } : undefined
  const ready = scans.find((s: any) => s.status === 'ready')
  return {
    assetBase: base,
    frame: ready?.frame ?? null,
    scans: scans.map((s: any) => ({
      id: s.id,
      name: s.name,
      status: s.status,
      points: s.point_count,
      bounds: s.bounds,
      potree: s.potree_prefix ? `${rel(s.potree_prefix)}/metadata.json` : null,
      viewer: { overview: layer(s.viewer?.overview), full: layer(s.viewer?.full ?? (s.potree_prefix ? { potree_prefix: s.potree_prefix, points: s.point_count } : null)) },
      labels: s.labels,
      progress: s.progress,
      stage_detail: s.stage_detail,
    })),
    revisions: revisions.map((r: any) => ({
      number: r.number,
      title: r.title,
      notes: r.notes,
      created_at: r.created_at,
      status: r.status,
      model_seq: r.model_seq,
      glb: rel(r.glb_key),
      view: rel(r.view_key),
      ifc: rel(r.ifc_key),
      heatmap: r.heatmap?.potree_prefix ? { ...r.heatmap, potree: `${rel(r.heatmap.potree_prefix)}/metadata.json` } : r.heatmap,
      heatmaps: r.heatmaps,
    })),
    points: points.results.map(pointOut),
    model: { seq: model.seq, base: model.base },
    live_heatmap: { on: p.settings?.live_heatmap !== false, ...(p.settings?.live_heatmap === false ? { reason: 'paused' } : {}) },
    live_heatmaps: isPublic ? {} : (p.settings?.live_heatmaps ?? {}),
  }
}

async function projectWrite(c: C, p: ProjectRow, role: Role, rest: string): Promise<Response> {
  const env = c.env
  const pid = p.id
  const u = me(c)
  const method = c.req.method
  const need = (r: Role) => {
    const rank = { viewer: 0, editor: 1, owner: 2 }
    if (rank[role] < rank[r]) throw new HttpError(403, 'forbidden', 'You don’t have access to do that here.')
  }

  // ----- the project itself
  if (rest === '' && method === 'PATCH') {
    need('editor')
    const b = await body(c)
    const sets: string[] = []
    const vals: unknown[] = []
    const settings = { ...(p.settings ?? {}) }
    let settingsChanged = false
    if (typeof b.name === 'string' && b.name.trim()) {
      sets.push('name = ?')
      vals.push(b.name.trim().slice(0, 200))
    }
    if ('spend_cap_usd' in b) {
      need('owner')
      sets.push('spend_cap_usd = ?')
      vals.push(b.spend_cap_usd == null ? null : Math.max(0, Number(b.spend_cap_usd)))
    }
    if (b.status === 'archived' || (b.status === 'active' && p.status === 'archived')) {
      need('owner')
      sets.push('status = ?')
      vals.push(b.status)
    }
    if (typeof b.live_heatmap === 'boolean') {
      settings.live_heatmap = b.live_heatmap
      settingsChanged = true
    }
    if (b.scope) {
      settings.scope = normScope({ ...(settings.scope ?? {}), ...b.scope })
      settingsChanged = true
    }
    if (settingsChanged) {
      sets.push('settings = ?')
      vals.push(JSON.stringify(settings))
    }
    if (sets.length) await env.DB.prepare(`UPDATE projects SET ${sets.join(', ')}, updated_at = ? WHERE id = ?`).bind(...vals, now(), pid).run()
    const project = projectOut((await loadProject(env, pid))!)
    await emit(env, pid, { type: 'project.updated', project })
    if (b.scope) c.executionCtx.waitUntil(estimate(env, pid, settings.scope))
    return c.json({ project })
  }

  // ----- members
  if (rest === '/members' && method === 'POST') {
    need('owner')
    const b = await body(c)
    const email = String(b.email ?? '').trim().toLowerCase()
    const r: Role = ['owner', 'editor', 'viewer'].includes(b.role) ? b.role : 'viewer'
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) throw new HttpError(400, 'invalid_email', 'Enter a valid email address.')
    const { user: invitee } = await upsertUser(env, email)
    const had = await env.DB.prepare('SELECT role FROM project_members WHERE project_id = ? AND user_id = ?').bind(pid, invitee.id).first()
    await env.DB.prepare('INSERT INTO project_members (project_id, user_id, role, added_at) VALUES (?, ?, ?, ?) ON CONFLICT(project_id, user_id) DO UPDATE SET role = excluded.role')
      .bind(pid, invitee.id, r, now())
      .run()
    if (!had) {
      const { sendEmail } = await import('../../../src/email')
      c.executionCtx.waitUntil(
        sendEmail(env, {
          to: email,
          subject: `${u.name || u.email} shared “${p.name}” with you on Moving Atoms`,
          text: `${u.name || u.email} added you to “${p.name}” as ${r === 'viewer' ? 'a viewer' : `an ${r}`}.\n\nOpen it: ${env.SITE_URL}/app/p/${pid}\n\nSign in with this email address; we'll send you a code.`,
        }),
      )
    }
    return c.json({ member: { email, role: r, invited: !had } })
  }
  const mem = /^\/members\/([^/]+)$/.exec(rest)
  if (mem && method === 'DELETE') {
    if (mem[1] !== u.id) need('owner')
    const owners = await env.DB.prepare("SELECT COUNT(*) AS n FROM project_members WHERE project_id = ? AND role = 'owner' AND user_id != ?").bind(pid, mem[1]).first<{ n: number }>()
    if (!owners?.n) throw new HttpError(409, 'last_owner', 'A project needs at least one owner.')
    await env.DB.prepare('DELETE FROM project_members WHERE project_id = ? AND user_id = ?').bind(pid, mem[1]).run()
    return c.json({ ok: true })
  }

  // ----- uploads (Uppy's S3 multipart protocol, §4)
  if (rest === '/uploads' && method === 'POST') {
    need('editor')
    const b = await body(c)
    const name = String(b.filename ?? '').replace(/[\\/\0]/g, '_').slice(0, 250)
    if (!name) throw new HttpError(400, 'bad_name', 'A file name is needed.')
    if (Number(b.size) > MAX_UPLOAD) throw new HttpError(413, 'too_big', 'Files can be up to 200 GB. Split it, or send it as a link.')
    const fileId = uuid()
    const key = `projects/${pid}/${isPointCloud(name) ? 'sources' : 'files'}/${fileId}/${name}`
    const up = await env.UPLOADS.createMultipartUpload(key, { httpMetadata: { contentType: b.type || 'application/octet-stream' }, customMetadata: { project: pid, by: u.id } })
    await env.DB.prepare('INSERT INTO uploads (upload_id, project_id, file_id, r2_key, name, size_bytes, content_type, created_by, created_at) VALUES (?,?,?,?,?,?,?,?,?)')
      .bind(up.uploadId, pid, fileId, key, name, Number(b.size) || null, b.type || null, u.id, now())
      .run()
    return c.json({ uploadId: up.uploadId, key, fileId })
  }
  const sign = /^\/uploads\/([^/]+)\/sign$/.exec(rest)
  if (sign && method === 'POST') {
    need('editor')
    const b = await body(c)
    const up = await upload(env, pid, decodeURIComponent(sign[1]))
    const n = Number(b.partNumber)
    if (!(n >= 1 && n <= 10000)) throw new HttpError(400, 'bad_part', 'Part numbers run 1–10000.')
    return c.json({ url: await partUrl(env, up.r2_key, up.upload_id, n, `/app/api/projects/${pid}/uploads/${encodeURIComponent(up.upload_id)}/part/${n}`) })
  }
  const done = /^\/uploads\/([^/]+)\/complete$/.exec(rest)
  if (done && method === 'POST') {
    need('editor')
    const b = await body(c)
    const up = await upload(env, pid, decodeURIComponent(done[1]))
    const obj = await completeUpload(env, up.r2_key, up.upload_id, b.parts ?? [])
    return c.json(await fileArrived(c, p, up, obj.size))
  }
  const abort = /^\/uploads\/([^/]+)$/.exec(rest)
  if (abort && method === 'DELETE') {
    need('editor')
    const up = await env.DB.prepare('SELECT * FROM uploads WHERE upload_id = ? AND project_id = ?').bind(decodeURIComponent(abort[1]), pid).first<any>()
    if (up) {
      await abortUpload(env, up.r2_key, up.upload_id)
      await env.DB.prepare('DELETE FROM uploads WHERE upload_id = ?').bind(up.upload_id).run()
    }
    return c.json({ ok: true })
  }

  // ----- a scan from a link (§4 imports): the processing worker fetches it
  if (rest === '/imports' && method === 'POST') {
    need('editor')
    const b = await body(c)
    let url: URL
    try {
      url = new URL(String(b.url ?? ''))
      if (!/^https?:$/.test(url.protocol)) throw new Error()
    } catch {
      throw new HttpError(400, 'bad_url', 'Paste a full https:// link to the scan.')
    }
    const name = decodeURIComponent(url.pathname.split('/').pop() || 'imported-scan').slice(0, 250)
    const fileId = uuid()
    const t = now()
    const f = { id: fileId, project_id: pid, kind: 'source', name, r2_key: `projects/${pid}/sources/${fileId}/${name}`, size_bytes: null, content_type: null, status: 'uploading', created_by: u.id, created_at: t }
    const scan = { id: uuid(), project_id: pid, file_id: fileId, name, status: 'importing', stage_detail: 'Copying from the link', progress: 0, created_at: t, updated_at: t }
    const jobId = uuid()
    await env.DB.batch([
      env.DB.prepare('INSERT INTO files (id, project_id, kind, name, r2_key, status, created_by, created_at) VALUES (?,?,?,?,?,?,?,?)').bind(f.id, pid, f.kind, name, f.r2_key, f.status, u.id, t),
      env.DB.prepare('INSERT INTO scans (id, project_id, file_id, name, status, stage_detail, progress, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)').bind(scan.id, pid, fileId, name, scan.status, scan.stage_detail, 0, t, t),
      env.DB.prepare("INSERT INTO jobs (id, project_id, type, status, input, created_at, updated_at) VALUES (?, ?, 'link_import', 'queued', ?, ?, ?)").bind(
        jobId,
        pid,
        JSON.stringify({ url: url.toString(), file_id: fileId, scan_id: scan.id, r2_key: f.r2_key }),
        t,
        t,
      ),
      env.DB.prepare("UPDATE projects SET status = CASE WHEN status = 'setup' THEN 'processing' ELSE status END, updated_at = ?, last_active_at = ? WHERE id = ?").bind(t, t, pid),
    ])
    const full = parseRow<any>(await env.DB.prepare('SELECT * FROM scans WHERE id = ?').bind(scan.id).first(), SCAN_JSON)
    await emit(env, pid, { type: 'file.created', file: f }, { type: 'scan.updated', scan: full })
    c.executionCtx.waitUntil(jobQueued(env, pid))
    return c.json({ job: { id: jobId, type: 'link_import', status: 'queued' }, file: f, scan: full })
  }

  // ----- fit to scan (§17.5): a model_fit job for the processing worker
  if (rest === '/model/fit' && method === 'POST') {
    need('editor')
    const b = await body(c)
    const ids = [...new Set((b.element_ids ?? []) as string[])].slice(0, 500)
    if (!ids.length) throw new HttpError(400, 'nothing', 'Select something to fit.')
    const id = uuid()
    const t = now()
    await env.DB.prepare("INSERT INTO jobs (id, project_id, type, status, input, created_at, updated_at) VALUES (?, ?, 'model_fit', 'queued', ?, ?, ?)")
      .bind(id, pid, JSON.stringify({ element_ids: ids, by: u.id }), t, t)
      .run()
    const job = { id, type: 'model_fit', status: 'queued', stage: null, progress: 0 }
    await emit(env, pid, { type: 'job.updated', id, type_: 'model_fit', status: 'queued', stage: null, progress: 0, job })
    c.executionCtx.waitUntil(jobQueued(env, pid))
    return c.json({ job })
  }

  // ----- the live model (the room)
  if (rest === '/model/ops' || rest === '/model/undo' || rest === '/model/redo') {
    need('editor')
    const b = await body(c)
    return toRoom(c, pid, rest, { method: 'POST', body: { ...b, author: { kind: 'user', id: `user:${u.id}`, name: u.name || u.email } } })
  }

  // ----- saved views
  if (rest === '/views' && method === 'POST') {
    need('editor')
    const b = await body(c)
    const t = now()
    const view = { id: uuid(), name: String(b.name ?? 'View').slice(0, 120), state: b.state ?? {}, created_by: u.id, author: u.name || u.email, created_at: t, updated_at: t }
    await env.DB.prepare('INSERT INTO views (id, project_id, name, state, created_by, author, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)')
      .bind(view.id, pid, view.name, JSON.stringify(view.state), u.id, view.author, t, t)
      .run()
    await emit(env, pid, { type: 'views.changed' })
    return c.json({ view })
  }
  const vw = /^\/views\/([^/]+)$/.exec(rest)
  if (vw) {
    need('editor')
    if (method === 'DELETE') {
      await env.DB.prepare('DELETE FROM views WHERE id = ? AND project_id = ?').bind(vw[1], pid).run()
      await emit(env, pid, { type: 'views.changed' })
      return c.json({ ok: true })
    }
    const b = await body(c)
    await env.DB.prepare('UPDATE views SET name = COALESCE(?, name), state = COALESCE(?, state), updated_at = ? WHERE id = ? AND project_id = ?')
      .bind(b.name ? String(b.name).slice(0, 120) : null, b.state ? JSON.stringify(b.state) : null, now(), vw[1], pid)
      .run()
    const view = parseRow(await env.DB.prepare('SELECT * FROM views WHERE id = ?').bind(vw[1]).first(), ['state'])
    if (!view) throw new HttpError(404, 'not_found', 'View not found.')
    await emit(env, pid, { type: 'views.changed' })
    return c.json({ view })
  }

  // ----- chat (§8, §12)
  if (rest === '/messages' && method === 'POST') {
    need('editor')
    const b = await body(c)
    const text = String(b.text ?? '').slice(0, 20000)
    const blocks: any[] = (Array.isArray(b.file_ids) ? b.file_ids : []).slice(0, 20).map((id: string) => ({ type: 'file', file_id: String(id) }))
    if (Array.isArray(b.element_ids) && b.element_ids.length) blocks.push({ type: 'selection', element_ids: b.element_ids.slice(0, 500).map(String), label: b.selection_label })
    const turn = await currentTurn(env, pid)
    const msgBody: Record<string, unknown> = { text, blocks, queued: Boolean(turn) }
    if (b.start) {
      msgBody.start = b.start
      const settings = { ...(p.settings ?? {}), started: now() }
      await env.DB.prepare('UPDATE projects SET settings = ? WHERE id = ?').bind(JSON.stringify(settings), pid).run()
      await emit(env, pid, { type: 'project.updated', project: { id: pid, started: settings.started } })
    }
    const message = await addMessage(env, pid, { role: 'user', author_id: u.id, body: msgBody })
    await touchProject(env, pid)
    c.executionCtx.waitUntil(startTurn(env, pid, message.id, publicUser(u)))
    return c.json({ message, turn: turn ?? null })
  }
  const ans = /^\/messages\/(\d+)\/answer$/.exec(rest)
  if (ans && method === 'POST') {
    need('editor')
    const m = await getMessage(env, pid, Number(ans[1]))
    const card = m?.body.blocks?.find((x: any) => x.type === 'question')
    if (!m || !card) throw new HttpError(404, 'not_found', 'Question not found.')
    if (m.body.answer) throw new HttpError(409, 'already_answered', 'Someone already answered this.')
    const given = ((await body(c)).answers ?? {}) as Record<string, string>
    const answers = Object.fromEntries(
      Object.entries(given)
        .filter(([, v]) => typeof v === 'string' && v.trim())
        .map(([k, v]) => [k, [v.trim().slice(0, 4000)]]),
    )
    await setBody(env, pid, m.id, { ...m.body, answer: { by: u.id, name: u.name ?? u.email, at: now(), answers } })
    const asked = (card.questions as any[]).filter((q) => answers[q.id])
    const text =
      asked.length === 1 && card.questions.length === 1
        ? answers[asked[0].id][0]
        : asked.map((q) => `**${String(q.question).split('?')[0]}?** ${answers[q.id][0]}`).join('\n\n')
    const turn = await currentTurn(env, pid)
    const message = await addMessage(env, pid, { role: 'user', author_id: u.id, body: { text, blocks: [], queued: Boolean(turn), answer_to: { message_id: m.id, question: card.id } } })
    c.executionCtx.waitUntil(startTurn(env, pid, message.id, publicUser(u)))
    return c.json({ message, turn: turn ?? null })
  }
  if (rest === '/stop' && method === 'POST') {
    need('editor')
    return toRoom(c, pid, '/stop', { method: 'POST', body: {} })
  }

  // ----- points (§4): a spot in the scan or the model, with a note for the agent
  if (rest === '/points' && method === 'POST') {
    need('editor')
    const b = await body(c)
    if (!Array.isArray(b.world) || b.world.length !== 3) throw new HttpError(400, 'bad_point', 'A point needs world coordinates.')
    const point = {
      id: uuid(),
      project_id: pid,
      author_id: u.id,
      revision_number: b.revision_number ?? null,
      side: b.side === 'model' ? 'model' : 'scan',
      world: b.world.map(Number),
      element_id: b.element_id ?? null,
      camera: b.camera ?? null,
      note: b.note ? String(b.note).slice(0, 4000) : null,
      request_id: b.request_id ?? null,
      status: 'open',
      response: null,
      addressed_in_revision: null,
      created_at: now(),
    }
    await env.DB.prepare(
      'INSERT INTO points (id, project_id, author_id, revision_number, side, world, element_id, camera, note, request_id, status, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
    )
      .bind(point.id, pid, u.id, point.revision_number, point.side, JSON.stringify(point.world), point.element_id, point.camera ? JSON.stringify(point.camera) : null, point.note, point.request_id, 'open', point.created_at)
      .run()
    await emit(env, pid, { type: 'point.created', point })
    const turn = await currentTurn(env, pid)
    const message = await addMessage(env, pid, { role: 'user', author_id: u.id, body: { text: point.note || '', blocks: [{ type: 'point', point_id: point.id }], queued: Boolean(turn) } })
    c.executionCtx.waitUntil(startTurn(env, pid, message.id, publicUser(u)))
    return c.json({ point, message })
  }

  // ----- the estimate (§19): POST re-prices with a changed scope (and keeps it on the project)
  if (rest === '/estimate' && method === 'POST') {
    need('editor')
    const b = await body(c)
    const scope = normScope({ ...(p.settings?.scope ?? {}), ...b })
    await env.DB.prepare('UPDATE projects SET settings = ? WHERE id = ?').bind(JSON.stringify({ ...(p.settings ?? {}), scope }), pid).run()
    await emit(env, pid, { type: 'project.updated', project: { id: pid, scope } })
    return c.json({ estimate: await estimate(env, pid, scope) })
  }

  // ----- the view-only link (§20)
  if (rest === '/share' || rest === '/share/renew') {
    if (role !== 'owner' && !u.is_admin) throw new HttpError(403, 'forbidden', 'Only the project’s owners can share it.')
    if (method === 'DELETE') {
      await env.DB.prepare('UPDATE projects SET share_token = NULL, share_created_at = NULL, share_created_by = NULL WHERE id = ?').bind(pid).run()
      return c.json({ link: null })
    }
    if (method === 'POST') {
      if (rest === '/share' && p.share_token) return c.json({ link: shareLink(env, p) })
      const token = randomToken(18)
      await env.DB.prepare('UPDATE projects SET share_token = ?, share_created_at = ?, share_created_by = ? WHERE id = ?').bind(token, now(), u.id, pid).run()
      return c.json({ link: shareLink(env, (await loadProject(env, pid))!) })
    }
  }

  throw new HttpError(404, 'not_found', 'Not found.')
}

async function upload(env: Env, pid: string, uploadId: string) {
  const up = await env.DB.prepare('SELECT * FROM uploads WHERE upload_id = ? AND project_id = ?').bind(uploadId, pid).first<any>()
  if (!up) throw new HttpError(404, 'upload_not_found', 'That upload has expired. Start it again.')
  return up
}

/** A finished upload becomes a project file; a point cloud also becomes a scan queued for ingest. */
async function fileArrived(c: C, p: ProjectRow, up: any, size: number) {
  const env = c.env
  const pid = p.id
  const u = me(c)
  const t = now()
  const src = isPointCloud(up.name)
  const f = {
    id: up.file_id,
    project_id: pid,
    kind: src ? 'source' : 'upload',
    name: up.name,
    r2_key: up.r2_key,
    size_bytes: size,
    content_type: up.content_type,
    status: 'ready',
    created_by: u.id,
    created_at: t,
  }
  const stmts = [
    env.DB.prepare('INSERT OR REPLACE INTO files (id, project_id, kind, name, r2_key, size_bytes, content_type, status, created_by, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)').bind(
      f.id,
      pid,
      f.kind,
      f.name,
      f.r2_key,
      size,
      f.content_type,
      'ready',
      u.id,
      t,
    ),
    env.DB.prepare('DELETE FROM uploads WHERE upload_id = ?').bind(up.upload_id),
  ]
  let scan: any = null
  if (src) {
    const ext = up.name.split('.').pop()?.toUpperCase()
    scan = {
      id: uuid(),
      project_id: pid,
      file_id: f.id,
      name: up.name,
      status: 'queued',
      stage_detail: 'Waiting for a processing slot',
      progress: 0,
      point_count: null,
      bounds: null,
      frame: null,
      copc_key: null,
      potree_prefix: null,
      labels: null,
      overview: null,
      brief: { source: { name: up.name, bytes: size, format: ext } },
      viewer: null,
      error: null,
      created_at: t,
      updated_at: t,
    }
    stmts.push(
      env.DB.prepare('INSERT INTO scans (id, project_id, file_id, name, status, stage_detail, progress, brief, created_at, updated_at) VALUES (?,?,?,?,?,?,0,?,?,?)').bind(
        scan.id,
        pid,
        f.id,
        up.name,
        'queued',
        scan.stage_detail,
        JSON.stringify(scan.brief),
        t,
        t,
      ),
      env.DB.prepare("INSERT INTO jobs (id, project_id, type, status, input, created_at, updated_at) VALUES (?, ?, 'ingest', 'queued', ?, ?, ?)").bind(
        uuid(),
        pid,
        JSON.stringify({ scan_id: scan.id, file_id: f.id, r2_key: up.r2_key, size }),
        t,
        t,
      ),
      env.DB.prepare("UPDATE projects SET status = CASE WHEN status = 'setup' THEN 'processing' ELSE status END, updated_at = ?, last_active_at = ? WHERE id = ?").bind(t, t, pid),
    )
  }
  await env.DB.batch(stmts)
  await emit(env, pid, { type: 'file.created', file: f }, ...(scan ? [{ type: 'scan.updated', scan }, { type: 'project.updated', project: { id: pid, status: p.status === 'setup' ? 'processing' : p.status } }] : []))
  await addMessage(env, pid, { role: 'system', body: { text: `${u.name || u.email} uploaded **${up.name}**.`, blocks: [{ type: 'file', file_id: f.id }] } })
  if (src) c.executionCtx.waitUntil(Promise.all([estimate(env, pid, p.settings?.scope), jobQueued(env, pid)]))
  return { file: f, scan }
}

// ---------- account and billing (§14)

app.get('/account', async (c) => {
  const acc = await myAccount(c)
  const { results } = await c.env.DB.prepare(
    "SELECT m.user_id, u.email, u.name, m.role, u.created_at AS added_at FROM account_members m JOIN users u ON u.id = m.user_id WHERE m.account_id = ?",
  )
    .bind(acc)
    .all()
  return c.json({ account: await accountSummary(c.env, acc), members: results })
})

app.get('/account/ledger', async (c) => {
  const acc = await myAccount(c)
  const before = Number(c.req.query('before')) || Number.MAX_SAFE_INTEGER
  const limit = Math.min(200, Number(c.req.query('limit')) || 50)
  const { results } = await c.env.DB.prepare(
    'SELECT l.*, p.name AS project_name FROM ledger l LEFT JOIN projects p ON p.id = l.project_id WHERE l.account_id = ? AND l.id < ? ORDER BY l.id DESC LIMIT ?',
  )
    .bind(acc, before, limit)
    .all()
  return c.json(parseRows(results, ['meta']))
})

app.get('/account/usage', async (c) => {
  const acc = await myAccount(c)
  const days = Math.min(366, Math.max(1, Number(c.req.query('days')) || 30))
  const since = new Date(Date.now() - days * 86_400_000).toISOString()
  const { results } = await c.env.DB.prepare(
    "SELECT l.amount, l.created_at, l.project_id, l.meta, p.name FROM ledger l LEFT JOIN projects p ON p.id = l.project_id WHERE l.account_id = ? AND l.kind = 'usage' AND l.created_at >= ?",
  )
    .bind(acc, since)
    .all<any>()
  const byDay = new Map<string, number>()
  const byProject = new Map<string, { project_id: string; name: string; amount: number }>()
  const byModel = new Map<string, { model: string; amount: number; input_tokens: number; output_tokens: number }>()
  let total = 0
  for (const r of results) {
    const amt = -Number(r.amount)
    total += amt
    const d = r.created_at.slice(0, 10)
    byDay.set(d, (byDay.get(d) ?? 0) + amt)
    if (r.project_id) {
      const x = byProject.get(r.project_id) ?? { project_id: r.project_id, name: r.name ?? 'Project', amount: 0 }
      x.amount += amt
      byProject.set(r.project_id, x)
    }
    const meta = r.meta ? JSON.parse(r.meta) : {}
    const model = meta.model ?? 'other'
    const m = byModel.get(model) ?? { model, amount: 0, input_tokens: 0, output_tokens: 0 }
    m.amount += amt
    m.input_tokens += Number(meta.input_tokens ?? 0)
    m.output_tokens += Number(meta.output_tokens ?? 0)
    byModel.set(model, m)
  }
  const r2 = <T extends { amount: number }>(x: T) => ({ ...x, amount: round2(x.amount) })
  return c.json({
    days,
    total: round2(total),
    by_day: [...byDay].sort().map(([day, amount]) => ({ day, amount: round2(amount) })),
    by_project: [...byProject.values()].map(r2).sort((a, b) => b.amount - a.amount),
    by_model: [...byModel.values()].map(r2).sort((a, b) => b.amount - a.amount),
  })
})

app.get('/billing', async (c) => {
  const [b, s, acc] = await Promise.all([billingSettings(c.env), platformSettings(c.env), myAccount(c).then((a) => accountSummary(c.env, a))])
  return c.json({ ...b, starting_credits: s.starting_credits, balance: acc?.balance ?? 0, payments: Boolean(c.env.STRIPE_SECRET_KEY) })
})

async function stripe(env: Env, path: string, form?: Record<string, string>) {
  if (!env.STRIPE_SECRET_KEY) throw new HttpError(503, 'payments_off', 'Payments aren’t switched on yet.')
  const r = await fetch(`https://api.stripe.com/v1/${path}`, {
    method: form ? 'POST' : 'GET',
    headers: { Authorization: `Bearer ${env.STRIPE_SECRET_KEY}`, ...(form ? { 'Content-Type': 'application/x-www-form-urlencoded' } : {}) },
    body: form ? new URLSearchParams(form) : undefined,
  })
  const j = (await r.json()) as any
  if (!r.ok) throw new HttpError(502, 'stripe_error', j?.error?.message ?? 'Stripe refused the request.')
  return j
}

app.post('/billing/checkout', async (c) => {
  const b = await body(c)
  const acc = await myAccount(c)
  const s = await billingSettings(c.env)
  let credits = Math.max(s.min_credits, Math.ceil(Number(b.credits || 0) / s.round_to) * s.round_to)
  if (s.max_credits) credits = Math.min(credits, s.max_credits)
  const amount = round2(credits * s.usd_per_credit)
  const pid = b.project_id && (await loadProject(c.env, b.project_id)) ? String(b.project_id) : null
  if (pid) await requireProject(c.env, me(c), pid)
  const back = pid ? `${c.env.SITE_URL}/app/p/${pid}` : `${c.env.SITE_URL}/app/account`
  const session = await stripe(c.env, 'checkout/sessions', {
    mode: 'payment',
    'line_items[0][quantity]': '1',
    'line_items[0][price_data][currency]': s.currency,
    'line_items[0][price_data][unit_amount]': String(Math.round(amount * 100)),
    'line_items[0][price_data][product_data][name]': `${credits.toLocaleString('en-US')} Moving Atoms credits`,
    customer_email: me(c).email,
    client_reference_id: acc,
    'metadata[account_id]': acc,
    'metadata[credits]': String(credits),
    ...(pid ? { 'metadata[project_id]': pid } : {}),
    success_url: `${back}?topup={CHECKOUT_SESSION_ID}`,
    cancel_url: `${back}?topup=cancel`,
  })
  await c.env.DB.prepare("INSERT INTO checkouts (session_id, account_id, project_id, credits, amount_usd, status, created_by, created_at) VALUES (?, ?, ?, ?, ?, 'open', ?, ?)")
    .bind(session.id, acc, pid, credits, amount, me(c).id, now())
    .run()
  return c.json({ url: session.url, session_id: session.id, credits, amount_usd: amount })
})

app.post('/billing/confirm', async (c) => {
  const sid = String((await body(c)).session_id ?? '')
  const acc = await myAccount(c)
  const row = await c.env.DB.prepare('SELECT * FROM checkouts WHERE session_id = ? AND account_id = ?').bind(sid, acc).first<any>()
  if (!row) throw new HttpError(404, 'not_found', 'Checkout not found.')
  const s = await stripe(c.env, `checkout/sessions/${encodeURIComponent(sid)}`)
  const summary = async () => (await accountSummary(c.env, acc))!.balance
  if (s.metadata?.account_id !== acc || Number(s.metadata?.credits) !== row.credits) return c.json({ status: 'mismatch', credits: row.credits, balance: await summary(), applied: false })
  if (s.payment_status === 'paid' || s.payment_status === 'no_payment_required') {
    const entry = await postLedger(c.env, acc, 'topup', row.credits, { project_id: row.project_id, ref: `stripe:${sid}`, meta: { amount_usd: row.amount_usd, session_id: sid } })
    if (entry) await c.env.DB.prepare("UPDATE checkouts SET status = 'paid', applied_at = ? WHERE session_id = ?").bind(now(), sid).run()
    const account = await accountSummary(c.env, acc)
    if (row.project_id) await emit(c.env, row.project_id, { type: 'account.updated', account })
    return c.json({ status: 'paid', credits: row.credits, balance: account!.balance, applied: true })
  }
  const status = s.status === 'expired' ? 'expired' : s.status === 'complete' ? 'processing' : 'open'
  return c.json({ status, credits: row.credits, balance: await summary(), applied: false })
})

// ---------- admin

app.get('/admin/projects', async (c) => {
  requireAdmin(c)
  const { results } = await c.env.DB.prepare(
    "SELECT p.*, a.name AS acc_name, u.email AS owner_email FROM projects p JOIN accounts a ON a.id = p.account_id LEFT JOIN users u ON u.id = a.owner_id WHERE p.status != 'archived' ORDER BY p.last_active_at DESC LIMIT 500",
  ).all<any>()
  const rows = parseRows<ProjectRow & { acc_name: string; owner_email: string }>(results, ['settings'])
  const cards = await projectCards(c.env, rows)
  return c.json({
    projects: cards.map(({ images: _i, ...card }, i) => ({ ...card, account: { id: rows[i].account_id, name: rows[i].acc_name, owner_email: rows[i].owner_email ?? null } })),
  })
})

app.get('/admin/accounts', async (c) => {
  requireAdmin(c)
  const since = new Date(Date.now() - 30 * 86_400_000).toISOString()
  const { results } = await c.env.DB.prepare(
    `SELECT a.id, a.name, u.email AS owner_email, a.balance, a.created_at,
       COALESCE((SELECT -SUM(amount) FROM ledger l WHERE l.account_id = a.id AND l.kind = 'usage' AND l.created_at >= ?), 0) AS spent_30d
     FROM accounts a LEFT JOIN users u ON u.id = a.owner_id ORDER BY a.created_at DESC LIMIT 1000`,
  )
    .bind(since)
    .all<any>()
  return c.json(results.map((r) => ({ ...r, balance: round2(r.balance), spent_30d: round2(r.spent_30d) })))
})

app.post('/admin/accounts/:aid/credits', async (c) => {
  requireAdmin(c)
  const b = await body(c)
  const amount = Number(b.amount)
  if (!Number.isFinite(amount) || amount === 0) throw new HttpError(400, 'bad_amount', 'Enter an amount.')
  const entry = await postLedger(c.env, c.req.param('aid'), amount > 0 ? 'grant' : 'adjustment', amount, { meta: { note: String(b.note ?? '').slice(0, 300), by: me(c).email } })
  if (!entry) throw new HttpError(404, 'not_found', 'Account not found.')
  const account = await accountSummary(c.env, c.req.param('aid'))
  const { results } = await c.env.DB.prepare("SELECT id FROM projects WHERE account_id = ? AND status != 'archived'").bind(c.req.param('aid')).all<{ id: string }>()
  c.executionCtx.waitUntil(Promise.all(results.map((p) => emit(c.env, p.id, { type: 'account.updated', account }))))
  return c.json({ entry: { id: entry.id, kind: amount > 0 ? 'grant' : 'adjustment', amount }, balance: account!.balance })
})

app.get('/admin/settings', async (c) => {
  requireAdmin(c)
  return c.json(await platformSettings(c.env))
})

app.patch('/admin/settings', async (c) => {
  requireAdmin(c)
  const b = await body(c)
  const s = await platformSettings(c.env)
  for (const k of ['starting_credits', 'markup', 'low_balance'] as const) if (Number.isFinite(Number(b[k]))) s[k] = Number(b[k])
  if (b.prices && typeof b.prices === 'object') s.prices = { ...s.prices, ...b.prices }
  await c.env.DB.prepare("UPDATE settings SET value = ? WHERE key = 'platform'").bind(JSON.stringify(s)).run()
  return c.json(s)
})

// the part relay runs before the session check (the signed URL is its credential)
const relay = new Hono<{ Bindings: Env }>().basePath('/app/api')
relay.onError((e) => errorResponse(e))
relay.put('/projects/:pid/uploads/:uid/part/:n', async (c) => {
  const up = await c.env.DB.prepare('SELECT r2_key FROM uploads WHERE upload_id = ? AND project_id = ?').bind(decodeURIComponent(c.req.param('uid')), c.req.param('pid')).first<{ r2_key: string }>()
  if (!up) throw new HttpError(404, 'upload_not_found', 'That upload has expired. Start it again.')
  return relayPart(c.env, c.req.raw, c.req.query('t') ?? null, { key: up.r2_key, uploadId: decodeURIComponent(c.req.param('uid')), partNumber: Number(c.req.param('n')) })
})

const appHandler = handle(app)
const relayHandler = handle(relay)
export const onRequest: PagesFunction<Env> = (ctx) =>
  ctx.request.method === 'PUT' && /\/uploads\/[^/]+\/part\/\d+$/.test(new URL(ctx.request.url).pathname) ? relayHandler(ctx as never) : appHandler(ctx as never)
