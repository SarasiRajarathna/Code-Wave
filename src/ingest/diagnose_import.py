import sys
from pathlib import Path

print("=== DIAGNOSTIC ===")
this_file = Path(__file__).resolve()
print("This file's actual path:      ", this_file)

repo_root = this_file.parents[2]
print("Computed REPO_ROOT:           ", repo_root)

src_dir = repo_root / "src"
print("Computed src dir:             ", src_dir)
print("  -> exists?                  ", src_dir.exists())

ingest_dir = src_dir / "ingest"
print("Computed src/ingest dir:      ", ingest_dir)
print("  -> exists?                  ", ingest_dir.exists())

init_file = ingest_dir / "__init__.py"
print("src/ingest/__init__.py:       ", init_file, "-> exists?", init_file.exists())

loaders_file = ingest_dir / "loaders.py"
print("src/ingest/loaders.py:        ", loaders_file, "-> exists?", loaders_file.exists())

sys.path.insert(0, str(src_dir))
print("\nsys.path, first 5 entries:")
for p in sys.path[:5]:
    print("  ", p)

print("\nAttempting: import ingest")
try:
    import ingest
    print("  SUCCESS -- found at:", ingest.__file__)
except Exception as e:
    print("  FAILED:", repr(e))

print("\nAttempting: from ingest import loaders")
try:
    from ingest import loaders
    print("  SUCCESS -- found at:", loaders.__file__)
except Exception as e:
    print("  FAILED:", repr(e))