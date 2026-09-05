"""
query.py

Interactive CLI and Evaluation Runner for Code-Wave Ashen Era Assistant.
Supports:
1. Single question answering:
   python src/query.py --question "What is the recorded garrison strength of Greyfell Citadel?"

2. Interactive conversation mode:
   python src/query.py --interactive

3. Evaluation benchmark against sample_questions.json (for Member 3):
   python src/query.py --eval ../Ashen_Era_Archive/Ashen_Era_Archive/sample_questions.json
"""

import sys
import json
import argparse
from pathlib import Path

# Add src to sys.path
src_dir = Path(__file__).resolve().parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from agent.iterative_agent import AshenIterativeAgent
from retrieval.hybrid import HybridRetriever
from ingest.embeddings import get_embedding_model


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def print_banner():
    print("=" * 75)
    print("      CODE-WAVE -- ASHEN ERA ARCHIVE INTELLIGENT ASSISTANT")
    print("         Sub-track 1C: Searching the Way a Human Does")
    print("=" * 75)


def format_agent_output(result):
    print("\n" + "-" * 75)
    print(f"QUESTION: {result.question}")
    print("-" * 75)

    if result.hops:
        print("\n[REASONING & RETRIEVAL TRAIL]")
        for h in result.hops:
            print(f"  [Hop {h.hop_number}] Searched: \"{h.query}\"")
            if h.thought:
                print(f"            Thought : {h.thought}")

    print("\n[ANSWER]")
    print(result.answer)

    if result.citations:
        print("\n[CITATIONS]")
        for c in result.citations:
            print(f"  * {c}")

    if result.rich_media:
        print("\n[RELEVANT ARCHIVE FIGURE ATTACHED]")
        print(f"  Plate Title: {result.rich_media['title']}")
        print(f"  Local Path : {result.rich_media['path']}")

    print("-" * 75 + "\n")


def run_interactive(agent: AshenIterativeAgent):
    print_banner()
    print("Entering interactive mode. Type your question or 'exit' / 'quit' to stop.\n")

    while True:
        try:
            user_input = input("Ashen-Archive > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("Exiting. Farewell, Scholar of the Ashen Era.")
                break

            result = agent.run(user_input, verbose=True)
            format_agent_output(result)

        except KeyboardInterrupt:
            print("\nSession interrupted.")
            break
        except Exception as e:
            print(f"\nError processing query: {e}\n")


def run_evaluation(agent: AshenIterativeAgent, eval_file: str, output_file: str = "data/evaluation_results.json"):
    eval_path = Path(eval_file)
    if not eval_path.exists():
        print(f"Evaluation questions file not found: {eval_path}")
        return

    with open(eval_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    print_banner()
    print(f"Running automated benchmark on {len(questions)} test questions...")
    print(f"Test File: {eval_path}")

    results_summary = []
    for i, q_item in enumerate(questions, 1):
        qid = q_item.get("qid", f"q_{i}")
        track = q_item.get("track", "Unknown Track")
        q_text = q_item.get("question", "")

        print(f"\n[{i}/{len(questions)}] Processing [{qid}] ({track})")
        print(f"Query: {q_text}")

        res = agent.run(q_text, verbose=False)

        entry = {
            "qid": qid,
            "track": track,
            "question": q_text,
            "answer": res.answer,
            "citations": res.citations,
            "total_hops": len(res.hops),
            "rich_media": res.rich_media["title"] if res.rich_media else None,
            "is_sufficient": res.is_sufficient,
        }
        results_summary.append(entry)
        print(f"  -> Answer snippet: {res.answer[:120]}...")

    out_p = Path(output_file)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 75)
    print(f"Benchmark completed! Evaluated {len(results_summary)} questions.")
    print(f"Full results saved to: {out_p}")
    print("=" * 75 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Code-Wave Ashen Era Assistant Query Runner")
    parser.add_argument("--question", "-q", type=str, default=None, help="Single question to ask")
    parser.add_argument("--interactive", "-i", action="store_true", help="Launch interactive CLI chat")
    parser.add_argument("--eval", "-e", type=str, default=None, help="Path to evaluation JSON questions file")
    parser.add_argument("--provider", type=str, default="local", choices=["local", "voyage"], help="Embedding provider")
    parser.add_argument("--max-hops", type=int, default=3, help="Max reasoning hops")
    parser.add_argument("--no-cache", action="store_true", help="Bypass response cache")
    args = parser.parse_args()

    # Initialize retriever & agent
    embedder = get_embedding_model(provider=args.provider)
    retriever = HybridRetriever(embedding_model=embedder)
    agent = AshenIterativeAgent(retriever=retriever, max_hops=args.max_hops)

    if args.eval:
        run_evaluation(agent, eval_file=args.eval)
    elif args.interactive:
        run_interactive(agent)
    elif args.question:
        print_banner()
        res = agent.run(args.question, verbose=True, no_cache=args.no_cache)
        format_agent_output(res)
    else:
        # Default fallback to a sample test query
        sample_q = "According to the figure plate, what is the recorded garrison strength of Greyfell Citadel?"
        print_banner()
        print("No query supplied. Demonstrating sample run:")
        res = agent.run(sample_q, verbose=True, no_cache=args.no_cache)
        format_agent_output(res)


if __name__ == "__main__":
    main()
