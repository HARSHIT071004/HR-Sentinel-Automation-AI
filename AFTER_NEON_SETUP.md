# After Neon Setup – Next Steps to Get Login Working

Your `DATABASE_URL` env var is set on Vercel. Now do these steps:

---

## 1. Verify the URL format is correct

In Vercel Dashboard → Environment Variables, make sure `DATABASE_URL` is:

```
postgresql+asyncpg://user:pass@ep-xxx.neon.tech/neondb
```

Neon gives you `postgresql://...` (no `+asyncpg`). You **must** add `+asyncpg` after `postgresql` for async SQLAlchemy to work.

---

## 2. Seed users into the database

Run this on your **local machine** (one time only).

### Using the seed script:

```powershell
cd backend
pip install -r ../requirements.txt
$env:DATABASE_URL = "postgresql+asyncpg://user:pass@ep-xxx.neon.tech/neondb"
python seed.py
```

Expected output:
```
Database seeded successfully!
Admin: admin@aegis.com / admin123
HR: hr@aegis.com / hr123
```

Do **not** run seed on Vercel – run it locally with your Neon URL.

---

## 3. Set remaining env vars on Vercel

| Variable | Value | Where to set |
|---|---|---|
| `JWT_SECRET_KEY` | `node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"` | Vercel Dashboard → Settings → Environment Variables |
| `CORS_ORIGINS` | `["https://hr-sentinel-automation-nh0mlesgr.vercel.app"]` | Same place – use your actual Vercel domain |

Apply these to **Production** only (or all three: Production, Preview, Development).

---

## 4. Redeploy on Vercel

After changing env vars, trigger a fresh deploy:

- **Option A**: Push a dummy commit: `git commit --allow-empty -m "redeploy" && git push`
- **Option B**: Vercel Dashboard → Deployments → latest deploy → ⋮ → Redeploy

---

## 5. Test login

| Role | Email | Password |
|---|---|---|
| Admin | admin@aegis.com | admin123 |
| HR Manager | hr@aegis.com | hr123 |

Open your Vercel app URL and sign in.

---

## Troubleshooting

**Still getting 500?** Open DevTools → Network tab → click the failed `/login` request → check the **Response** tab. The `"detail"` field tells you exactly what's wrong:

| `"detail"` message | Likely cause |
|---|---|
| `"Invalid email or password"` | Seed not run yet |
| *connection error* | URL missing `+asyncpg` or wrong credentials |
| *"no such table"* | Tables not created (redeploy to trigger lifespan) |

If you see a connection error, double-check the `DATABASE_URL` format and that your Neon project allows connections from anywhere (Neon → Settings → IP Allow → Allow all).
