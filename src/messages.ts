// The project chat (§8): rows in D1, every change announced on the project's live socket.
import type { Env } from './env'
import { emit } from './projects'
import { now, parseRow } from './util'

export interface MessageBody {
  text?: string
  blocks?: any[]
  [k: string]: unknown
}

export interface Message {
  id: number
  project_id: string
  turn_id: string | null
  role: 'user' | 'agent' | 'system'
  author_id: string | null
  author?: { id: string; email: string; name: string | null } | null
  body: MessageBody
  created_at: string
  updated_at: string
}

const SELECT = `SELECT m.*, u.email AS a_email, u.name AS a_name FROM messages m LEFT JOIN users u ON u.id = m.author_id`

export function messageOut(r: Record<string, any>): Message {
  const m = parseRow<any>(r, ['body'])!
  const author = m.author_id && m.a_email ? { id: m.author_id, email: m.a_email, name: m.a_name ?? null } : null
  delete m.a_email
  delete m.a_name
  return { ...m, author }
}

export async function addMessage(
  env: Env,
  pid: string,
  m: { role: Message['role']; body: MessageBody; turn_id?: string | null; author_id?: string | null },
  opts: { silent?: boolean } = {},
): Promise<Message> {
  const t = now()
  const r = await env.DB.prepare(
    'INSERT INTO messages (project_id, turn_id, role, author_id, body, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING id',
  )
    .bind(pid, m.turn_id ?? null, m.role, m.author_id ?? null, JSON.stringify(m.body), t, t)
    .first<{ id: number }>()
  const msg = (await getMessage(env, pid, r!.id))!
  if (!opts.silent) await emit(env, pid, { type: 'message.created', message: msg })
  return msg
}

export async function getMessage(env: Env, pid: string, id: number) {
  const r = await env.DB.prepare(`${SELECT} WHERE m.project_id = ? AND m.id = ?`).bind(pid, id).first()
  return r ? messageOut(r) : null
}

export async function setBody(env: Env, pid: string, id: number, body: MessageBody, extra: { turn_id?: string | null } = {}) {
  const sets = ['body = ?', 'updated_at = ?']
  const vals: unknown[] = [JSON.stringify(body), now()]
  if (extra.turn_id !== undefined) {
    sets.push('turn_id = ?')
    vals.push(extra.turn_id)
  }
  await env.DB.prepare(`UPDATE messages SET ${sets.join(', ')} WHERE project_id = ? AND id = ?`).bind(...vals, pid, id).run()
  await emit(env, pid, { type: 'message.updated', id, body })
}

export async function listMessages(env: Env, pid: string, opts: { before?: number; limit?: number }) {
  const limit = Math.min(200, Math.max(1, opts.limit ?? 50))
  const { results } = await env.DB.prepare(`${SELECT} WHERE m.project_id = ? AND m.id < ? ORDER BY m.id DESC LIMIT ?`)
    .bind(pid, opts.before ?? Number.MAX_SAFE_INTEGER, limit)
    .all()
  return results.map(messageOut).reverse()
}
