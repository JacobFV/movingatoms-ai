# movingatoms.ai on Cloudflare

A rebuild of [movingatoms.ai](https://movingatoms.ai) (scan-to-BIM: upload a LiDAR scan, get a Revit/IFC model) on
Cloudflare: **Pages** for the site and API, **Durable Objects** for live project rooms and the agent, **D1** for data,
**R2** for scans and large media. Live at **https://movingatoms-ai.pages.dev**.

The original ran on an nginx VM with a Fastify + Supabase backend. This repo keeps the public site and the `/app`
client byte-for-byte (apart from three patches listed below) and replaces the whole backend. The API follows
the app's own contract: the request and response shapes its compiled client and mock backend expect.

## Layout

```
public/                 the static site (69 pages, assets, films) and the /app client bundle
functions/              Pages Functions
  _middleware.ts        security headers, /app SPA fallback, R2 fallback for big files, 404 page
  app/api/[[path]].ts   the app API (CONTRACTS §4): sign-in, projects, uploads, chat, viewer, billing, admin,
                        view-only links, and the processing worker's endpoints
  app/ws.ts             live socket → the project's Durable Object
  app/a/[[path]].ts     signed viewer asset links → R2 (Range requests, for Potree octrees and GLBs)
  app/f/[[path]].ts     one-hour file download links → R2
  portal/api/…          the homepage's sign-in, newsletter, site chat, legacy dashboard/quote
  upload/api/…          the homepage's legacy resumable uploader
  ma/api/send.ts        first-party, cookieless analytics (Umami-compatible) → D1
src/                    shared server code (auth, R2 multipart, projects, messages, estimate, email)
workers/realtime/       companion Worker that hosts the ProjectRoom Durable Object
  src/room.ts           WebSockets (hibernation), live event fan-out, turn lifecycle
  src/model.ts          the live BIM model: ops log in SQLite, if_version conflicts, per-author undo/redo
  src/agent.ts          the project agent ("Atom"): Claude (claude-opus-5-5) with model/viewer/question tools
migrations/             D1 schema
scripts/                media upload helpers for files too big for Pages
docs/INTERNAL.md        the Functions ⇄ Durable Object contract
```

## How the pieces fit

- **Sign-in:** an emailed 6-digit code. Successful sign-in creates a refresh session in an HttpOnly cookie (hashed
  in D1). The app then exchanges it for 15-minute HMAC bearer tokens (`GET /app/api/auth/session`).
- **Uploads:** resumable multipart, with up to 200 GB per file. By default each part streams through the Worker into
  R2 via the binding, so no R2 S3 keys are needed and the ETags are recorded in D1. If you set `R2_ACCESS_KEY_ID`
  and `R2_SECRET_ACCESS_KEY`, browsers PUT parts straight to R2 with presigned URLs instead. The bucket then needs a
  CORS rule that exposes `ETag`.
- **Live:** every project has one `ProjectRoom` Durable Object. Functions post events to it after each write, and it
  fans them out to the open sockets. It also owns the live model and runs agent turns.
- **Processing:** decoding scans, building Potree layers, fitting and model builds are GPU/CPU work that can't run
  on Workers. Uploads queue `jobs` rows in D1. A processing machine claims them through
  `/app/api/worker/*` (bearer `WORKER_TOKEN`), writes its outputs to R2 under `projects/<pid>/…`, and reports back:
  - `POST /worker/jobs/claim`
  - `PATCH /worker/jobs/:id`
  - `PATCH /worker/scans/:id`
  - `POST /worker/projects/:pid/files`
  - `POST /worker/projects/:pid/revisions` and `PATCH /worker/projects/:pid/revisions/:n`
  - `PUT /worker/projects/:pid/estimate`
  - `POST /worker/projects/:pid/messages`
  - `POST /worker/projects/:pid/events`

  When a scan is marked `ready`, the project becomes active, the estimate is priced, and (outside onboarding) the
  agent starts.
- **Estimate:** until a processing worker sends a measured one, it's priced from the scan's footprint and levels
  with a rate table in `src/estimate.ts`.
- **Billing:** credits ledger in D1 (1 credit = $1), with Stripe Checkout for top-ups when `STRIPE_SECRET_KEY` is
  set. Agent usage is metered per turn from token counts × the platform price table.

## Patches to the original client

1. The live socket URL gains `?project_id=` so the Function can route the upgrade to the right Durable Object
   (`public/app/assets/mount-*.js`).
2. The agent's model id maps to the "Atom-2" label (`public/app/assets/preload-helper-*.js`).
3. Analytics post to this site (`data-host-url="/ma"`), and the original zone's Cloudflare beacon is removed.

## Configuration

Vars live in `wrangler.toml` and `workers/realtime/wrangler.toml`. Secrets (`wrangler pages secret put …
--project-name movingatoms-ai`, and `wrangler secret put … -c workers/realtime/wrangler.toml` for the Worker):

| Secret | Where | Needed for |
|---|---|---|
| `SESSION_SECRET` | both (same value) | sign-in tokens, signed links — **set** |
| `WORKER_TOKEN` | Pages | the processing worker API and media uploads — **set** |
| `ANTHROPIC_API_KEY` | realtime Worker | the project agent; without it the agent says it isn't configured |
| `RESEND_API_KEY` | Pages (and Worker for invites) | emailing sign-in codes; then remove `DEV_CODES` |
| `STRIPE_SECRET_KEY` | Pages | credit top-ups |
| `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` | Pages | optional direct-to-R2 uploads |

> **`DEV_CODES = "1"` is on** because no email provider is configured yet. Sign-in codes are shown on screen, so
> anyone can sign in as any address. Turn it off as soon as `RESEND_API_KEY` is set.

## Deploy

```sh
npm install
npm run deploy:realtime        # the Durable Object Worker first (Pages binds to it by script name)
npm run db:migrate             # D1 schema
npm run deploy:pages           # site + Functions (uses --force: wrangler 4.15x otherwise redirects Pages to Workers)
```

Large public files (over Pages' 25 MiB limit) live in the `movingatoms-media` bucket and are served by the middleware
when the static lookup 404s: `node scripts/media-sync.mjs <dir>` (up to 300 MB each) and
`WORKER_TOKEN=… node scripts/media-upload-big.mjs <site> <dir> <key>…` (any size).

## Cloudflare resources

Account `20d4becc35c40a0bbfb8803a525aaae1`:
- Pages project `movingatoms-ai`
- Worker `movingatoms-realtime` (Durable Object `ProjectRoom`)
- D1 `movingatoms`
- R2 buckets `movingatoms-uploads` (private) and `movingatoms-media` (public site files)
