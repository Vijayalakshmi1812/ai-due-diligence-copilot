import argparse
import json

from dotenv import load_dotenv

load_dotenv()

from app.retrieve import MODES, retrieve  # noqa: E402


def is_relevant(text: str, keywords, min_match: int) -> bool:
    t = text.lower()
    return sum(k.lower() in t for k in keywords) >= min_match


def eval_retrieval(qa, mode: str, k: int) -> dict:
    hits, rr, prec = 0, 0.0, 0.0
    for item in qa:
        res = retrieve(item["question"], item["company"], k=k, mode=mode)
        flags = [is_relevant(r["text"], item["expected_keywords"], item.get("min_match", 1)) for r in res]
        if any(flags):
            hits += 1
            rr += 1.0 / (flags.index(True) + 1)
        prec += sum(flags) / max(len(flags), 1)
    n = len(qa)
    return {"hit@k": hits / n, "mrr": rr / n, "precision@k": prec / n}


def eval_faithfulness(qa, k: int):
    """Returns (average score, number of questions scored). Skips questions that fail."""
    from app.analyze import ask, chat

    judge_system = (
        "You are a strict fact-checker. Split the ANSWER into atomic factual claims and count how many "
        "are directly supported by the CONTEXT. Return ONLY JSON: "
        '{"total_claims": int, "supported_claims": int}'
    )
    scores = []
    for i, item in enumerate(qa, 1):
        try:
            res = ask(item["question"], item["company"], k=k)
            ctx = "\n\n".join(res["contexts"])
            raw = chat(judge_system, f"CONTEXT:\n{ctx}\n\nANSWER:\n{res['answer']}", json_mode=True)
            d = json.loads(raw)
            total = max(int(d.get("total_claims", 0)), 1)
            scores.append(min(int(d.get("supported_claims", 0)) / total, 1.0))
            print(f"  faithfulness {i}/{len(qa)}: {scores[-1]:.2f}")
        except Exception as e:
            print(f"  faithfulness {i}/{len(qa)}: skipped ({type(e).__name__})")
    if not scores:
        return None, 0
    return sum(scores) / len(scores), len(scores)


def save(lines):
    with open("evaluation/results.md", "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--qa", default="evaluation/qa_set.json")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--faithfulness", action="store_true")
    args = ap.parse_args()

    qa = json.load(open(args.qa, encoding="utf-8"))
    rows = []
    for mode in MODES:
        m = eval_retrieval(qa, mode, args.k)
        rows.append((mode, m))
        print(f"{mode:15s} hit@{args.k}={m['hit@k']:.2f}  MRR={m['mrr']:.2f}  P@{args.k}={m['precision@k']:.2f}")

    lines = [
        f"Questions: {len(qa)}",
        "",
        f"| Strategy | Hit@{args.k} | MRR | Precision@{args.k} |",
        "|---|---|---|---|",
    ] + [f"| {mode} | {m['hit@k']:.2f} | {m['mrr']:.2f} | {m['precision@k']:.2f} |" for mode, m in rows]

    save(lines)  # retrieval results are saved even if faithfulness fails
    print("\nSaved retrieval results to evaluation/results.md")

    if args.faithfulness:
        print("\nRunning faithfulness check (calls Groq)...")
        f, n = eval_faithfulness(qa, args.k)
        if f is None:
            print("Faithfulness could not be computed (check your internet connection and API key).")
        else:
            print(f"\nFaithfulness (hybrid_rerank answers): {f:.2f}  ({n}/{len(qa)} questions scored)")
            lines.append(f"\nFaithfulness (LLM-judged, hybrid_rerank): **{f:.2f}** ({n}/{len(qa)} questions scored)")
            save(lines)
            print("Updated evaluation/results.md")


if __name__ == "__main__":
    main()