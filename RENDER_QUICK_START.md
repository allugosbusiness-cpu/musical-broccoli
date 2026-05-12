# Render.com Deployment - Quick Start

## Prerequisites
✅ **Already Done:**
- `render.yaml` configuration file created
- Django settings updated with Render ALLOWED_HOSTS and CSRF origins
- Frontend API configuration updated to support Render backend
- `.env.production` file configured with Render backend URL
- `requirements.txt` includes all dependencies (gunicorn, psycopg2-binary, dj-database-url)

## Deploy Backend to Render (5 minutes)

### Step 1: Commit & Push Changes
```bash
cd "c:\Users\Mugogo\Desktop\Fleet Management"
git add -A
git commit -m "Prepare for Render.com deployment - add render.yaml and configuration"
git push origin main
```

### Step 2: Create Render Account & Project
1. Go to https://render.com
2. Click **New +** → **Web Service**
3. Connect your GitHub account
4. Select repository: `Fleet Management`
5. Fill in:
   - **Name**: `pulsetrack-backend`
   - **Root Directory**: leave blank (or `.` if required)
   - **Runtime**: Python 3.10 (selected in render.yaml)
6. Scroll down and click **Create Web Service**

### Step 3: Wait for Deploy
- Render will read `render.yaml`
- It will automatically:
  - Create PostgreSQL database
  - Install dependencies
  - Run migrations
  - Start the web service
- Monitor progress in **Logs** tab
- Once green checkmark appears, deployment is complete ✓

### Step 4: Get Your Backend URL
After deployment succeeds:
- Your backend URL will be: `https://pulsetrack-backend.render.com`
- Test it: `https://pulsetrack-backend.render.com/api/v1/` (should show 404 or API root)

## Deploy Frontend to Vercel (2 minutes)

### Step 1: Rebuild Frontend
```bash
cd "c:\Users\Mugogo\Desktop\Fleet Management\client\Frontend"
npm run build
```

### Step 2: Deploy to Vercel
```bash
npx vercel --prod --yes
```

This will automatically use the `.env.production` file with the Render backend URL.

### Step 3: Verify
- Frontend should load at: `https://pulsetrack-frontend-henna.vercel.app`
- Check browser console for any API errors
- Test a page that makes an API call

## Troubleshooting

### Backend shows 500 error
Check Render logs:
1. Render Dashboard → pulsetrack-backend → **Logs**
2. Look for: database connection errors, import errors, or migration failures
3. Common fixes:
   - Wait 2-3 minutes for database to be ready
   - Check that PostgreSQL service is running (look for pulsetrack-db in services)
   - Verify `DATABASE_URL` environment variable is set

### Frontend can't reach backend
1. Check browser Network tab for failed requests
2. Look for CORS errors in browser console
3. Verify backend URL is correct in browser devtools
4. Check that `CORS_ALLOWED_ORIGINS` in Django settings includes the Vercel frontend

### Build fails on Render
1. Check **Logs** during build step
2. Common causes:
   - Missing Python package in requirements.txt
   - Static files collection failing
   - Database migration error
3. Fix locally and push again

## After Deployment

### Pin Important URLs
- **Backend API**: `https://pulsetrack-backend.render.com/api/v1`
- **Frontend App**: `https://pulsetrack-frontend-henna.vercel.app`
- **Render Dashboard**: `https://dashboard.render.com`

### Set Up Monitoring
1. Render dashboard → Services → Alerts
2. Enable alerts for failures
3. Configure notification email

### Regular Maintenance
- Check logs weekly for errors
- Monitor database size (PostgreSQL free tier has limits)
- Update dependencies monthly

## Next Steps After Successful Deploy

1. **Test all endpoints** in PulseTrack app
2. **Load test** with sample data
3. **Set up error tracking** (optional: Sentry.io)
4. **Configure auto-deploy** (Render does this by default from main branch)
5. **Set up backups** (Render handles database backups automatically)

---

**Total Deploy Time**: ~15 minutes (including build time)
**Cost**: Free tier available, ~$7-14/month for production-grade
