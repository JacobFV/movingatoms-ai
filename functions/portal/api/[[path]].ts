// The marketing site's API (/portal/api): sign-in for the homepage uploader and the dashboard, the newsletter,
// the chat widget, upload progress reports, and the older dashboard/quote pages' reads.
// Clients: public/home/app.js, public/chat/chat.js, public/dashboard/dashboard.js, public/quote/quote.js.
// Every answer is `{ok: true, ...}` or `{ok: false, error}` with a status, as those pages read it.
import { Hono } from 'hono'
import { handle } from 'hono/cloudflare-pages'
import type { Env } from '../../../src/env'
import { currentUser, signOut, startCode, verifyCode } from '../../../src/auth'
import { sendEmail } from '../../../src/email'
import { EMAIL_RE, HttpError, now, randomToken } from '../../../src/util'
import { submissionView, submissionsFor } from '../../../src/site/submissions'

const app = new Hono<{ Bindings: Env }>().basePath('/portal/api')

const ok = (data: Record<string, unknown> = {}, status = 200, headers: Record<string, string> = {}) =>
  new Response(JSON.stringify({ ok: true, ...data }), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', ...headers },
  })
const fail = (status: number, error: string, extra: Record<string, unknown> = {}) =>
  new Response(JSON.stringify({ ok: false, error, ...extra }), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' },
  })

app.onError((e) => {
  if (e instanceof HttpError) return fail(e.status, e.message, { code: e.code, ...e.extra })
  console.error(e)
  return fail(500, 'Something went wrong on our side. Try again.')
})

const body = async (req: Request) => ((await req.json().catch(() => ({}))) ?? {}) as Record<string, any>
const userOut = (u: { id: string; email: string; name: string | null; company: string | null }) => ({ id: u.id, email: u.email, name: u.name, company: u.company })

// ---------- account ----------

app.get('/me', async (c) => {
  const u = await currentUser(c.env, c.req.raw)
  return u ? ok({ user: userOut(u) }) : fail(401, 'Not signed in.', { user: null })
})

app.post('/auth/start', async (c) => {
  const b = await body(c.req.raw)
  const r = await startCode(c.env, c.req.raw, b.email)
  return ok(r.dev_code ? { devCode: r.dev_code, expires_in: r.expires_in } : { expires_in: r.expires_in })
})

app.post('/auth/verify', async (c) => {
  const b = await body(c.req.raw)
  const r = await verifyCode(c.env, c.req.raw, b.email, b.code, { name: b.name, company: b.company, role: b.role })
  return ok({ user: userOut(r.user), new_account: r.isNew }, 200, { 'Set-Cookie': r.cookie })
})

app.post('/auth/logout', async (c) => ok({}, 200, { 'Set-Cookie': await signOut(c.env, c.req.raw) }))

// ---------- newsletter ----------

app.post('/newsletter', async (c) => {
  const b = await body(c.req.raw)
  if (b.website) return ok() // the honeypot: pretend it worked
  const email = String(b.email ?? '').trim().toLowerCase()
  if (!EMAIL_RE.test(email) || email.length > 254) return fail(400, 'Enter a valid email address.')
  await c.env.DB.prepare('INSERT INTO newsletter (email, source, created_at) VALUES (?, ?, ?) ON CONFLICT(email) DO NOTHING')
    .bind(email, (c.req.header('Referer') ?? '').slice(0, 200), now())
    .run()
  return ok()
})

// ---------- the homepage uploader's progress reports (the team is told when an upload is in trouble) ----------

app.post('/upload-progress', async (c) => {
  const u = await currentUser(c.env, c.req.raw)
  if (!u) return fail(401, 'Not signed in.')
  const b = await body(c.req.raw)
  const id = String(b.submissionId ?? '')
  const report = {
    sent: Number(b.sent) || 0,
    total: Number(b.total) || 0,
    mode: b.mode === 'proxy' ? 'proxy' : 'direct',
    parts: Number(b.parts) || 0,
    error: b.error ? String(b.error).slice(0, 300) : null,
    at: Date.now(),
  }
  await c.env.DB.prepare('UPDATE submissions SET progress = ?, updated_at = ? WHERE id = ? AND user_id = ?').bind(JSON.stringify(report), now(), id, u.id).run()
  return ok()
})

// ---------- the older dashboard and quote pages ----------

app.get('/submissions', async (c) => {
  const u = await currentUser(c.env, c.req.raw)
  if (!u) return fail(401, 'Sign in to see your scans.')
  return ok({ user: userOut(u), submissions: await submissionsFor(c.env, u.id) })
})

// The legacy instant quote: pricing now happens in the app (/app), so a submission made through the old flow is
// reviewed by the team, who follow up by email. quote.js sends a "reviewing" upload to the dashboard.
app.get('/estimate/:id', async (c) => {
  const u = await currentUser(c.env, c.req.raw)
  if (!u) return fail(401, 'Sign in to see your estimate.')
  const v = await submissionView(c.env, c.req.param('id'), u.id)
  return v ? ok(v) : fail(404, 'We couldn’t find this upload.')
})
app.get('/estimate/:id/preview', () => new Response('No preview', { status: 404 }))
app.get('/estimate/:id/poster', () => new Response('No poster', { status: 404 }))
app.post('/estimate/:id/scope', async (c) => {
  const u = await currentUser(c.env, c.req.raw)
  if (!u) return fail(401, 'Sign in to change your estimate.')
  const b = await body(c.req.raw)
  const outputs = Array.isArray(b.scope?.outputs) ? b.scope.outputs.filter((x: unknown) => typeof x === 'string').slice(0, 8) : []
  const row = await c.env.DB.prepare('SELECT scope FROM submissions WHERE id = ? AND user_id = ?').bind(c.req.param('id'), u.id).first<{ scope: string | null }>()
  if (!row) return fail(404, 'We couldn’t find this upload.')
  const scope = { ...JSON.parse(row.scope ?? '{}'), outputs }
  await c.env.DB.prepare('UPDATE submissions SET scope = ?, updated_at = ? WHERE id = ?').bind(JSON.stringify(scope), now(), c.req.param('id')).run()
  return ok((await submissionView(c.env, c.req.param('id'), u.id)) ?? {})
})
// Payments for legacy quotes are not taken here (credits are bought in the app); these answer "not found" honestly.
app.post('/checkout/session', () => fail(404, 'No payment found for this session.'))
app.post('/checkout/:id', () => fail(404, 'Payments for this upload are handled by the team. We’ll email you.'))
app.post('/checkout/:id/confirm', () => fail(404, 'No payment found for this upload.'))
app.post('/dev/mockpay/:id', () => fail(404, 'Not available.'))

// ---------- the chat widget ----------

const TEAM_HELLO =
  'Thanks for the message! Ahmad and Shehryar read every chat and reply here, usually within minutes during the day (San Francisco time). Leave your email below and we’ll reply there too if you’ve gone.'

interface ChatRow {
  id: number
  role: string
  body: string
  created_at: string
}
const chatOut = (m: ChatRow) => ({
  id: m.id,
  sender: m.role === 'visitor' ? 'visitor' : 'team',
  author: m.role === 'bot' ? 'Moving Atoms' : m.role === 'team' ? 'Moving Atoms team' : undefined,
  body: m.body,
  created: Date.parse(m.created_at),
})

async function chatSince(env: Env, token: string, after: number) {
  const { results } = await env.DB.prepare('SELECT id, role, body, created_at FROM chat_messages WHERE token = ? AND id > ? ORDER BY id LIMIT 200')
    .bind(token, Math.floor(after) || 0)
    .all<ChatRow>()
  return results.map(chatOut)
}

app.get('/chat/poll', async (c) => {
  const token = c.req.query('token') ?? ''
  if (!token) return ok({ messages: [], team_online: false })
  const t = await c.env.DB.prepare('SELECT email FROM chat_threads WHERE token = ?').bind(token).first<{ email: string | null }>()
  if (!t) return ok({ messages: [], team_online: false })
  return ok({ messages: await chatSince(c.env, token, Number(c.req.query('after') ?? 0)), email: t.email, team_online: false })
})

app.post('/chat/send', async (c) => {
  const b = await body(c.req.raw)
  if (b.website) return ok({ messages: [] })
  const text = String(b.body ?? '').trim()
  if (!text) return fail(400, 'Write a message first.')
  if (text.length > 4000) return fail(400, 'That message is too long.')
  let token = typeof b.token === 'string' && /^[A-Za-z0-9_-]{16,64}$/.test(b.token) ? b.token : ''
  const t = now()
  let thread = token ? await c.env.DB.prepare('SELECT token, email FROM chat_threads WHERE token = ?').bind(token).first<{ token: string; email: string | null }>() : null
  const isNew = !thread
  if (!thread) {
    token = randomToken(24)
    await c.env.DB.prepare('INSERT INTO chat_threads (token, page, created_at, updated_at) VALUES (?, ?, ?, ?)').bind(token, String(b.page ?? '').slice(0, 300), t, t).run()
    thread = { token, email: null }
  }
  // a little flood control: at most 20 visitor messages a minute per thread
  const recent = await c.env.DB.prepare("SELECT COUNT(*) AS n FROM chat_messages WHERE token = ? AND role = 'visitor' AND created_at > ?")
    .bind(token, new Date(Date.now() - 60_000).toISOString())
    .first<{ n: number }>()
  if ((recent?.n ?? 0) >= 20) return fail(429, 'Slow down a little and try again in a minute.')
  const stmts = [
    c.env.DB.prepare("INSERT INTO chat_messages (token, role, body, created_at) VALUES (?, 'visitor', ?, ?)").bind(token, text, t),
    c.env.DB.prepare('UPDATE chat_threads SET updated_at = ?, page = COALESCE(?, page) WHERE token = ?').bind(t, b.page ? String(b.page).slice(0, 300) : null, token),
  ]
  if (isNew) stmts.push(c.env.DB.prepare("INSERT INTO chat_messages (token, role, body, created_at) VALUES (?, 'bot', ?, ?)").bind(token, TEAM_HELLO, t))
  await c.env.DB.batch(stmts)
  if (c.env.TEAM_EMAIL)
    c.executionCtx.waitUntil(
      sendEmail(c.env, {
        to: c.env.TEAM_EMAIL,
        subject: `Site chat${thread.email ? ` from ${thread.email}` : ''}: ${text.slice(0, 60)}`,
        text: `${text}\n\nPage: ${b.page ?? ''}\nThread: ${token}${thread.email ? `\nVisitor email: ${thread.email}` : ''}`,
        replyTo: thread.email ?? undefined,
      }).then(() => undefined),
    )
  return ok({ token, messages: await chatSince(c.env, token, Number(b.after ?? 0)) })
})

app.post('/chat/email', async (c) => {
  const b = await body(c.req.raw)
  const email = String(b.email ?? '').trim().toLowerCase()
  if (!EMAIL_RE.test(email)) return fail(400, 'Add a valid email.')
  const token = String(b.token ?? '')
  const r = await c.env.DB.prepare('UPDATE chat_threads SET email = ?, updated_at = ? WHERE token = ?').bind(email, now(), token).run()
  if (!r.meta.changes) return fail(404, 'Send a message first.')
  return ok()
})

app.all('*', () => fail(404, 'Not found.'))

export const onRequest = handle(app)
