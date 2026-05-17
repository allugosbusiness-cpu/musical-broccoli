# Railway Database Setup Guide

## ✅ Automatic Setup (Recommended)

When you redeploy to Railway, the `Procfile` will automatically run:
```bash
release: python manage.py migrate && python manage.py setup_database
```

This will:
1. Run all Django migrations
2. Create superuser account (admin/admin123)
3. Load sample data (if add_sample_data.py exists)

## 🔧 Manual Setup (Current Issue)

If you deployed BEFORE these files were created, manually initialize:

### Option 1: Railway CLI (Recommended)
```powershell
# Navigate to server directory
cd "c:\Users\Mugogo\Desktop\Fleet Management\server"

# Make sure you're authenticated
railway login

# Link to your Railway project
railway link

# Run migrations directly
railway run python manage.py migrate

# Run setup command
railway run python manage.py setup_database

# Test the API
python -c "
import requests
r = requests.get('https://musical-broccoli-production.up.railway.app/api/v1/trucks/', timeout=5)
print(f'Status: {r.status_code}')
if r.status_code == 200:
    print(f'✅ Success! Got {len(r.json())} trucks')
else:
    print(f'Error: {r.text[:200]}')
"
```

### Option 2: Railway Dashboard
1. Go to your Railway project dashboard
2. Click the PostgreSQL plugin
3. Click "Data"
4. In the browser console or terminal:
   ```sql
   -- Run this to check if migrations have run
   SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
   ```
5. If tables are missing, use Option 1 (Railway CLI)

### Option 3: Redeploy with Git Push
```powershell
# Make sure you committed the new setup files
git add .
git commit -m "Add database setup management command"
git push

# Railway will auto-run the release: command from Procfile
# Check Railway dashboard → Deployments for logs
```

## 📊 What Gets Created

After setup_database runs:

**Database Tables:**
- auth_user, auth_group (Django auth)
- api_truck, api_driver, api_mission (Fleet data)
- api_alert, api_trackingdata (Real-time data)
- All other Django tables

**Superuser Account:**
- Username: `admin`
- Password: `admin123`
- Access: https://musical-broccoli-production.up.railway.app/admin

**Sample Data:**
- 5 trucks with GPS data
- 5 drivers
- 3 missions
- Pre-filled alerts and tracking

## 🧪 Verification

After setup, test these endpoints:

```powershell
# Get all trucks
curl "https://musical-broccoli-production.up.railway.app/api/v1/trucks/" | jq

# Get all drivers
curl "https://musical-broccoli-production.up.railway.app/api/v1/drivers/" | jq

# Get all missions
curl "https://musical-broccoli-production.up.railway.app/api/v1/missions/" | jq

# Admin panel
# Visit: https://musical-broccoli-production.up.railway.app/admin
# Login: admin / admin123
```

## ❌ Troubleshooting

**Still getting 500 errors?**
- Check Railway logs: `railway logs`
- Check if database URL is set: `railway vars`
- Try: `railway run python manage.py shell`

**Migrations not running?**
- Make sure Procfile exists in server/ directory
- Check Procfile format: exactly `release:` line
- Redeploy to trigger the release command

**PostgreSQL connection failed?**
- Add PostgreSQL plugin to Railway project
- Check plugin status in Railway dashboard
- Verify DATABASE_URL in Railway env vars

**Superuser already exists error?**
- The command is idempotent, this is safe
- You can reset: `railway run python manage.py shell`
  ```python
  from django.contrib.auth.models import User
  User.objects.filter(username='admin').delete()
  User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
  ```
