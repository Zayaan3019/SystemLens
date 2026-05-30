python -m pip install --upgrade pip
pip install pyinstaller
pyinstaller --onefile --name systemlens --paths src --collect-all systemlens --collect-all webview --add-data "src/systemlens/web;systemlens/web" src/systemlens/__main__.py
Write-Host "Build output: dist/systemlens.exe"