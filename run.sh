#!/usr/bin/env bash
set -e
[ -x .venv/bin/python ] || python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
[ -f .env ] || cp .env.example .env
python -m khub.cli seed
python -m khub.server
