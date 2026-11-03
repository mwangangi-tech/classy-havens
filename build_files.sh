#!/bin/bash
echo "BUILD START"
python3.12 -m pip install -r requirements.txt
python3.12 manage.py collectstatic --noinput --clear
python3.12 manage.py migrate
echo "BUILD END"