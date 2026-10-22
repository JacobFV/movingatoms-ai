// Sign-in: email + password (no reset or recovery, by the owner's choice), then a refresh session in an HttpOnly
// cookie and short-lived bearer access tokens. The emailed-code functions below stay for when email is set up.
// The homepage's portal API and the app share the same people and sessions.
import type { Env } from './env'
import { canEmail, codeEmail, sendEmail } from './email'
import { b64url, b64urlDecode, clientIp, cookie, EMAIL_RE, HttpError, now, randomToken, sha256, signToken, uuid, verifyToken } from './util'

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
  password_hash?: string | null
  failed_logins?: number
  locked_until?: number | null
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

// ---------- passwords ----------

const PBKDF2_ITERATIONS = 100_000 // the Workers runtime's maximum
const MAX_FAILS = 10
const LOCK_MS = 15 * 60_000

async function pbkdf2(password: string, salt: Uint8Array, iterations: number) {
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveBits'])
  return new Uint8Array(await crypto.subtle.deriveBits({ name: 'PBKDF2', hash: 'SHA-256', salt, iterations }, key, 256))
}

export async function hashPassword(password: string) {
  const salt = crypto.getRandomValues(new Uint8Array(16))
  return `pbkdf2$${PBKDF2_ITERATIONS}$${b64url(salt)}$${b64url(await pbkdf2(password, salt, PBKDF2_ITERATIONS))}`
}

async function checkPassword(password: string, stored: string) {
  const [alg, iter, salt, hash] = stored.split('$')
  if (alg !== 'pbkdf2' || !salt || !hash) return false
  const got = await pbkdf2(password, b64urlDecode(salt), Number(iter))
  const want = b64urlDecode(hash)
  if (got.length !== want.length) return false
  let diff = 0
  for (let i = 0; i < got.length; i++) diff |= got[i] ^ want[i]
  return diff === 0
}

function checkNewPassword(password: string) {
  if (password.length < 8) throw new HttpError(400, 'weak_password', 'Use at least 8 characters for your password.')
  if (password.length > 200) throw new HttpError(400, 'weak_password', 'That password is too long.')
}

/**
 * Sign in with a password. `mode`: 'login' needs an account, 'register' needs none, 'auto' (the homepage uploader)
 * signs in when the account has a password and creates it otherwise. An account made by an invitation has no
 * password yet: the first password set on it claims it.
 */
export async function passwordSignIn(
  env: Env,
  req: Request,
  raw: { email?: string; password?: string; name?: string; company?: string; role?: string; mode?: string },
) {
  const email = String(raw.email ?? '').trim().toLowerCase()
  const password = String(raw.password ?? '')
  const mode = raw.mode === 'login' || raw.mode === 'register' ? raw.mode : 'auto'
  if (!EMAIL_RE.test(email) || email.length > 254) throw new HttpError(400, 'invalid_email', 'Enter a valid email address.')
  if (!password) throw new HttpError(400, 'missing_password', 'Enter your password.')
  const existing = await env.DB.prepare('SELECT * FROM users WHERE email = ?').bind(email).first<User>()

  if (existing?.password_hash) {
    if (mode === 'register') throw new HttpError(409, 'account_exists', 'There’s already an account for this email. Sign in instead.')
    if (existing.locked_until && existing.locked_until > Date.now()) {
      const m = Math.ceil((existing.locked_until - Date.now()) / 60_000)
      throw new HttpError(429, 'too_many_tries', `Too many wrong passwords. Try again in ${m} minute${m === 1 ? '' : 's'}.`, { retry_after: m * 60 })
    }
    if (!(await checkPassword(password, existing.password_hash))) {
      const fails = (existing.failed_logins ?? 0) + 1
      await env.DB.prepare('UPDATE users SET failed_logins = ?, locked_until = ? WHERE id = ?')
        .bind(fails >= MAX_FAILS ? 0 : fails, fails >= MAX_FAILS ? Date.now() + LOCK_MS : null, existing.id)
        .run()
      throw new HttpError(401, 'wrong_password', 'That email and password don’t match.')
    }
    await env.DB.prepare('UPDATE users SET failed_logins = 0, locked_until = NULL WHERE id = ?').bind(existing.id).run()
    const { user } = await upsertUser(env, email, raw)
    return { user, isNew: false, ...(await createSession(env, req, user.id)) }
  }

  if (mode === 'login') throw new HttpError(404, 'no_account', 'There’s no account for this email yet. Create one.')
  checkNewPassword(password)
  const { user, isNew } = await upsertUser(env, email, raw)
  await env.DB.prepare('UPDATE users SET password_hash = ?, failed_logins = 0, locked_until = NULL WHERE id = ?').bind(await hashPassword(password), user.id).run()
  return { user, isNew: isNew || !existing?.password_hash, ...(await createSession(env, req, user.id)) }
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
