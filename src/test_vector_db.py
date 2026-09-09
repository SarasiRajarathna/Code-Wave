"""Forwarding wrapper to src/ingest/test_vector_db.py"""
import sys
from pathlib import Path
import argparse

src_dir = Path(__file__).resolve().parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from ingest.test_vector_db import test_queries

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Vector DB Search")
    parser.add_argument("--provider", type=str, default="local", choices=["local", "voyage"])
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()

    test_queries(provider=args.provider, top_k=args.top_k)
