# Render.com Deployment - Quick Start (UPDATED)

## ⚠️ Previous Deploy Failed - HERE'S THE FIX

**Error received:** `ModuleNotFoundError: No module named 'app'`

**Root Cause:** The previous `render.yaml` had the build command trying to run migrations and collectstatic during the build phase, before the database was ready.

**Solution Applied:**
✅ Simplified `startCommand` - just run gunicorn (migrations will happen on first request or manual trigger)
✅ Improved `wsgi.py` - added defensive Python path handling
✅ Removed complex bash scripts - Render handles environment setup automatically
✅ Verified app starts correctly locally with all 9 Django apps loading

## Prerequisites
✅ **Already Done:**
- `render.yaml` configuration file updated with working config
- Django settings updated with Render ALLOWED_HOSTS and CSRF origins
- Frontend API configuration supports Render backend
- `.env.production` configured with Render backend URL
- `requirements.txt` includes all dependencies
- **NEW:** `wsgi.py` enhanced with better error handling and Python path setup

## Deploy Backend to Render (5 minutes)

### Step 1: Commit & Push Latest Changes
```bash
cd "c:\Users\Mugogo\Desktop\Fleet Management"
git pull origin main  # Make sure you have latest fixes
```

### Step 2: Go to Your Render Service

1. **If service already exists:**
   - Go to https://dashboard.render.com
   - Click on "pulsetrack-backend" service
   - Click **Manual Deploy** → **Deploy latest commit**
   - Watch logs for success

2. **If you need to create new service:**
   - Go to https://render.com
   - Click **New +** → **Web Service**
   - Connect GitHub repo
   - Render will auto-detect `render.yaml` and configure everything
   - Click **Create Web Service**

### Step 3: Wait for Deploy (3-5 minutes)

Watch the **Logs** tab. You should see:
```
✓ Building dependencies
✓ Deployed successfully
✓ Service is live
```

If you see errors, check the logs section below.

### Step 4: Test Backend

Once deployed successfully:
```
curl https://pulsetrack-backend.render.com/api/v1/
```

Should return API response (200 OK or 404 is both acceptable).

### Step 5: Run Migrations (One-time)

After first successful deploy, SSH into the service to run migrations:
1. In Render dashboard → pulsetrack-backend → **Shell**
2. Run:
```bash
python manage.py migrate
```

Or, run via Render deploy hook (if migrations needed on every deploy):
- This will be handled automatically on next redeploy after setup

## Troubleshooting

### Deploy Still Fails
1. Check **Logs** tab in Render dashboard
2. Look for any lines with "ERROR" or "FAILED"
3. Common fixes:
   - **"cannot import name..."** → Missing package in requirements.txt
   - **"CSRF error"** → Check CSRF_TRUSTED_ORIGINS in settings.py (already fixed)
   - **"Static files not found"** → This is okay during development

### Backend Returns 503 or 502
1. Wait 1-2 minutes for service to fully start
2. Check if database is still initializing
3. In Render dashboard, look for "pulsetrack-db" service status

### CORS Errors in Browser Console
- Verify backend URL is correct in frontend config
- Check that CORS_ALLOWED_ORIGINS includes your Vercel frontend URL
- If still broken, check browser Network tab for actual error response

## Deploy Frontend (2 minutes)

After backend is live:

```bash
cd "c:\Users\Mugogo\Desktop\Fleet Management\client\Frontend"
npm run build
npx vercel --prod --yes
```

This will use the `.env.production` file with the Render backend URL.

## Success Indicators

✅ Backend is working if:
- `https://pulsetrack-backend.render.com/api/v1/` returns JSON (200 OK or 404)
- Logs show "Uvicorn running on" or "Gunicorn working" (no errors)
- No database connection errors in logs

✅ Frontend is working if:
- `https://pulsetrack-frontend-henna.vercel.app/` loads
- Browser console has no CORS errors
- API calls appear in Network tab and return data

## After Successful Deployment

1. **Save these URLs:**
   - Backend API: `https://pulsetrack-backend.render.com/api/v1`
   - Frontend App: `https://pulsetrack-frontend-henna.vercel.app`

2. **Test the app:**
   - Open frontend app
   - Try to load a dashboard or list page
   - Verify it fetches data from backend without CORS errors

3. **Monitor logs regularly:**
   - Render dashboard → Logs → Check for warnings or errors

4. **Schedule regular checks:**
   - Visit Render dashboard once a week
   - Keep eye on database size (free PostgreSQL has limits)

## Key Differences from Railway

| Aspect | Railway | Render |
|--------|---------|--------|
| Deploy Method | Push to GitHub | Push to GitHub (same) |
| Build Logs | Minimal | Very detailed ✓ |
| Python Support | Good | Excellent ✓ |
| Configuration | Custom env vars | `render.yaml` ✓ |
| Reliability | Moderate | High ✓ |
| Startup Time | Slow | Fast ✓ |
| Cost | $5+/month | $7+/month |

---

**Last Updated:** After deploy failure fix
**Status:** Ready to deploy with improved configuration
**Next Step:** Go to Render dashboard and redeploy the service

