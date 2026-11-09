#!/usr/bin/env bash
# One command for the whole data setup:
#   bash run_all.sh            # everything
#   bash run_all.sh --no-fetch # skip the Arch Wiki download (reuse data/corpus.jsonl)
set -euo pipefail
cd "$(dirname "$0")"
FETCH=1; [[ "${1:-}" == "--no-fetch" ]] && FETCH=0
step() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }

step "1/6 Python environment (.venv)"
[[ -d .venv ]] || python3 -m venv .venv
source .venv/bin/activate
pip install -q --disable-pip-version-check requests beautifulsoup4 pytest
echo "ok"

step "2/6 Eval set (24 cases)"
python scripts/build_eval_set.py

step "3/6 Tests (risk flagger)"
python -m pytest -q tests

if [[ $FETCH -eq 1 ]]; then
  step "4/6 Arch Wiki corpus (~10 min)"
  python scripts/fetch_archwiki.py --out data/corpus.jsonl.tmp
  mv data/corpus.jsonl.tmp data/corpus.jsonl
else
  step "4/6 Arch Wiki corpus: skipped (--no-fetch)"
  [[ -f data/corpus.jsonl ]] || { echo "data/corpus.jsonl missing, rerun without --no-fetch"; exit 1; }
fi

step "5/6 Man pages"
bash scripts/fetch_manpages.sh data/man | grep -c '^ok' | xargs -I{} echo "{} man pages saved in data/man/"

step "6/6 Coverage check"
python scripts/check_coverage.py

printf '\n\033[1;32mAll done.\033[0m\n'
