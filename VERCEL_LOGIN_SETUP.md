# Login Setup for Vercel Deployment

## 1. Create a PostgreSQL database

SQLite won't work on Vercel (ephemeral filesystem). Use **Neon** (free):

1. Go to [neon.tech](https://neon.tech) → sign up → create a project
2. Copy the connection string (looks like `postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb`)
3. Append `+asyncpg` after `postgresql`:
   ```
   postgresql+asyncpg://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb
   ```

## 2. Set environment variables in Vercel

**Vercel Dashboard → Your Project → Settings → Environment Variables → Add**

| Variable | Value |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@ep-xxx.neon.tech/neondb` |
| `JWT_SECRET_KEY` | Run `node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"` and paste output |
| `CORS_ORIGINS` | `["https://hr-sentinel-automation-ai-two.vercel.app"]` |

## 3. Seed users

Run this on **your local machine** (not on Vercel). The seed script connects to your Neon DB and creates user accounts.

### Using the seed script directly:

```bash
# 1. Navigate to backend
cd backend

# 2. Install deps
pip install -r ../requirements.txt

# 3. Set your Neon URL temporarily (use your actual URL)
$env:DATABASE_URL = "postgresql+asyncpg://user:pass@ep-xxx.neon.tech/neondb"

# 4. Run seed
python seed.py
```

Expected output:
```
Database seeded successfully!
Admin: admin@aegis.com / admin123
HR: hr@aegis.com / hr123
```

### Or using a one-shot command (PowerShell):

```powershell
cd backend
pip install -r ../requirements.txt
$env:DATABASE_URL = "postgresql+asyncpg://user:pass@ep-xxx.neon.tech/neondb"
python seed.py
```

## 4. Redeploy on Vercel

After adding env vars, go to **Vercel Dashboard → Deployments → ... → Redeploy** (or just push another commit).

## 5. Log in

| Role | Email | Password |
|---|---|---|
| Admin | admin@aegis.com | admin123 |
| HR Manager | hr@aegis.com | hr123 |

---

> **Note**: No employee or attendance data is created by seed. After login, upload Excel/CSV files from the dashboard to populate the system.
