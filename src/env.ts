// Bindings and secrets shared by the Pages Functions and the realtime Worker (the Durable Objects).
// Names match wrangler.toml and workers/realtime/wrangler.toml.

export interface Env {
  // storage
  DB: D1Database
  UPLOADS: R2Bucket // private: customer scans, project files, deliverables
  MEDIA: R2Bucket // public: site files too big for Pages (sample Revit zips, scene assets)
  ASSETS: Fetcher // Pages static assets (Pages only)

  // Durable Objects (defined in workers/realtime)
  PROJECT_ROOM: DurableObjectNamespace

  // config (vars)
  SITE_URL: string // https://movingatoms.ai
  APP_NAME?: string
  ADMIN_EMAILS?: string // comma separated; these people get is_admin on sign-in
  DEV_CODES?: string // "1": sign-in codes are shown on screen instead of emailed (no email provider yet)
  EMAIL_FROM?: string // "Moving Atoms <hello@movingatoms.ai>"
  TEAM_EMAIL?: string // where chat messages and new submissions are announced
  AGENT_MODEL?: string // default claude-opus-5-5
  R2_ACCOUNT_ID?: string
  R2_UPLOADS_BUCKET?: string // the bucket name, for presigned part URLs

  // secrets
  SESSION_SECRET: string // signs access tokens, asset links and share links
  WORKER_TOKEN?: string // the processing worker's bearer token (/app/api/worker/*)
  ANTHROPIC_API_KEY?: string
  RESEND_API_KEY?: string
  STRIPE_SECRET_KEY?: string
  R2_ACCESS_KEY_ID?: string // optional: direct-to-R2 part uploads; without it parts go through the Worker
  R2_SECRET_ACCESS_KEY?: string

  // optional Cloudflare Email Service binding
  EMAIL?: SendEmail
}
