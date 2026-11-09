# Linux Error Diagnoser — ALAKHOUCH · BENDI

Paste a Linux terminal error → category → top-3 Arch Wiki sections → cited fix (or "escalate") → risky commands flagged.

| # | Capability | Model | File | Status |
|---|---|---|---|---|
| 1 | Classify (6 classes + other) | fine-tuned text classifier (Labs 3–4) | `src/classifier.py` | todo |
| 2 | Retrieve top-3 sections | BM25 + sentence-transformer (Labs 5–6) | `src/retriever.py` | todo |
| 3 | Draft cited diagnosis / escalate | Gemini (only LLM) | `src/drafter.py` | todo |
| 4 | Flag risky commands | rules | `src/risk_flagger.py` | **done + tests** |

## Tonight (on your machine — Arch Wiki is not reachable from the cloud)
```bash
pip install requests beautifulsoup4
python scripts/fetch_archwiki.py --out data/corpus.jsonl     # ~150 pages, 6 domains, split into sections
bash  scripts/fetch_manpages.sh data/man                     # on the Kali/Ubuntu VM
```

## Evaluation set
`python scripts/build_eval_set.py` → `data/eval_24.jsonl`: 18 covered (3 per domain) + 3 out-of-corpus + 3 risky.
Each case: error, category, ref page/URL, ref fix. **To do:** replace the synthetic error texts with real captures from our VMs (`source` field).

## Tests
`python -m pytest -q tests`
