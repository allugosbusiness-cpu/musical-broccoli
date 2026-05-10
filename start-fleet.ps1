# start-fleet.ps1
# Launch Fleet Management backend, frontend, and web in separate terminals

# Ensure virtual environment is activated for backend
Write-Host "Starting backend (FastAPI)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "cd '$PWD\server'; .\.venv\Scripts\activate; uvicorn main:app --reload"

# Start React Native frontend
Write-Host "Starting mobile frontend (Expo)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "cd '$PWD\mobile'; npm install; expo start -c"

# Start web frontend (if present)
Write-Host "Starting web frontend..."
Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "cd '$PWD\client\Frontend'; npm install; npm run start"
