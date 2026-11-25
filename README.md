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
## Lab 9 — Final evaluation

Notebook: `notebooks/02_lab9_final.ipynb` (Colab, CPU, Gemini key in Secrets as `GEMINI_API_KEY`).

**Pipeline:** classify (TF-IDF logistic regression trained on the 2,995 labelled wiki sections)
→ retrieve (BM25 + MiniLM embeddings, Reciprocal Rank Fusion, soft category boost)
→ draft (Gemini, 5 cited passages, `answer` / `partial` / `escalate`)
→ flag (21 regex rules, v2).

**What the notebook measures**
- Retrieval: top-1/3/5, MRR, bootstrap 95 % CI, exact McNemar tests, per category,
  robustness (no paths, first line only, typos), sensitivity (RRF k, titles).
- Classifier: prototypes vs TF-IDF vs embeddings, with and without the test errors
  (leave-one-out, no leakage); an "other" class trained on out-of-scope tools.
- Pipeline: no filter vs hard vs soft filter vs oracle category.
- End-to-end vs Gemini alone: cited page, escalation, risky commands shown without warning.
- Flagger: two separate held-out command sets (v1 vs v2).

**Lab 9 changes after the first run**
- The drafter escalated 8/12 covered errors → it now gets 5 passages of 2,500 characters and may
  answer `partial`, listing unsupported steps.
- Flagger v2: `systemctl disable --now <firewall>` is caught; `rm /var/cache/pacman/pkg/*.part` is no longer flagged.

Results are exported to `results/` (`summary.json`, figures, `e2e_results.csv`).
