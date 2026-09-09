"""Forwarding wrapper to src/ingest/run_vector_ingest.py"""
import sys
from pathlib import Path

src_dir = Path(__file__).resolve().parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from ingest.run_vector_ingest import main

if __name__ == "__main__":
    main()
