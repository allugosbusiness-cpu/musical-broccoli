# Railway Configuration for PulseTrack Backend

## Deployment Files Created:
✅ requirements.txt - Python dependencies for production
✅ Procfile - Process configuration (gunicorn + migrations)
✅ runtime.txt - Python version (3.14.4)
✅ railway.json - Railway project settings
✅ .env - Environment variables

## Steps to Deploy on Railway:

### 1. Go to https://railway.app
- Sign up with GitHub (recommended for easy integration)

### 2. Create New Project
- Click "Create New Project"
- Select "Deploy from GitHub" or "Deploy from Repo"
- Connect your GitHub account (if using GitHub option)
- Or upload the Fleet Management folder

### 3. Configure Project
- **Name:** pulsetrack-backend
- **Root Directory:** server/

### 4. Set Environment Variables (Critical!)
Add these in Railway dashboard:
```
DEBUG = False
SECRET_KEY = generate-secure-random-string-here
ALLOWED_HOSTS = *.railway.app,*.vercel.app,localhost,127.0.0.1
CORS_ALLOWED_ORIGINS = https://pulsetrack-frontend-henna.vercel.app,http://localhost:5173
DATABASE_URL = [Railway will auto-generate PostgreSQL]
```

### 5. Connect Database (if needed)
- Click "Add Plugin"
- Select "PostgreSQL"
- Railway auto-configures DATABASE_URL

### 6. Deploy
- Click "Deploy"
- Wait 2-3 minutes
- Get your backend URL: https://pulsetrack-backend-prod.railway.app

## Frontend Update
After backend deploys, update mobile app and frontend:
```
VITE_API_BASE_URL = https://your-backend-url.railway.app/api/v1
```

## Generate Secure SECRET_KEY
Run in Python:
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```
Or use: https://djecrety.ir/
