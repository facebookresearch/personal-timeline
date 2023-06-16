#! /bin/bash
python -m src.ingest.workflow
python -m src.ingest.offline_processing
python -m src.ingest.create_episodes
python -m src.ingest.derive_episodes