// Outgoing email: Resend when RESEND_API_KEY is set, else the Cloudflare Email Service binding (EMAIL), else nothing
// (sendEmail returns false and the caller decides: sign-in shows the code on screen only when DEV_CODES=1).
import type { Env } from './env'

export interface Mail {
  to: string
  subject: string
  text: string
  html?: string
  replyTo?: string
}

export async function sendEmail(env: Env, m: Mail): Promise<boolean> {
  const from = env.EMAIL_FROM || 'Moving Atoms <hello@movingatoms.ai>'
  if (env.RESEND_API_KEY) {
    const r = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { Authorization: `Bearer ${env.RESEND_API_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ from, to: [m.to], subject: m.subject, text: m.text, html: m.html, reply_to: m.replyTo }),
    })
    if (!r.ok) console.error('resend', r.status, await r.text().catch(() => ''))
    return r.ok
  }
  if (env.EMAIL) {
    try {
      await env.EMAIL.send({ from, to: m.to, subject: m.subject, text: m.text, html: m.html, replyTo: m.replyTo } as never)
      return true
    } catch (e) {
      console.error('email binding', e)
      return false
    }
  }
  return false
}

export const canEmail = (env: Env) => Boolean(env.RESEND_API_KEY || env.EMAIL)

const esc = (s: string) => s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]!)

export function codeEmail(code: string) {
  const text = `Your Moving Atoms sign-in code is ${code}.\n\nIt expires in 10 minutes. If you didn't ask for it, you can ignore this email.`
  const html = `<div style="font:15px/1.5 -apple-system,Segoe UI,sans-serif;color:#111;max-width:440px">
<p>Your Moving Atoms sign-in code:</p>
<p style="font:600 30px/1.2 ui-monospace,Menlo,monospace;letter-spacing:6px;margin:18px 0">${esc(code)}</p>
<p style="color:#555">It expires in 10 minutes. If you didn't ask for it, you can ignore this email.</p></div>`
  return { subject: `${code} is your Moving Atoms code`, text, html }
}
