Write-Host "Installing Python requirements..." -ForegroundColor Cyan
pip install -r research/requirements.txt

Write-Host "Installing Frontend dependencies..." -ForegroundColor Cyan
cd research-frontend
npm install
cd ..

Write-Host "Setup complete!" -ForegroundColor Green
