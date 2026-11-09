#!/usr/bin/env python3
"""Check that every reference page of the eval set exists in the corpus + corpus stats.
    python scripts/check_coverage.py
"""
import json, collections, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
corpus = [json.loads(l) for l in open(root / "data/corpus.jsonl", encoding="utf-8")]
cases = [json.loads(l) for l in open(root / "data/eval_24.jsonl", encoding="utf-8")]

pages = {c["page"] for c in corpus}
by_dom = collections.defaultdict(set)
for c in corpus:
    by_dom[c["domain"]].add(c["page"])
print(f"Corpus: {len(pages)} pages, {len(corpus)} sections")
for d, p in by_dom.items():
    print(f"  {d:13} {len(p):3} pages")

missing = [(c["id"], c["ref_page"]) for c in cases if c["ref_page"] and c["ref_page"] not in pages]
print(f"\nEval ref pages in corpus: {sum(1 for c in cases if c['ref_page']) - len(missing)}/"
      f"{sum(1 for c in cases if c['ref_page'])}")
for i, p in missing:
    print(f"  MISSING {i}: {p}")
