// Small helpers used everywhere: ids, time, JSON rows, hashing and signing.

export const now = () => new Date().toISOString()
export const uuid = () => crypto.randomUUID()

/** `{error, message?}` with a status — the shape every client here reads. */
export class HttpError extends Error {
  constructor(
    public status: number,
    public code: string,
    message?: string,
    public extra: Record<string, unknown> = {},
  ) {
    super(message ?? code)
  }
}

export function json(data: unknown, status = 200, headers: HeadersInit = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', ...headers },
  })
}

export function errorResponse(e: unknown) {
  if (e instanceof HttpError) return json({ error: e.code, message: e.message, ...e.extra }, e.status)
  console.error(e)
  return json({ error: 'server_error', message: 'Something went wrong on our side. Try again.' }, 500)
}

/** Parse the JSON columns of a row (names listed), leaving the rest as they are. */
export function parseRow<T>(row: Record<string, unknown> | null | undefined, cols: string[]): T | null {
  if (!row) return null
  const out: Record<string, unknown> = { ...row }
  for (const c of cols) {
    const v = out[c]
    if (typeof v === 'string') {
      try {
        out[c] = JSON.parse(v)
      } catch {
        /* leave it */
      }
    }
  }
  return out as T
}

export const parseRows = <T>(rows: Record<string, unknown>[], cols: string[]) => rows.map((r) => parseRow<T>(r, cols)!)

const enc = new TextEncoder()

export function b64url(bytes: ArrayBuffer | Uint8Array): string {
  const b = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes)
  let s = ''
  for (const x of b) s += String.fromCharCode(x)
  return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

export function b64urlDecode(s: string): Uint8Array {
  const pad = s.replace(/-/g, '+').replace(/_/g, '/') + '==='.slice((s.length + 3) % 4)
  const bin = atob(pad)
  const out = new Uint8Array(bin.length)
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i)
  return out
}

export function randomToken(bytes = 32) {
  return b64url(crypto.getRandomValues(new Uint8Array(bytes)))
}

export async function sha256(text: string) {
  return b64url(await crypto.subtle.digest('SHA-256', enc.encode(text)))
}

const keys = new Map<string, Promise<CryptoKey>>()
function hmacKey(secret: string) {
  let k = keys.get(secret)
  if (!k) {
    k = crypto.subtle.importKey('raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign', 'verify'])
    keys.set(secret, k)
  }
  return k
}

export async function hmac(secret: string, data: string) {
  return b64url(await crypto.subtle.sign('HMAC', await hmacKey(secret), enc.encode(data)))
}

/** Constant-time check of an HMAC signature. */
export async function hmacVerify(secret: string, data: string, sig: string) {
  try {
    return await crypto.subtle.verify('HMAC', await hmacKey(secret), b64urlDecode(sig), enc.encode(data))
  } catch {
    return false
  }
}

/** A compact signed token: base64url(JSON payload) + '.' + HMAC. `exp` is epoch seconds. */
export async function signToken(secret: string, payload: Record<string, unknown>) {
  const body = b64url(enc.encode(JSON.stringify(payload)))
  return `${body}.${await hmac(secret, body)}`
}

export async function verifyToken<T extends object>(secret: string, token: string | null | undefined): Promise<T | null> {
  if (!token) return null
  const i = token.lastIndexOf('.')
  if (i < 1) return null
  const body = token.slice(0, i)
  if (!(await hmacVerify(secret, body, token.slice(i + 1)))) return null
  try {
    const p = JSON.parse(new TextDecoder().decode(b64urlDecode(body))) as T & { exp?: number }
    if (p.exp !== undefined && p.exp * 1000 < Date.now()) return null
    return p as T
  } catch {
    return null
  }
}

export function cookie(req: Request, name: string): string | null {
  const h = req.headers.get('Cookie')
  if (!h) return null
  for (const part of h.split(';')) {
    const [k, ...v] = part.trim().split('=')
    if (k === name) return decodeURIComponent(v.join('='))
  }
  return null
}

export const clientIp = (req: Request) => req.headers.get('CF-Connecting-IP') ?? req.headers.get('X-Forwarded-For') ?? ''

export const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/

export const round2 = (n: number) => Math.round(n * 100) / 100
