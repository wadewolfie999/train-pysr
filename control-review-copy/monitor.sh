#!/usr/bin/env bash
# Non-metric Act 5 campaign monitor. Never prints AUC or predictions.
set -euo pipefail

ACT5_ROOT="${1:-/Users/vaheedgorgeen/SR-Workspace/SR-Res-work/act-05}"
RUN_ID_FILE="$ACT5_ROOT/runs"/*/run-id.txt
# Resolve latest run root
RUN_ROOT="$(ls -d "$ACT5_ROOT"/runs/*/ 2>/dev/null | sort | tail -n 1)"
if [[ -z "${RUN_ROOT}" ]]; then
  echo "No Act 5 run directory found under $ACT5_ROOT"
  exit 1
fi
RUN_ROOT="${RUN_ROOT%/}"
STATUS="$RUN_ROOT/progress/campaign-status.json"
LEDGER="$RUN_ROOT/ledgers/attempt-ledger.jsonl"
PIDFILE="$RUN_ROOT/campaign.pid"

echo "=== SR-Res Act 5 non-metric monitor ==="
echo "RUN_ROOT: $RUN_ROOT"
echo "timestamp_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo

if [[ -f "$PIDFILE" ]]; then
  pid="$(cat "$PIDFILE")"
  if ps -p "$pid" >/dev/null 2>&1; then
    echo "runner_pid: $pid (RUNNING)"
  else
    echo "runner_pid: $pid (NOT RUNNING)"
  fi
else
  echo "runner_pid: (none)"
fi
echo

if [[ -f "$STATUS" ]]; then
  echo "--- campaign-status.json ---"
  # Filter out any accidental metric-like keys just in case
  python3 - <<PY
import json, re
from pathlib import Path
p=Path("$STATUS")
data=json.loads(p.read_text())
banned=re.compile(r"auc|prediction|score|expression|loss|rank", re.I)
safe={k:v for k,v in data.items() if not banned.search(k)}
print(json.dumps(safe, indent=2, sort_keys=True))
PY
else
  echo "status file not found: $STATUS"
fi
echo

if [[ -f "$LEDGER" ]]; then
  echo "--- attempt ledger summary (non-metric) ---"
  python3 - <<PY
import json
from collections import Counter
from pathlib import Path
lines=Path("$LEDGER").read_text().splitlines()
states=Counter(); stages=Counter(); arms=Counter(); retries=0
for line in lines:
    if not line.strip():
        continue
    r=json.loads(line)
    states[r.get('state','?')]+=1
    stages[r.get('stage','?')]+=1
    arms[r.get('arm','?')]+=1
    if r.get('infrastructure_retry_of'):
        retries+=1
print(json.dumps({
  "ledger_records": len(lines),
  "by_state": dict(states),
  "by_stage": dict(stages),
  "by_arm": dict(arms),
  "infrastructure_retry_records": retries,
}, indent=2, sort_keys=True))
PY
else
  echo "ledger not found yet"
fi
echo

echo "--- recent attempt status files (state only) ---"
python3 - <<PY
import json
from pathlib import Path
root=Path("$RUN_ROOT")/"attempts"
rows=[]
if root.exists():
  for p in sorted(root.glob("*/status.json"))[-12:]:
    try:
      s=json.loads(p.read_text())
      rows.append({
        "attempt_id": s.get("attempt_id"),
        "arm": s.get("arm"),
        "stage": s.get("stage"),
        "configuration_id": s.get("configuration_id"),
        "state": s.get("state"),
        "elapsed_seconds": s.get("elapsed_seconds"),
        "timed_out": s.get("timed_out"),
        "error_class": s.get("error_class"),
        "artifact_completeness": s.get("artifact_completeness"),
      })
    except Exception as e:
      rows.append({"path": str(p), "error": type(e).__name__})
print(json.dumps(rows, indent=2))
PY

echo
echo "Monitor command:"
echo "  bash $ACT5_ROOT/control/monitor.sh $ACT5_ROOT"
