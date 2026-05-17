# CORS Error Fix Guide

## Problem
Your frontend at `https://pulsetrack-frontend-henna.vercel.app` is getting blocked by CORS policy when trying to access the backend at `https://pulsetrack-back.onrender.com`.

**Errors:**
```
Access to XMLHttpRequest at 'https://pulsetrack-back.onrender.com/api/trucks/all_trucks_with_trails/' 
from origin 'https://pulsetrack-frontend-henna.vercel.app' has been blocked by CORS policy: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## Root Cause
The Django backend's CORS configuration is using placeholder/example domains that don't match your actual Vercel frontend URL. The production settings need to include `https://pulsetrack-frontend-henna.vercel.app` in the allowed origins list.

## Solution

### Step 1: Update Django Settings (✅ COMPLETED)
The [Logistics/settings.py](Logistics/settings.py) file has been updated to:
- Support environment variable configuration for CORS origins
- Default to your actual frontend URL in production
- Parse comma-separated origins from `CORS_ALLOWED_ORIGINS` environment variable

**Changes made:**
```python
# Production mode now checks environment variable:
cors_origins = config('CORS_ALLOWED_ORIGINS', default='https://pulsetrack-frontend-henna.vercel.app,https://pulsetrack.example.com')
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in cors_origins.split(',')]
```

### Step 2: Deploy to Render
You need to redeploy your backend to Render for the changes to take effect:

**Option A: Via Render Dashboard (Recommended)**
1. Go to https://dashboard.render.com/
2. Click on your backend service (likely `pulsetrack-back`)
3. Click **"Manual Deploy"** or **"Deploy"** button
4. Wait for deployment to complete (usually 2-3 minutes)

**Option B: Via Git Push**
```bash
cd "c:\Users\Mugogo\Desktop\Fleet Management\server"
git add Logistics/settings.py
git commit -m "Fix: Add production CORS configuration for Vercel frontend"
git push origin main
# Render will auto-deploy
```

### Step 3: Verify Environment Variables (Optional but Recommended)
In Render Dashboard, ensure you have the environment variable set:
1. Go to your service settings
2. Click **Environment**
3. Add this variable if not present (optional - the code defaults to your URLs):
   ```
   CORS_ALLOWED_ORIGINS=https://pulsetrack-frontend-henna.vercel.app,https://pulsetrack.example.com
   ```

### Step 4: Test the Fix
After deployment, test the endpoint:

**Using curl:**
```bash
curl -H "Origin: https://pulsetrack-frontend-henna.vercel.app" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -X OPTIONS https://pulsetrack-back.onrender.com/api/trucks/all_trucks_with_trails/
```

**Expected response should include:**
```
Access-Control-Allow-Origin: https://pulsetrack-frontend-henna.vercel.app
```

**Or simply:**
1. Refresh your Vercel frontend: https://pulsetrack-frontend-henna.vercel.app
2. Open browser DevTools (F12)
3. Check Network tab - the API requests should no longer show CORS errors
4. Truck data should load successfully

## Additional Notes

### Why This Happened
- Django's CORS middleware wasn't configured with your production Vercel URL
- Default/placeholder domains in production settings didn't match your actual deployment URLs

### Security Note
- **Development (DEBUG=True):** `CORS_ALLOW_ALL_ORIGINS = True` allows requests from any origin
- **Production (DEBUG=False):** Only specified origins are allowed, which is more secure

### If Issues Persist
1. Verify `DEBUG=False` is set in Render environment
2. Check Render logs: Dashboard → Your Service → Logs
3. Ensure the git push deployed successfully
4. Clear browser cache (Ctrl+Shift+Delete) and reload
5. Check that `django-cors-headers` is in `requirements.txt`

## Files Modified
- [Logistics/settings.py](Logistics/settings.py#L133-L163) - CORS configuration with environment variable support
