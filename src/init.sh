#! /bin/bash
mkdir ~/personal-data
ln -s ~/personal-data
touch env/ingest.env.list
touch env/frontend.env.list
python -m src.init