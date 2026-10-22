// Projects: who may do what, rows in the app's shapes, the projects page's card, live events and asset links.
import type { Env } from './env'
import type { User } from './auth'
import { HttpError, now, parseRow, parseRows, signToken, verifyToken } from './util'

export type Role = 'owner' | 'editor' | 'viewer'
const RANK: Record<Role, number> = { viewer: 0, editor: 1, owner: 2 }

export interface ProjectRow {
  id: string
  account_id: string
  name: string
  status: string
  model: string
  spend_cap_usd: number | null
  spend_usd: number
  container_state: string
  settings: Record<string, any>
  share_token: string | null
  share_created_at: string | null
  share_created_by: string | null
  created_by: string | null
  created_at: string
  updated_at: string
  last_active_at: string
}

export const SCAN_JSON = ['bounds', 'frame', 'labels', 'overview', 'brief', 'viewer']
export const REV_JSON = ['heatmap', 'heatmaps', 'renders']

export async function loadProject(env: Env, pid: string): Promise<ProjectRow | null> {
  if (!/^[0-9a-f-]{36}$/.test(pid)) return null
  return parseRow<ProjectRow>(await env.DB.prepare('SELECT * FROM projects WHERE id = ?').bind(pid).first(), ['settings'])
}

/** The person's role on the project: their membership, or owner for an admin. Null when they have none. */
export async function roleOn(env: Env, user: User, pid: string): Promise<Role | null> {
  const m = await env.DB.prepare('SELECT role FROM project_members WHERE project_id = ? AND user_id = ?').bind(pid, user.id).first<{ role: Role }>()
  if (m) return m.role
  return user.is_admin ? 'owner' : null
}

/** The project and the person's role, or 404 (also when they can't see it) / 403 (not enough role). */
export async function requireProject(env: Env, user: User, pid: string, need: Role = 'viewer') {
  const p = await loadProject(env, pid)
  const role = p ? await roleOn(env, user, pid) : null
  if (!p || !role) throw new HttpError(404, 'not_found', 'Project not found.')
  if (RANK[role] < RANK[need]) throw new HttpError(403, 'forbidden', 'You don’t have access to do that here.')
  return { project: p, role }
}

/** A project as the app reads it (`Project` in types.ts). */
export function projectOut(p: ProjectRow) {
  const s = p.settings ?? {}
  return {
    id: p.id,
    name: p.name,
    status: p.status,
    spend_cap_usd: p.spend_cap_usd,
    spend_usd: p.spend_usd,
    model: p.model,
    container_state: p.container_state,
    created_at: p.created_at,
    updated_at: p.updated_at,
    last_active_at: p.last_active_at,
    onboarding: Boolean(s.onboarding),
    scope: s.scope ?? null,
    started: s.started ?? null,
    live_heatmap: s.live_heatmap ?? null,
  }
}

export async function touchProject(env: Env, pid: string) {
  const t = now()
  await env.DB.prepare('UPDATE projects SET updated_at = ?, last_active_at = ? WHERE id = ?').bind(t, t, pid).run()
}

// ---------- live events (§5): the project's room fans them out to every open socket ----------

export function room(env: Env, pid: string) {
  return env.PROJECT_ROOM.get(env.PROJECT_ROOM.idFromName(pid))
}

export async function emit(env: Env, pid: string, ...events: Record<string, unknown>[]) {
  try {
    await room(env, pid).fetch('https://room/emit', { method: 'POST', body: JSON.stringify({ project_id: pid, events }) })
  } catch (e) {
    console.error('emit', pid, e)
  }
}

// ---------- asset links (§11): the viewer's assetBase, a signed prefix into the project's R2 files ----------

const ASSET_TTL = 6 * 3600

/** `/app/a/<pid>.<token>/` — everything under it maps to R2 `projects/<pid>/…` (and the shared `public/` fixtures). */
export async function assetBase(env: Env, pid: string, share?: string) {
  const t = await signToken(env.SESSION_SECRET, { p: pid, exp: Math.floor(Date.now() / 1000) + ASSET_TTL, typ: 'asset', ...(share ? { s: 1 } : {}) })
  return `/app/a/${pid}.${t}/`
}

export async function checkAssetToken(env: Env, pid: string, token: string) {
  const t = await verifyToken<{ p: string; typ: string }>(env.SESSION_SECRET, token)
  return Boolean(t && t.typ === 'asset' && t.p === pid)
}

/** A one-hour download link for a file (`GET /files/:id/url`). */
export async function fileLink(env: Env, f: { id: string; project_id: string; r2_key: string; name: string }, download: boolean) {
  const exp = Math.floor(Date.now() / 1000) + 3600
  const t = await signToken(env.SESSION_SECRET, { f: f.id, k: f.r2_key, exp, typ: 'file', ...(download ? { d: 1 } : {}) })
  return { url: `/app/f/${encodeURIComponent(t)}/${encodeURIComponent(f.name)}`, expires: 3600, name: f.name }
}

// ---------- the projects page's card (CONTRACTS §4 GET /api/projects; server/src/projectCard.ts) ----------

const HAND_OVER = ['RVT', 'IFC', 'DWG', 'NWD', 'NWC', 'DXF', 'STEP', 'GLB', 'PDF', 'XLSX', 'CSV']
const rank = (k: string) => (HAND_OVER.includes(k) ? HAND_OVER.indexOf(k) : HAND_OVER.length)
const extOf = (name: string) => (/\.([A-Za-z0-9]{2,5})$/.exec(name)?.[1] ?? '').toUpperCase()
const SPAN: Record<string, [number, number]> = {
  queued: [0, 0],
  inspecting: [0, 0.05],
  decoding: [0.05, 0.45],
  labelling: [0.45, 0.65],
  converting: [0.65, 0.95],
  overview: [0.95, 1],
}
const fraction = (v: number) => Math.max(0, Math.min(1, v > 1 ? v / 100 : v))

export async function projectCards(env: Env, projects: ProjectRow[]) {
  if (!projects.length) return []
  const ids = projects.map((p) => p.id)
  const ph = ids.map(() => '?').join(',')
  const [scans, files, waits, turns, revs] = await Promise.all([
    env.DB.prepare(`SELECT project_id, status, progress, created_at FROM scans WHERE project_id IN (${ph}) ORDER BY created_at`).bind(...ids).all<any>(),
    env.DB.prepare(`SELECT id, project_id, kind, name, r2_key FROM files WHERE project_id IN (${ph}) AND status = 'ready' AND kind IN ('deliverable','image')`).bind(...ids).all<any>(),
    // an agent question or point request after the person's last message
    env.DB.prepare(
      `SELECT m.project_id FROM messages m WHERE m.project_id IN (${ph}) AND m.role = 'agent'
         AND (m.body LIKE '%"type":"point_request"%' OR (m.body LIKE '%"type":"question"%' AND m.body NOT LIKE '%"answer":%'))
         AND m.id > COALESCE((SELECT MAX(id) FROM messages u WHERE u.project_id = m.project_id AND u.role = 'user'), 0)
       GROUP BY m.project_id`,
    ).bind(...ids).all<any>(),
    env.DB.prepare(`SELECT project_id FROM turns WHERE project_id IN (${ph}) AND status IN ('queued','running') GROUP BY project_id`).bind(...ids).all<any>(),
    env.DB.prepare(`SELECT project_id, COUNT(*) AS n FROM revisions WHERE project_id IN (${ph}) GROUP BY project_id`).bind(...ids).all<any>(),
  ])
  const by = <T extends { project_id: string }>(rows: T[]) => {
    const m = new Map<string, T[]>()
    for (const r of rows) m.set(r.project_id, [...(m.get(r.project_id) ?? []), r])
    return m
  }
  const scanMap = by(scans.results)
  const fileMap = by(files.results)
  const waiting = new Set(waits.results.map((r) => r.project_id))
  const working = new Set(turns.results.map((r) => r.project_id))
  const revCount = new Map(revs.results.map((r) => [r.project_id, r.n as number]))

  return Promise.all(
    projects.map(async (p) => {
      const ss = scanMap.get(p.id) ?? []
      const ff = fileMap.get(p.id) ?? []
      const latest = ss.at(-1)
      const busy = [...ss].reverse().find((s) => s.status !== 'ready' && s.status !== 'error')
      const deliverables = [...new Set(ff.filter((f) => f.kind === 'deliverable').map((f) => extOf(f.name)).filter(Boolean))].sort(
        (a, b) => rank(a) - rank(b) || a.localeCompare(b),
      )
      const cap = p.spend_cap_usd == null ? null : Number(p.spend_cap_usd)
      let state: string
      let progress: number | null = null
      if (busy?.status === 'importing') {
        state = 'uploading'
        progress = fraction(busy.progress) || null
      } else if (waiting.has(p.id)) state = 'reply'
      else if (busy) {
        const [a, b] = SPAN[busy.status] ?? [0, 1]
        state = 'processing'
        progress = a + (b - a) * fraction(busy.progress)
      } else if (working.has(p.id)) state = 'working'
      else if (latest?.status === 'error') state = 'unreadable'
      else if (deliverables.length) state = 'delivered'
      else if (!ss.length && !revCount.get(p.id)) state = 'empty'
      else if (cap != null && Number(p.spend_usd) >= cap) state = 'paused'
      else state = 'ready'
      const imgs = ff.filter((f) => f.kind === 'image' && /\/overview-|^overview-/.test(f.r2_key.split('/').pop() ?? ''))
      const base = imgs.length ? await assetBase(env, p.id) : ''
      const images = imgs
        .sort((a) => (/iso/.test(a.r2_key) ? -1 : 1))
        .map((f) => ({ id: f.id, view: /iso/.test(f.r2_key) ? 'iso_ne' : 'top', thumb: base + f.r2_key.replace(`projects/${p.id}/`, '') }))
      return { id: p.id, name: p.name, updated: p.last_active_at ?? p.updated_at ?? p.created_at, state, progress, deliverables, images }
    }),
  )
}

export async function projectScans(env: Env, pid: string) {
  const { results } = await env.DB.prepare('SELECT * FROM scans WHERE project_id = ? ORDER BY created_at').bind(pid).all()
  return parseRows<any>(results, SCAN_JSON)
}

export async function projectRevisions(env: Env, pid: string) {
  const { results } = await env.DB.prepare('SELECT * FROM revisions WHERE project_id = ? ORDER BY number').bind(pid).all()
  return parseRows<any>(results, REV_JSON)
}

export async function members(env: Env, pid: string) {
  const { results } = await env.DB.prepare(
    'SELECT m.user_id, u.email, u.name, m.role FROM project_members m JOIN users u ON u.id = m.user_id WHERE m.project_id = ? ORDER BY m.added_at',
  )
    .bind(pid)
    .all()
  return results
}

export async function currentTurn(env: Env, pid: string) {
  return env.DB.prepare("SELECT * FROM turns WHERE project_id = ? AND status IN ('queued','running') ORDER BY created_at DESC LIMIT 1").bind(pid).first()
}

/** The account's balance and whether it's low (`AccountSummary`). */
export async function accountSummary(env: Env, accountId: string) {
  const a = await env.DB.prepare('SELECT id, name, balance FROM accounts WHERE id = ?').bind(accountId).first<{ id: string; name: string; balance: number }>()
  if (!a) return null
  const s = await platformSettings(env)
  return { id: a.id, name: a.name, balance: Math.round(a.balance * 100) / 100, low: a.balance < s.low_balance, low_threshold: s.low_balance }
}

export async function platformSettings(env: Env) {
  const r = await env.DB.prepare("SELECT value FROM settings WHERE key = 'platform'").first<{ value: string }>()
  return JSON.parse(r?.value ?? '{}') as { starting_credits: number; markup: number; low_balance: number; prices: { models: Record<string, any>; units?: Record<string, number> } }
}

export async function billingSettings(env: Env) {
  const r = await env.DB.prepare("SELECT value FROM settings WHERE key = 'billing'").first<{ value: string }>()
  return JSON.parse(r?.value ?? '{}') as { usd_per_credit: number; currency: string; min_credits: number; round_to: number; max_credits?: number }
}

/** Add a ledger entry and move the balance, atomically. `ref` makes it idempotent (a Stripe session, a usage event). */
export async function postLedger(
  env: Env,
  accountId: string,
  kind: string,
  amount: number,
  extra: { project_id?: string | null; ref?: string | null; meta?: Record<string, unknown> | null } = {},
) {
  if (extra.ref) {
    const seen = await env.DB.prepare('SELECT id FROM ledger WHERE account_id = ? AND ref = ?').bind(accountId, extra.ref).first()
    if (seen) return null
  }
  const amt = Math.round(amount * 1e6) / 1e6
  const res = await env.DB.batch([
    env.DB.prepare('UPDATE accounts SET balance = ROUND(balance + ?, 6) WHERE id = ?').bind(amt, accountId),
    env.DB.prepare(
      'INSERT INTO ledger (account_id, kind, amount, balance_after, project_id, ref, meta, created_at) VALUES (?, ?, ?, (SELECT balance FROM accounts WHERE id = ?), ?, ?, ?, ?) RETURNING id, balance_after',
    ).bind(accountId, kind, amt, accountId, extra.project_id ?? null, extra.ref ?? null, extra.meta ? JSON.stringify(extra.meta) : null, now()),
  ])
  return (res[1].results?.[0] as { id: number; balance_after: number }) ?? null
}
