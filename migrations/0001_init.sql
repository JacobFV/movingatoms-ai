-- Moving Atoms on Cloudflare: D1 schema.
-- Shapes follow the app's contract (web/src/lib/types.ts). JSON columns are TEXT holding JSON.
-- Times are ISO-8601 strings (UTC). Money is credits (1 credit = $1).

-- ---------- people and sign-in ----------

CREATE TABLE users (
  id          TEXT PRIMARY KEY,
  email       TEXT NOT NULL UNIQUE COLLATE NOCASE,
  name        TEXT,
  company     TEXT,
  role        TEXT,
  is_admin    INTEGER NOT NULL DEFAULT 0,
  prefs       TEXT NOT NULL DEFAULT '{}',
  created_at  TEXT NOT NULL,
  last_seen_at TEXT
);

-- one-time email codes (6 digits, stored hashed)
CREATE TABLE auth_codes (
  email       TEXT PRIMARY KEY COLLATE NOCASE,
  code_hash   TEXT NOT NULL,
  expires_at  INTEGER NOT NULL,   -- epoch ms
  tries       INTEGER NOT NULL DEFAULT 0,
  sent_at     INTEGER NOT NULL,
  ip          TEXT
);

-- refresh sessions: the HttpOnly cookie holds `<id>.<secret>`; only the secret's hash is kept
CREATE TABLE sessions (
  id          TEXT PRIMARY KEY,
  user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  secret_hash TEXT NOT NULL,
  created_at  TEXT NOT NULL,
  expires_at  INTEGER NOT NULL,   -- epoch ms
  revoked     INTEGER NOT NULL DEFAULT 0,
  user_agent  TEXT,
  ip          TEXT
);
CREATE INDEX sessions_user ON sessions(user_id);

-- ---------- accounts and credits (§14) ----------

CREATE TABLE accounts (
  id          TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  owner_id    TEXT REFERENCES users(id),
  balance     REAL NOT NULL DEFAULT 0,
  created_at  TEXT NOT NULL
);

CREATE TABLE account_members (
  account_id  TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role        TEXT NOT NULL DEFAULT 'owner',
  PRIMARY KEY (account_id, user_id)
);
CREATE INDEX account_members_user ON account_members(user_id);

CREATE TABLE ledger (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  account_id    TEXT NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  kind          TEXT NOT NULL,     -- grant | usage | topup | adjustment | refund
  amount        REAL NOT NULL,
  balance_after REAL NOT NULL,
  project_id    TEXT,
  ref           TEXT,
  meta          TEXT,              -- JSON
  created_at    TEXT NOT NULL
);
CREATE INDEX ledger_account ON ledger(account_id, id DESC);
CREATE UNIQUE INDEX ledger_ref ON ledger(account_id, ref) WHERE ref IS NOT NULL;

CREATE TABLE settings (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL               -- JSON
);

-- ---------- projects ----------

CREATE TABLE projects (
  id              TEXT PRIMARY KEY,
  account_id      TEXT NOT NULL REFERENCES accounts(id),
  name            TEXT NOT NULL,
  status          TEXT NOT NULL DEFAULT 'setup',   -- setup | processing | active | archived
  model           TEXT NOT NULL,
  spend_cap_usd   REAL,
  spend_usd       REAL NOT NULL DEFAULT 0,
  container_state TEXT NOT NULL DEFAULT 'none',
  settings        TEXT NOT NULL DEFAULT '{}',      -- JSON: scope, onboarding, started, live_heatmap
  share_token     TEXT UNIQUE,
  share_created_at TEXT,
  share_created_by TEXT,
  created_by      TEXT REFERENCES users(id),
  created_at      TEXT NOT NULL,
  updated_at      TEXT NOT NULL,
  last_active_at  TEXT NOT NULL
);
CREATE INDEX projects_account ON projects(account_id);

CREATE TABLE project_members (
  project_id  TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role        TEXT NOT NULL,                       -- owner | editor | viewer
  added_at    TEXT NOT NULL,
  PRIMARY KEY (project_id, user_id)
);
CREATE INDEX project_members_user ON project_members(user_id);

CREATE TABLE files (
  id            TEXT PRIMARY KEY,
  project_id    TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  kind          TEXT NOT NULL,     -- source | upload | deliverable | image | attachment | asset
  name          TEXT NOT NULL,
  r2_key        TEXT NOT NULL,
  size_bytes    INTEGER,
  content_type  TEXT,
  status        TEXT NOT NULL,     -- uploading | ready | failed | deleted
  meta          TEXT,              -- JSON
  created_by    TEXT,
  created_at    TEXT NOT NULL
);
CREATE INDEX files_project ON files(project_id, created_at DESC);

-- multipart uploads in flight (the app's resumable uploader)
CREATE TABLE uploads (
  upload_id   TEXT PRIMARY KEY,
  project_id  TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  file_id     TEXT NOT NULL,
  r2_key      TEXT NOT NULL,
  name        TEXT NOT NULL,
  size_bytes  INTEGER,
  content_type TEXT,
  created_by  TEXT,
  created_at  TEXT NOT NULL
);

-- parts received for an upload (the R2 binding has no ListParts; S3 ListParts is used for presigned uploads)
CREATE TABLE upload_parts (
  upload_id   TEXT NOT NULL,
  part_number INTEGER NOT NULL,
  etag        TEXT NOT NULL,
  size        INTEGER NOT NULL,
  PRIMARY KEY (upload_id, part_number)
);

CREATE TABLE scans (
  id            TEXT PRIMARY KEY,
  project_id    TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  file_id       TEXT,
  name          TEXT NOT NULL,
  status        TEXT NOT NULL,     -- queued | importing | inspecting | decoding | labelling | converting | overview | ready | error
  stage_detail  TEXT,
  progress      REAL NOT NULL DEFAULT 0,
  point_count   INTEGER,
  bounds        TEXT,              -- JSON
  frame         TEXT,              -- JSON
  copc_key      TEXT,
  potree_prefix TEXT,
  labels        TEXT,              -- JSON
  overview      TEXT,              -- JSON
  brief         TEXT,              -- JSON
  viewer        TEXT,              -- JSON {overview, full}
  error         TEXT,
  created_at    TEXT NOT NULL,
  updated_at    TEXT NOT NULL
);
CREATE INDEX scans_project ON scans(project_id, created_at);

CREATE TABLE revisions (
  id          TEXT PRIMARY KEY,
  project_id  TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  number      INTEGER NOT NULL,
  title       TEXT,
  notes       TEXT,
  status      TEXT NOT NULL DEFAULT 'ready',
  model_seq   INTEGER,
  graph_key   TEXT,
  glb_key     TEXT,
  view_key    TEXT,
  ifc_key     TEXT,
  heatmap     TEXT NOT NULL DEFAULT '{}',   -- JSON
  heatmaps    TEXT NOT NULL DEFAULT '{}',   -- JSON, per scan
  renders     TEXT NOT NULL DEFAULT '[]',   -- JSON
  created_by  TEXT,
  created_at  TEXT NOT NULL,
  UNIQUE (project_id, number)
);

-- background work: scan ingest, link imports, fits, estimates. A processing worker (GPU box) claims rows.
CREATE TABLE jobs (
  id          TEXT PRIMARY KEY,
  project_id  TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  type        TEXT NOT NULL,     -- ingest | link_import | model_fit | estimate | build
  status      TEXT NOT NULL,     -- queued | running | done | error
  stage       TEXT,
  progress    REAL NOT NULL DEFAULT 0,
  input       TEXT,              -- JSON
  result      TEXT,              -- JSON
  error       TEXT,
  claimed_by  TEXT,
  claimed_at  INTEGER,
  created_at  TEXT NOT NULL,
  updated_at  TEXT NOT NULL
);
CREATE INDEX jobs_queue ON jobs(status, created_at);
CREATE INDEX jobs_project ON jobs(project_id, created_at DESC);

CREATE TABLE messages (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id  TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  turn_id     TEXT,
  role        TEXT NOT NULL,     -- user | agent | system
  author_id   TEXT,
  body        TEXT NOT NULL,     -- JSON MessageBody
  created_at  TEXT NOT NULL,
  updated_at  TEXT NOT NULL
);
CREATE INDEX messages_project ON messages(project_id, id);

CREATE TABLE turns (
  id          TEXT PRIMARY KEY,
  project_id  TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  status      TEXT NOT NULL,     -- queued | running | done | error | stopped
  kind        TEXT NOT NULL,     -- user | kickoff | system
  started_at  TEXT,
  ended_at    TEXT,
  error       TEXT,
  created_at  TEXT NOT NULL
);
CREATE INDEX turns_project ON turns(project_id, created_at DESC);

CREATE TABLE points (
  id                    TEXT PRIMARY KEY,
  project_id            TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  author_id             TEXT,
  revision_number       INTEGER,
  side                  TEXT NOT NULL,
  world                 TEXT NOT NULL,   -- JSON Vec3
  element_id            TEXT,
  camera                TEXT,            -- JSON
  note                  TEXT,
  request_id            TEXT,
  status                TEXT NOT NULL DEFAULT 'open',
  response              TEXT,
  addressed_in_revision INTEGER,
  created_at            TEXT NOT NULL
);
CREATE INDEX points_project ON points(project_id, created_at DESC);

CREATE TABLE views (
  id          TEXT PRIMARY KEY,
  project_id  TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  name        TEXT NOT NULL,
  state       TEXT NOT NULL,     -- JSON ViewState
  created_by  TEXT,
  author      TEXT,
  created_at  TEXT NOT NULL,
  updated_at  TEXT NOT NULL
);
CREATE INDEX views_project ON views(project_id);

CREATE TABLE estimates (
  project_id  TEXT PRIMARY KEY REFERENCES projects(id) ON DELETE CASCADE,
  data        TEXT NOT NULL,     -- JSON Estimate
  updated_at  TEXT NOT NULL
);

CREATE TABLE checkouts (
  session_id  TEXT PRIMARY KEY,  -- Stripe Checkout session id
  account_id  TEXT NOT NULL REFERENCES accounts(id),
  project_id  TEXT,
  credits     REAL NOT NULL,
  amount_usd  REAL NOT NULL,
  status      TEXT NOT NULL,     -- open | paid | expired | failed
  created_by  TEXT,
  created_at  TEXT NOT NULL,
  applied_at  TEXT
);

-- ---------- the marketing site (/portal, /upload, /ma) ----------

-- the legacy portal's submissions (the homepage's ?app=0 flow and /upload)
CREATE TABLE submissions (
  id          TEXT PRIMARY KEY,
  user_id     TEXT REFERENCES users(id),
  email       TEXT,
  name        TEXT,
  company     TEXT,
  notes       TEXT,
  scope       TEXT,              -- JSON
  status      TEXT NOT NULL DEFAULT 'uploading',   -- uploading | received
  progress    TEXT,              -- JSON, last browser report
  created_at  TEXT NOT NULL,
  updated_at  TEXT NOT NULL
);

CREATE TABLE submission_files (
  submission_id TEXT NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
  r2_key        TEXT NOT NULL,
  upload_id     TEXT,
  name          TEXT NOT NULL,
  size_bytes    INTEGER,
  content_type  TEXT,
  status        TEXT NOT NULL,   -- uploading | ready
  created_at    TEXT NOT NULL,
  PRIMARY KEY (submission_id, r2_key)
);

CREATE TABLE newsletter (
  email       TEXT PRIMARY KEY COLLATE NOCASE,
  source      TEXT,
  created_at  TEXT NOT NULL
);

-- the site chat widget: one thread per browser token
CREATE TABLE chat_threads (
  token       TEXT PRIMARY KEY,
  email       TEXT,
  page        TEXT,
  created_at  TEXT NOT NULL,
  updated_at  TEXT NOT NULL
);
CREATE TABLE chat_messages (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  token       TEXT NOT NULL REFERENCES chat_threads(token) ON DELETE CASCADE,
  role        TEXT NOT NULL,     -- visitor | team | bot
  body        TEXT NOT NULL,
  created_at  TEXT NOT NULL
);
CREATE INDEX chat_messages_token ON chat_messages(token, id);

-- first-party analytics (the Umami-compatible collector at /ma/api/send)
CREATE TABLE events (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  ts          TEXT NOT NULL,
  type        TEXT NOT NULL,     -- pageview | event
  name        TEXT,
  url         TEXT,
  referrer    TEXT,
  title       TEXT,
  screen      TEXT,
  language    TEXT,
  country     TEXT,
  visitor     TEXT,              -- daily-rotating hash, no cookies
  data        TEXT               -- JSON
);
CREATE INDEX events_ts ON events(ts);

INSERT INTO settings (key, value) VALUES
  ('platform', '{"starting_credits":10,"markup":1,"low_balance":50,"prices":{"models":{"claude-opus-5-5":{"input":4,"cached_input":0.2,"cache_write":5,"output":20}},"units":{"farm_minute":0,"gpu_render_minute":0,"ingest_gb":0}}}'),
  ('billing',  '{"usd_per_credit":1,"currency":"usd","min_credits":100,"round_to":100,"max_credits":100000}');
