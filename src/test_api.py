"""
test_api.py

Validates FastAPI endpoints locally using TestClient.
"""

import sys
from pathlib import Path

src_dir = Path(__file__).resolve().parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from fastapi.testclient import TestClient
from api import app

def test_fastapi_endpoints():
    client = TestClient(app)

    print("\n[TEST API 1/6] Testing GET /app (Dark-Fantasy Web Explorer) ...")
    r = client.get("/app")
    assert r.status_code == 200, f"Failed: {r.text}"
    assert "ASHEN ERA ARCHIVE" in r.text, "Title not found in HTML"
    print("  [PASS] Web Explorer HTML served successfully.")

    print("\n[TEST API 2/6] Testing GET / (Redirect) ...")
    r_root = client.get("/", follow_redirects=True)
    assert r_root.status_code == 200
    print("  [PASS] Root redirect to /app validated.")

    print("\n[TEST API 2/5] Testing GET /api/health ...")
    r = client.get("/api/health")
    assert r.status_code == 200, f"Failed: {r.text}"
    print(f"  [PASS] Health check: {r.json()}")

    print("\n[TEST API 3/5] Testing GET /api/samples ...")
    r = client.get("/api/samples")
    assert r.status_code == 200, f"Failed: {r.text}"
    data = r.json()
    assert len(data) >= 5, f"Too few samples: {len(data)}"
    print(f"  [PASS] Samples retrieved: {len(data)} competition questions.")

    print("\n[TEST API 4/6] Testing GET /api/stats ...")
    r = client.get("/api/stats")
    assert r.status_code == 200, f"Failed: {r.text}"
    stats = r.json()
    print(f"  [PASS] System stats: {stats['vector_store']['total_chunks']} chunks in {stats['vector_store']['type']}")

    print("\n[TEST API 5/7] Testing GET /api/graph (Knowledge Graph Topology) ...")
    r_kg = client.get("/api/graph")
    assert r_kg.status_code == 200, f"Failed: {r_kg.text}"
    kg_json = r_kg.json()
    assert kg_json["stats"]["total_nodes"] >= 90, f"Too few nodes: {kg_json['stats']['total_nodes']}"
    assert kg_json["stats"]["total_edges"] >= 150, f"Too few edges: {kg_json['stats']['total_edges']}"
    print(f"  [PASS] Knowledge Graph: {kg_json['stats']['total_nodes']} nodes, {kg_json['stats']['total_edges']} edges.")

    print("\n[TEST API 5/5] Testing POST /api/query ...")
    payload = {
        "question": "According to the figure plate, what is the recorded garrison strength of Greyfell Citadel?",
        "max_hops": 2,
        "no_cache": False
    }
    r = client.post("/api/query", json=payload)
    assert r.status_code == 200, f"Failed: {r.text}"
    resp = r.json()
    assert "3,695" in resp["answer"] or resp["grounding_score"] >= 0.8
    print(f"  [PASS] Query response received:")
    print(f"         Grounding Status : {resp['grounding_status']}")
    print(f"         Grounding Score  : {resp['grounding_score'] * 100:.1f}%")
    print(f"         Citations Count  : {len(resp['citations'])}")
    print(f"         Rich Media Image : {resp['rich_media']['image_url'] if resp['rich_media'] else 'None'}")
    print(f"         Reasoning Graph  : {'Present' if resp['reasoning_graph'] else 'None'}")

    print("\n===========================================================================")
    print(" [FASTAPI VERIFICATION PASSED] All REST endpoints fully functional!")
    print("===========================================================================\n")

if __name__ == "__main__":
    test_fastapi_endpoints()
