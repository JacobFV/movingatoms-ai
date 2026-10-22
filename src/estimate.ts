// The project's estimate (§4 estimate, §19). The original priced jobs with a separate estimator service (B2) that
// measured the scan; here the Worker prices from what ingest recorded about the scan (footprint, levels, density)
// with a transparent rate table. A processing worker can replace it with a measured one (PUT /worker/.../estimate).
import type { Env } from './env'
import { emit } from './projects'
import { now } from './util'

export const DEFAULT_SCOPE = {
  formats: ['rvt'],
  lod: 350,
  model: ['architecture', 'structure', 'ducts', 'pipes', 'cable_trays', 'equipment'],
  model_other: '',
  exclude: ['loose_furniture', 'clutter', 'vegetation', 'not_visible'],
  exclude_other: '',
  area: 'whole',
  area_box: null as null | { min: number[]; max: number[] },
  levels: [] as number[],
  purpose: 'as_built',
  notes: '',
  attachments: [] as string[],
}
export type Scope = typeof DEFAULT_SCOPE

const LODS = [200, 300, 350, 400]
const FORMATS = ['rvt', 'ifc', 'usd', 'glb']
const PARTS = ['architecture', 'structure', 'ducts', 'pipes', 'cable_trays', 'equipment', 'furniture', 'site']
const LEAVE = ['loose_furniture', 'clutter', 'vegetation', 'not_visible', 'above_ceiling', 'small_pipes']
const PURPOSES = ['as_built', 'design', 'facilities', 'coordination', 'simulation']

/** A scope with every field valid (B2's normScope). */
export function normScope(raw: any): Scope {
  const r = raw && typeof raw === 'object' ? raw : {}
  const pick = (list: string[], v: unknown, d: string[]) => (Array.isArray(v) ? list.filter((x) => v.includes(x)) : d)
  let lod = Number(r.lod)
  if (lod === 500) lod = 400
  const box = r.area_box && Array.isArray(r.area_box.min) && Array.isArray(r.area_box.max) ? { min: r.area_box.min.map(Number), max: r.area_box.max.map(Number) } : null
  let area = ['whole', 'box', 'levels'].includes(r.area) ? r.area : box ? 'box' : 'whole'
  if (area === 'box' && !box) area = 'whole'
  let formats = pick(FORMATS, r.formats, DEFAULT_SCOPE.formats)
  if (!formats.length) formats = ['rvt']
  return {
    formats,
    lod: LODS.includes(lod) ? lod : 350,
    model: pick(PARTS, r.model, DEFAULT_SCOPE.model),
    model_other: typeof r.model_other === 'string' ? r.model_other.slice(0, 500) : '',
    exclude: pick(LEAVE, r.exclude, DEFAULT_SCOPE.exclude),
    exclude_other: typeof r.exclude_other === 'string' ? r.exclude_other.slice(0, 500) : '',
    area,
    area_box: area === 'box' ? box : null,
    levels: Array.isArray(r.levels) ? r.levels.map(Number).filter(Number.isFinite).slice(0, 50) : [],
    purpose: PURPOSES.includes(r.purpose) ? r.purpose : 'as_built',
    notes: typeof r.notes === 'string' ? r.notes.slice(0, 4000) : '',
    attachments: Array.isArray(r.attachments) ? r.attachments.filter((x: unknown) => typeof x === 'string').slice(0, 50) : [],
  }
}

// credits per m² of floor by LOD, and what each part adds (relative); the platform's rate card
const PER_M2: Record<number, number> = { 200: 0.06, 300: 0.1, 350: 0.13, 400: 0.2 }
const PART_WEIGHT: Record<string, number> = {
  architecture: 0.35,
  structure: 0.2,
  ducts: 0.12,
  pipes: 0.18,
  cable_trays: 0.06,
  equipment: 0.09,
  furniture: 0.08,
  site: 0.06,
}
const MIN_CREDITS = 100
const TOPUP_MULTIPLIER = 3

export interface Estimate {
  status: 'pending' | 'measuring' | 'ready' | 'held' | 'failed'
  stage: string | null
  progress?: number | null
  credits_expected?: number | null
  credits_low: number | null
  credits_high: number | null
  suggested_credits: number | null
  hours_expected?: number | null
  hours_low: number | null
  hours_high: number | null
  area_m2: number | null
  levels: number | null
  level_options?: { z: number; area_m2?: number | null }[] | null
  topup_options?: { kind: 'minimum' | 'estimate' | 'more'; credits: number }[] | null
  building_class: string | null
  summary: string[] | null
  scope: Partial<Scope> | null
  reasons: string[] | null
  version: number
  updated_at: string | null
  /** set by a measured estimate (a processing worker): the Worker's heuristic never overwrites it */
  measured?: boolean
}

const blank = (version = 0): Estimate => ({
  status: 'pending',
  stage: 'Waiting for the scan',
  progress: null,
  credits_low: null,
  credits_high: null,
  suggested_credits: null,
  hours_low: null,
  hours_high: null,
  area_m2: null,
  levels: null,
  building_class: null,
  summary: null,
  scope: null,
  reasons: null,
  version,
  updated_at: null,
})

export async function readEstimate(env: Env, pid: string): Promise<Estimate> {
  const r = await env.DB.prepare('SELECT data FROM estimates WHERE project_id = ?').bind(pid).first<{ data: string }>()
  return r ? (JSON.parse(r.data) as Estimate) : blank()
}

export async function writeEstimate(env: Env, pid: string, e: Estimate) {
  e.updated_at = now()
  await env.DB.prepare('INSERT INTO estimates (project_id, data, updated_at) VALUES (?, ?, ?) ON CONFLICT(project_id) DO UPDATE SET data = excluded.data, updated_at = excluded.updated_at')
    .bind(pid, JSON.stringify(e), e.updated_at)
    .run()
  await emit(env, pid, { type: 'estimate.updated', estimate: e })
  return e
}

const round10 = (n: number) => Math.max(10, Math.round(n / 10) * 10)
const up100 = (n: number) => Math.max(MIN_CREDITS, Math.ceil(n / 100) * 100)

/** Price the project's scope from its ready scans. Pending until a scan reports its footprint. */
export async function estimate(env: Env, pid: string, rawScope: unknown): Promise<Estimate> {
  const prev = await readEstimate(env, pid)
  const scope = normScope(rawScope)
  if (prev.measured && prev.status === 'ready' && JSON.stringify(prev.scope) === JSON.stringify(scope)) return prev
  const { results } = await env.DB.prepare("SELECT status, bounds, brief, point_count FROM scans WHERE project_id = ? AND status != 'error'").bind(pid).all<any>()
  if (!results.length) return writeEstimate(env, pid, { ...blank(prev.version + 1), scope })
  // measured: ingest has recorded the scan's extent (the brief starts with only the file's name and size)
  const ready = results.filter((s) => s.bounds || (s.brief && (JSON.parse(s.brief).bounds || JSON.parse(s.brief).footprint_m2)))
  if (!ready.length) return writeEstimate(env, pid, { ...blank(prev.version + 1), status: 'measuring', stage: 'Measuring the scan', scope })

  let footprint = 0
  let levels = 0
  const levelZ: number[] = []
  for (const s of ready) {
    const brief = s.brief ? JSON.parse(s.brief) : {}
    const b = s.bounds ? JSON.parse(s.bounds) : brief.bounds
    const fp = Number(brief.footprint_m2) || (b ? Math.abs((b.max[0] - b.min[0]) * (b.max[1] - b.min[1])) * 0.7 : 0)
    footprint += fp
    const lv = Array.isArray(brief.levels_guess) ? brief.levels_guess.filter((l: any) => l.kind !== 'ceiling') : []
    for (const l of lv) levelZ.push(Number(l.z))
    levels = Math.max(levels, lv.length || (b ? Math.max(1, Math.round((b.max[2] - b.min[2]) / 3.5)) : 1))
  }
  let area = footprint * Math.max(1, levels)
  if (scope.area === 'box' && scope.area_box) {
    const bx = scope.area_box
    area = Math.min(area, Math.abs((bx.max[0] - bx.min[0]) * (bx.max[1] - bx.min[1])) * Math.max(1, Math.round(Math.abs(bx.max[2] - bx.min[2]) / 3.5)))
  } else if (scope.area === 'levels' && scope.levels.length) area = footprint * scope.levels.length

  const weight = scope.model.reduce((a, p) => a + (PART_WEIGHT[p] ?? 0), 0) || 0.3
  const formats = 1 + 0.05 * Math.max(0, scope.formats.length - 1)
  const central = Math.max(MIN_CREDITS / 2, area * PER_M2[scope.lod] * weight * formats)
  const expected = round10(central)
  const hours = Math.max(1, Math.round((area / 400) * (scope.lod / 300) * 10) / 10)
  const suggested = up100(expected * TOPUP_MULTIPLIER)
  const e: Estimate = {
    status: area > 0 ? 'ready' : 'held',
    stage: null,
    progress: null,
    credits_expected: expected,
    credits_low: round10(expected * 0.75),
    credits_high: round10(expected * 1.4),
    suggested_credits: suggested,
    hours_expected: hours,
    hours_low: Math.max(0.5, Math.round(hours * 0.7 * 10) / 10),
    hours_high: Math.round(hours * 1.5 * 10) / 10,
    area_m2: Math.round(area),
    levels: scope.area === 'levels' && scope.levels.length ? scope.levels.length : levels,
    level_options: [...new Set(levelZ.map((z) => Math.round(z * 100) / 100))].sort((a, b) => a - b).map((z) => ({ z, area_m2: Math.round(footprint) })),
    topup_options: [...new Map([
      ['minimum', MIN_CREDITS],
      ['estimate', up100(expected)],
      ['more', up100(expected * 1.5)],
    ] as const).entries()]
      .map(([kind, credits]) => ({ kind, credits }))
      .filter((o, i, a) => a.findIndex((x) => x.credits === o.credits) === i),
    building_class: null,
    summary: [
      `About ${Math.round(area).toLocaleString('en-US')} m² of floor over ${levels} level${levels === 1 ? '' : 's'}`,
      `LOD ${scope.lod}: ${scope.model.length} part${scope.model.length === 1 ? '' : 's'} of the building`,
    ],
    scope,
    reasons: area > 0 ? null : ['We couldn’t measure the floor area from this scan yet. The team will price it by hand.'],
    version: prev.version + 1,
    updated_at: null,
  }
  return writeEstimate(env, pid, e)
}
