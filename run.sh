#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON=python
else
  echo "Python 3 not found. Install Python 3 and try again." >&2
  exit 1
fi

CREATED_VENV=0
if [ ! -d ".venv" ]; then
  "$PYTHON" -m venv .venv
  CREATED_VENV=1
fi

if [ -x ".venv/bin/python" ]; then
  VENV_PYTHON=".venv/bin/python"
elif [ -x ".venv/Scripts/python.exe" ]; then
  VENV_PYTHON=".venv/Scripts/python.exe"
else
  echo "Python from the virtual environment was not found in .venv." >&2
  exit 1
fi

if [ "$CREATED_VENV" = "1" ]; then
  "$VENV_PYTHON" -m pip install --upgrade pip
  "$VENV_PYTHON" -m pip install -r requirements.txt
fi

exec "$VENV_PYTHON" -m streamlit run app.py
