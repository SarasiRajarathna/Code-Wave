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
<<<<<<< HEAD
=======
    assert resp.get("cognitive_scratchpad") is not None, "Missing cognitive_scratchpad in response"
    assert resp.get("scepticism_index") is not None, "Missing scepticism_index in response"
>>>>>>> aeb2852b64774d175569b8a8f8fdafea56a6bf0a
    print(f"  [PASS] Query response received:")
    print(f"         Grounding Status : {resp['grounding_status']}")
    print(f"         Grounding Score  : {resp['grounding_score'] * 100:.1f}%")
    print(f"         Citations Count  : {len(resp['citations'])}")
    print(f"         Rich Media Image : {resp['rich_media']['image_url'] if resp['rich_media'] else 'None'}")
    print(f"         Reasoning Graph  : {'Present' if resp['reasoning_graph'] else 'None'}")
<<<<<<< HEAD
=======
    print(f"         Scratchpad Monologue: Present ({len(resp['cognitive_scratchpad'].get('internal_monologue_stream', []))} thoughts)")
    print(f"         Scepticism Lens : {resp['scepticism_index'].get('dominant_perspective')}")
>>>>>>> aeb2852b64774d175569b8a8f8fdafea56a6bf0a

    print("\n[TEST API 6/6] Testing POST /api/query/stream (Server-Sent Events) ...")
    r_stream = client.post("/api/query/stream", json={"question": "Where is Greyfell Citadel located?", "max_hops": 1})
    assert r_stream.status_code == 200, f"Streaming failed: {r_stream.text}"
    events_found = 0
    tokens_found = 0
    final_result_found = False
    for line in r_stream.iter_lines():
        if line and line.startswith("data: "):
            events_found += 1
            payload_str = line[6:]
            try:
                import json
                ev = json.loads(payload_str)
                if ev.get("event") == "token":
                    tokens_found += 1
                elif ev.get("event") == "final_result":
                    final_result_found = True
            except:
                pass
    assert events_found > 0, "No SSE events returned"
    assert final_result_found, "final_result event not found in stream"
    print(f"  [PASS] Stream verified: {events_found} total events, {tokens_found} streamed tokens, final_result received.")

<<<<<<< HEAD
    print("\n[TEST API 7/7] Testing POST /api/benchmark/run (Automated Evaluation Suite) ...")
=======
    print("\n[TEST API 7/8] Testing Multi-Turn Dialogue & Coreference Resolution ...")
    test_sid = "test_dialogue_session"
    r_turn1 = client.post("/api/query", json={"question": "Who was the ruler of the Shattered Vale when Greyfell Citadel was constructed?", "session_id": test_sid})
    assert r_turn1.status_code == 200
    r_turn2 = client.post("/api/query", json={"question": "What happened to him during the war?", "session_id": test_sid})
    assert r_turn2.status_code == 200
    resp_turn2 = r_turn2.json()
    coref = resp_turn2.get("coreference_resolution")
    assert coref is not None and coref.get("was_resolved"), f"Expected coreference resolution, got: {coref}"
    print(f"  [PASS] Multi-turn resolved: '{coref['original_query']}' -> '{coref['resolved_query']}' (Anchored to '{coref['anchor_entity']}')")

    print("\n[TEST API 8/8] Testing POST /api/benchmark/run (Automated Evaluation Suite) ...")
>>>>>>> aeb2852b64774d175569b8a8f8fdafea56a6bf0a
    r_bm = client.post("/api/benchmark/run")
    assert r_bm.status_code == 200, f"Benchmark failed: {r_bm.text}"
    bm_data = r_bm.json()
    assert bm_data["summary"]["total_cases"] == 6, f"Expected 6 cases, got {bm_data['summary']['total_cases']}"
    assert bm_data["summary"]["pass_rate_pct"] == 100.0, f"Expected 100% pass, got {bm_data['summary']['pass_rate_pct']}%"
    print(f"  [PASS] Live Benchmark: {bm_data['summary']['passed_cases']}/{bm_data['summary']['total_cases']} cases passed ({bm_data['summary']['pass_rate_pct']}%), Grounding: {bm_data['summary']['avg_grounding_pct']}%, Zero-Hallucination: {bm_data['summary']['zero_hallucination_rate_pct']}%.")

    print("\n===========================================================================")
    print(" [FASTAPI VERIFICATION PASSED] All REST endpoints fully functional!")
    print("===========================================================================\n")

if __name__ == "__main__":
    test_fastapi_endpoints()
