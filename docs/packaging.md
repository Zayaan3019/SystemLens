# SystemLens Packaging & Services

## Cross-platform packaging (PyInstaller)

### Windows (MSI)
1) Install PyInstaller:
```
pip install pyinstaller
```
2) Build executable:
```
pyinstaller --onefile --name systemlens --paths src --collect-all systemlens --add-data "src/systemlens/web;systemlens/web" src/systemlens/__main__.py
```
3) Convert to MSI (optional):
- Use WiX Toolset or Advanced Installer to wrap `dist/systemlens.exe` into an MSI.

### macOS (DMG)
1) Build:
```
pyinstaller --onefile --name systemlens --paths src --collect-all systemlens --add-data "src/systemlens/web:systemlens/web" src/systemlens/__main__.py
```
2) Create DMG:
```
hdiutil create systemlens.dmg -srcfolder dist/systemlens.app
```

### Linux (AppImage)
1) Build:
```
pyinstaller --onefile --name systemlens --paths src --collect-all systemlens --add-data "src/systemlens/web:systemlens/web" src/systemlens/__main__.py
```
2) Wrap into AppImage (optional) using appimagetool.

## Background service/daemon

### Linux (systemd)
Use [services/systemd/systemlens.service](../services/systemd/systemlens.service).

### macOS (launchd)
Use [services/macos/com.systemlens.plist](../services/macos/com.systemlens.plist).

### Windows (Task Scheduler)
Use [services/windows/systemlens.xml](../services/windows/systemlens.xml).
