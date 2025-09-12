#!/usr/bin/env bash
python -m flask db upgrade
gunicorn --bind 0.0.0.0:$PORT kei:kei --workers 4
