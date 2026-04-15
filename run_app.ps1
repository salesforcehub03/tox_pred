$BackendProcess = Start-Process python -ArgumentList "research/app/api.py" -PassThru -NoNewWindow
Write-Host "Backend started on http://127.0.0.1:8125" -ForegroundColor Yellow

cd research-frontend
npm run dev
