#!/usr/bin/env bash
# Durable Act 5 campaign launcher. Survives CLI-agent session end.
set -euo pipefail

ACT5_ROOT="${1:-/Users/vaheedgorgeen/SR-Workspace/SR-Res-work/act-05}"
RUN_ID="$(cat "$ACT5_ROOT/runs"/*/run-id.txt 2>/dev/null | tail -n 1)"
if [[ -z "${RUN_ID:-}" ]]; then
  echo "BLOCKED: no run-id.txt under $ACT5_ROOT/runs"
  exit 2
fi
RUN_ROOT="$ACT5_ROOT/runs/$RUN_ID"
PYTHON="$RUN_ROOT/environment/python/bin/python"
CONTROL="$ACT5_ROOT/control"
LOG_DIR="$RUN_ROOT/logs"
mkdir -p "$LOG_DIR" "$RUN_ROOT/progress" "$RUN_ROOT/ledgers"

if [[ ! -x "$PYTHON" ]]; then
  echo "BLOCKED: python missing at $PYTHON"
  exit 2
fi

export PYTHON_JULIAPKG_OFFLINE=yes
export PYTHON_JULIAPKG_EXE="$RUN_ROOT/environment/julia-1.10.3/bin/julia"
export PYTHON_JULIAPKG_PROJECT="$RUN_ROOT/environment/julia-project"
export JULIA_DEPOT_PATH="$RUN_ROOT/environment/julia-depot"
export JULIA_NUM_THREADS=1
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export PYTHON_JULIACALL_HANDLE_SIGNALS=yes
export PYTHON_JULIACALL_THREADS=1
export PYTHONHASHSEED=0
export PYTHONDONTWRITEBYTECODE=1
export PATH="$RUN_ROOT/environment/julia-1.10.3/bin:$PATH"

echo "=== Act 5 preflight (no training) ==="
"$PYTHON" "$CONTROL/validate_preflight.py" \
  --act5-root "$ACT5_ROOT" \
  --run-root "$RUN_ROOT" | tee "$LOG_DIR/preflight.stdout.txt"
PRE_RC=${PIPESTATUS[0]}
if [[ "$PRE_RC" -ne 0 ]]; then
  echo "BLOCKED: preflight failed with code $PRE_RC"
  exit "$PRE_RC"
fi

# Record freeze of control sources
"$PYTHON" - <<PY
from pathlib import Path
import sys
sys.path.insert(0, "$CONTROL")
from campaign_runner import CampaignPaths, freeze_control_hashes
from lib.hashutil import dump_json
from datetime import datetime, timezone
paths = CampaignPaths(Path("$ACT5_ROOT"), Path("$RUN_ROOT"))
freeze_control_hashes(paths)
dump_json(paths.evidence / "02-support-code" / "FROZEN.json", {
  "frozen_utc": datetime.now(timezone.utc).isoformat(),
  "note": "Control sources frozen before claim-bearing fits",
})
print("control frozen")
PY

if [[ -f "$RUN_ROOT/campaign.pid" ]]; then
  old="$(cat "$RUN_ROOT/campaign.pid")"
  if ps -p "$old" >/dev/null 2>&1; then
    echo "Campaign already running with pid $old"
    exit 0
  fi
fi

echo "=== Launching durable campaign runner ==="
# Scientific runner network isolation is enforced inside worker processes via
# network_guard sitecustomize. Scheduler itself stays local-only.
nohup "$PYTHON" "$CONTROL/campaign_runner.py" \
  --act5-root "$ACT5_ROOT" \
  --run-root "$RUN_ROOT" \
  --max-concurrent 2 \
  >"$LOG_DIR/campaign.stdout.txt" \
  2>"$LOG_DIR/campaign.stderr.txt" &
echo $! >"$RUN_ROOT/campaign.pid"
sleep 1
if ps -p "$(cat "$RUN_ROOT/campaign.pid")" >/dev/null 2>&1; then
  echo "LAUNCHED pid=$(cat "$RUN_ROOT/campaign.pid")"
  echo "Monitor: bash $CONTROL/monitor.sh $ACT5_ROOT"
  echo "Logs: $LOG_DIR/campaign.stdout.txt"
  exit 0
else
  echo "BLOCKED: runner failed to stay up; see $LOG_DIR/campaign.stderr.txt"
  exit 2
fi
