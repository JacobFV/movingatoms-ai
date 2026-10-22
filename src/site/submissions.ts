// The older upload portal's submissions, in the shapes public/dashboard/dashboard.js and public/quote/quote.js read.
import type { Env } from '../env'

interface SubRow {
  id: string
  status: string
  notes: string | null
  scope: string | null
  created_at: string
  updated_at: string
}
interface FileRow {
  submission_id: string
  name: string
  size_bytes: number | null
  status: string
}

/** Our states → the dashboard's: a finished upload is with the team ("In review"); they follow up by email. */
const STATUS: Record<string, string> = { uploading: 'uploading', received: 'reviewing' }

function out(s: SubRow, files: FileRow[]) {
  const scope = s.scope ? JSON.parse(s.scope) : {}
  const created = Date.parse(s.created_at)
  const finished = s.status === 'received' ? Date.parse(s.updated_at) : null
  return {
    id: s.id,
    status: STATUS[s.status] ?? 'reviewing',
    created,
    finished,
    files: files.map((f) => ({ name: f.name, size: f.size_bytes ?? 0, ready: f.status === 'ready' })),
    notes: s.notes ?? '',
    lodRequested: scope.lod ?? null,
    history: finished ? [{ status: 'received', at: finished }] : [],
    quote: null,
    payment: null,
    message: null,
    deliveryUrl: null,
  }
}

export async function submissionsFor(env: Env, userId: string) {
  const { results: subs } = await env.DB.prepare('SELECT * FROM submissions WHERE user_id = ? ORDER BY created_at DESC LIMIT 100').bind(userId).all<SubRow>()
  if (!subs.length) return []
  const ids = subs.map((s) => s.id)
  const { results: files } = await env.DB.prepare(`SELECT submission_id, name, size_bytes, status FROM submission_files WHERE submission_id IN (${ids.map(() => '?').join(',')})`)
    .bind(...ids)
    .all<FileRow>()
  return subs.map((s) => out(s, files.filter((f) => f.submission_id === s.id)))
}

/** quote.js's view of one submission: `reviewing` sends it to the dashboard, where the team's follow-up shows. */
export async function submissionView(env: Env, id: string, userId: string) {
  const s = await env.DB.prepare('SELECT * FROM submissions WHERE id = ? AND user_id = ?').bind(id, userId).first<SubRow>()
  if (!s) return null
  const { results: files } = await env.DB.prepare('SELECT submission_id, name, size_bytes, status FROM submission_files WHERE submission_id = ?').bind(id).all<FileRow>()
  const v = out(s, files)
  return { ...v, stage: null, preview: false, poster: false, options: { outputs: ['revit', 'ifc'] }, scope: s.scope ? JSON.parse(s.scope) : {} }
}
