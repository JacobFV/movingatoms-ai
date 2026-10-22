-- Email + password sign-in (no reset or recovery). PBKDF2-SHA256: "pbkdf2$<iterations>$<salt b64url>$<hash b64url>".
ALTER TABLE users ADD COLUMN password_hash TEXT;
ALTER TABLE users ADD COLUMN failed_logins INTEGER NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN locked_until INTEGER;   -- epoch ms
