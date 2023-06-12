#! /bin/bash
mkdir -p ~/personal-data/app_data/static
# cp src/frontend/static/* ~/personal-data/app_data/static/.
ln -s ~/personal-data
mkdir env
touch env/ingest.env.list
touch env/frontend.env.list
python -m src.init