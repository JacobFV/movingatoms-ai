// Sign-in (the app's CONTRACTS §4 "Sign-in"): a 6-digit code by email, then a refresh session in an HttpOnly cookie
// and short-lived bearer access tokens. The homepage's portal API and the app share the same people and sessions.
import type { Env } from './env'
import { canEmail, codeEmail, sendEmail } from './email'
import { clientIp, cookie, EMAIL_RE, HttpError, now, randomToken, sha256, signToken, uuid, verifyToken } from './util'

export const COOKIE = 'ma_session'
const CODE_TTL = 10 * 60_000
const RESEND_AFTER = 30_000
const MAX_TRIES = 5
const SESSION_TTL = 60 * 86_400_000 // 60 days, sliding
const ACCESS_TTL = 15 * 60 // seconds

export interface User {
  id: string
  email: string
  name: string | null
  company: string | null
  role: string | null
  is_admin: number
  prefs: string
  created_at: string
}

export interface Claims {
  sub: string
  email: string
  name: string | null
  sid: string
  exp: number
}

const sixDigits = () => String(crypto.getRandomValues(new Uint32Array(1))[0] % 1_000_000).padStart(6, '0')

/** Email a code. Returns `dev_code` only when DEV_CODES=1 and no email provider is configured. */
export async function startCode(env: Env, req: Request, rawEmail: string) {
  const email = String(rawEmail ?? '').trim().toLowerCase()
  if (!EMAIL_RE.test(email) || email.length > 254) throw new HttpError(400, 'invalid_email', 'Enter a valid email address.')
  const prev = await env.DB.prepare('SELECT sent_at FROM auth_codes WHERE email = ?').bind(email).first<{ sent_at: number }>()
  const wait = prev ? prev.sent_at + RESEND_AFTER - Date.now() : 0
  if (wait > 0) {
    const s = Math.ceil(wait / 1000)
    throw new HttpError(429, 'too_many_requests', `Wait ${s} seconds before asking for another code.`, { retry_after: s })
  }
  const code = sixDigits()
  await env.DB.prepare(
    `INSERT INTO auth_codes (email, code_hash, expires_at, tries, sent_at, ip) VALUES (?, ?, ?, 0, ?, ?)
     ON CONFLICT(email) DO UPDATE SET code_hash = excluded.code_hash, expires_at = excluded.expires_at, tries = 0,
       sent_at = excluded.sent_at, ip = excluded.ip`,
  )
    .bind(email, await sha256(`${email}:${code}`), Date.now() + CODE_TTL, Date.now(), clientIp(req))
    .run()
  if (canEmail(env)) {
    if (!(await sendEmail(env, { to: email, ...codeEmail(code) })))
      throw new HttpError(502, 'email_failed', 'We couldn’t send the email. Try again in a minute.')
    return { email, expires_in: CODE_TTL / 1000, resend_in: RESEND_AFTER / 1000 }
  }
  if (env.DEV_CODES === '1') return { email, expires_in: CODE_TTL / 1000, resend_in: RESEND_AFTER / 1000, dev_code: code }
  throw new HttpError(503, 'email_failed', 'Sign-in email isn’t set up on this server yet.')
}

/** Check a code and sign in: creates the person (and their account) the first time. */
export async function verifyCode(env: Env, req: Request, rawEmail: string, rawCode: string, extra: { name?: string; company?: string; role?: string } = {}) {
  const email = String(rawEmail ?? '').trim().toLowerCase()
  const code = String(rawCode ?? '').replace(/\D/g, '')
  const row = await env.DB.prepare('SELECT * FROM auth_codes WHERE email = ?').bind(email).first<{ code_hash: string; expires_at: number; tries: number }>()
  if (!row) throw new HttpError(400, 'invalid_code', 'That code isn’t right. Ask for a new one.', { tries_left: 0 })
  if (row.expires_at < Date.now()) throw new HttpError(400, 'code_expired', 'That code has expired. Ask for a new one.')
  if (row.tries >= MAX_TRIES) throw new HttpError(429, 'too_many_tries', 'Too many tries. Ask for a new code.')
  if ((await sha256(`${email}:${code}`)) !== row.code_hash) {
    await env.DB.prepare('UPDATE auth_codes SET tries = tries + 1 WHERE email = ?').bind(email).run()
    const left = MAX_TRIES - row.tries - 1
    throw new HttpError(400, left > 0 ? 'invalid_code' : 'too_many_tries', left > 0 ? 'That code isn’t right.' : 'Too many tries. Ask for a new code.', { tries_left: left })
  }
  await env.DB.prepare('DELETE FROM auth_codes WHERE email = ?').bind(email).run()
  const { user, isNew } = await upsertUser(env, email, extra)
  const session = await createSession(env, req, user.id)
  return { user, isNew, ...session }
}

export async function upsertUser(env: Env, email: string, extra: { name?: string; company?: string; role?: string } = {}) {
  const admins = (env.ADMIN_EMAILS ?? '').toLowerCase().split(',').map((s) => s.trim()).filter(Boolean)
  const isAdmin = admins.includes(email) ? 1 : 0
  const name = extra.name?.trim().slice(0, 120) || null
  const company = extra.company?.trim().slice(0, 200) || null
  const role = extra.role?.trim().slice(0, 80) || null
  let user = await env.DB.prepare('SELECT * FROM users WHERE email = ?').bind(email).first<User>()
  const isNew = !user
  if (!user) {
    const id = uuid()
    const t = now()
    await env.DB.batch([
      env.DB.prepare('INSERT INTO users (id, email, name, company, role, is_admin, created_at, last_seen_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)').bind(id, email, name, company, role, isAdmin, t, t),
    ])
    await ensureAccount(env, id, name || email)
    user = (await env.DB.prepare('SELECT * FROM users WHERE id = ?').bind(id).first<User>())!
    // invitations made before they had an account were recorded against a placeholder user with this email: nothing to merge
  } else {
    await env.DB.prepare(
      'UPDATE users SET name = COALESCE(name, ?), company = COALESCE(?, company), role = COALESCE(?, role), is_admin = MAX(is_admin, ?), last_seen_at = ? WHERE id = ?',
    )
      .bind(name, company, role, isAdmin, now(), user.id)
      .run()
    user = (await env.DB.prepare('SELECT * FROM users WHERE id = ?').bind(user.id).first<User>())!
  }
  return { user, isNew }
}

/** The person's own account (one each); starting credits from the platform settings. */
export async function ensureAccount(env: Env, userId: string, name: string) {
  const have = await env.DB.prepare('SELECT account_id FROM account_members WHERE user_id = ? LIMIT 1').bind(userId).first<{ account_id: string }>()
  if (have) return have.account_id
  const id = uuid()
  const t = now()
  const s = await env.DB.prepare("SELECT value FROM settings WHERE key = 'platform'").first<{ value: string }>()
  const starting = Number(JSON.parse(s?.value ?? '{}').starting_credits ?? 0)
  const stmts = [
    env.DB.prepare('INSERT INTO accounts (id, name, owner_id, balance, created_at) VALUES (?, ?, ?, ?, ?)').bind(id, name, userId, starting, t),
    env.DB.prepare("INSERT INTO account_members (account_id, user_id, role) VALUES (?, ?, 'owner')").bind(id, userId),
  ]
  if (starting > 0)
    stmts.push(
      env.DB.prepare("INSERT INTO ledger (account_id, kind, amount, balance_after, meta, created_at) VALUES (?, 'grant', ?, ?, ?, ?)").bind(
        id,
        starting,
        starting,
        JSON.stringify({ note: 'Starting credits' }),
        t,
      ),
    )
  await env.DB.batch(stmts)
  return id
}

async function createSession(env: Env, req: Request, userId: string) {
  const id = uuid()
  const secret = randomToken(32)
  await env.DB.prepare('INSERT INTO sessions (id, user_id, secret_hash, created_at, expires_at, user_agent, ip) VALUES (?, ?, ?, ?, ?, ?, ?)')
    .bind(id, userId, await sha256(secret), now(), Date.now() + SESSION_TTL, (req.headers.get('User-Agent') ?? '').slice(0, 300), clientIp(req))
    .run()
  return { cookie: sessionCookie(`${id}.${secret}`, SESSION_TTL / 1000), sid: id }
}

export function sessionCookie(value: string, maxAge: number) {
  return `${COOKIE}=${encodeURIComponent(value)}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${Math.floor(maxAge)}`
}

/** The session behind the cookie (and its person), extended on use. */
export async function sessionFromCookie(env: Env, req: Request): Promise<{ user: User; sid: string } | null> {
  const raw = cookie(req, COOKIE)
  if (!raw) return null
  const [id, secret] = raw.split('.')
  if (!id || !secret) return null
  const s = await env.DB.prepare('SELECT * FROM sessions WHERE id = ?').bind(id).first<{ user_id: string; secret_hash: string; expires_at: number; revoked: number }>()
  if (!s || s.revoked || s.expires_at < Date.now() || s.secret_hash !== (await sha256(secret))) return null
  const user = await env.DB.prepare('SELECT * FROM users WHERE id = ?').bind(s.user_id).first<User>()
  if (!user) return null
  if (s.expires_at - Date.now() < SESSION_TTL / 2)
    await env.DB.prepare('UPDATE sessions SET expires_at = ? WHERE id = ?').bind(Date.now() + SESSION_TTL, id).run()
  return { user, sid: id }
}

export async function accessToken(env: Env, user: Pick<User, 'id' | 'email' | 'name'>, sid: string) {
  const exp = Math.floor(Date.now() / 1000) + ACCESS_TTL
  const token = await signToken(env.SESSION_SECRET, { sub: user.id, email: user.email, name: user.name, sid, exp, typ: 'access' })
  return { access_token: token, expires_at: exp }
}

export const publicUser = (u: Pick<User, 'id' | 'email' | 'name'>) => ({ id: u.id, email: u.email, name: u.name })

export async function claimsFrom(env: Env, token: string | null | undefined) {
  const c = await verifyToken<Claims & { typ?: string }>(env.SESSION_SECRET, token)
  return c && c.typ === 'access' ? c : null
}

/** The signed-in person for an API call: bearer token first (the app), then the cookie (the homepage portal). */
export async function currentUser(env: Env, req: Request): Promise<User | null> {
  const h = req.headers.get('Authorization')
  if (h?.startsWith('Bearer ')) {
    const c = await claimsFrom(env, h.slice(7))
    if (!c) return null
    const s = await env.DB.prepare('SELECT revoked FROM sessions WHERE id = ?').bind(c.sid).first<{ revoked: number }>()
    if (!s || s.revoked) return null
    return env.DB.prepare('SELECT * FROM users WHERE id = ?').bind(c.sub).first<User>()
  }
  return (await sessionFromCookie(env, req))?.user ?? null
}

export async function signOut(env: Env, req: Request) {
  const raw = cookie(req, COOKIE)
  const id = raw?.split('.')[0]
  if (id) await env.DB.prepare('UPDATE sessions SET revoked = 1 WHERE id = ?').bind(id).run()
  return sessionCookie('', 0)
}
