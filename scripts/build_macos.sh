#!/usr/bin/env bash
python3 -m pip install --upgrade pip
python3 -m pip install pyinstaller
pyinstaller --onefile --name systemlens --paths src --collect-all systemlens --add-data "src/systemlens/web:systemlens/web" src/systemlens/__main__.py
