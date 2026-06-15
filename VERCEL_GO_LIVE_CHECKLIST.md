# Vercel Go-Live Checklist

## ✅ Done

| Step | Status |
|---|---|
| Code deployed to Vercel | ✅ |
| Neon PostgreSQL database created | ✅ |
| `DATABASE_URL` set in Vercel env (prod + preview + deployment) | ✅ |
| Seed script run – users created in Neon DB | ✅ |

## ❌ Still needed

### 1. Set remaining env vars on Vercel

| Variable | Value |
|---|---|
| `JWT_SECRET_KEY` | Run `node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"` and paste the output |
| `CORS_ORIGINS` | `["https://hr-sentinel-automation-nh0mlesgr.vercel.app"]` (use your actual domain) |

### 2. Redeploy

```powershell
git commit --allow-empty -m "redeploy with Neon DB"
git push
```

Vercel will auto-deploy. Wait ~2 minutes.

### 3. Login

Open your Vercel URL → Sign in:

| Email | Password |
|---|---|
| admin@aegis.com | admin123 |
| hr@aegis.com | hr123 |

### 4. Use the app

Upload Excel/CSV attendance files from the dashboard to populate employees and attendance data.

---

## If login still fails

Open DevTools → Network tab → click the 500 login request → check **Response** body for the `"detail"` message.
