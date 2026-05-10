#!/usr/bin/env python3
"""
PRIVA VP9508 Greenhouse Sensor Dashboard
Run: python3 run_dashboard.py
Then open: http://localhost:5000
"""
import subprocess, sys, os

print("📦 Checking dependencies...")
try:
    import flask
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "--break-system-packages"])
    import flask

# Run the server
os.chdir(os.path.dirname(os.path.abspath(__file__)))
subprocess.run([sys.executable, "app.py"])
