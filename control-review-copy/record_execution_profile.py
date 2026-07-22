#!/usr/bin/env python3
"""Record Act 5 A4 execution profile before model execution."""

from __future__ import annotations

import json
import os
import platform
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    act5 = Path(sys.argv[1]).resolve()
    run = Path(sys.argv[2]).resolve()
    out = run / "evidence" / "00-authority-and-profile"
    out.mkdir(parents=True, exist_ok=True)

    # Network state: best-effort, no scientific dependency
    network_state = "UNKNOWN"
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1)
        # Does not send packets to 8.8.8.8 for connect on UDP; just route resolution-ish
        sock.connect(("8.8.8.8", 80))
        network_state = f"ROUTE_OK local={sock.getsockname()[0]}"
        sock.close()
    except Exception as exc:  # noqa: BLE001
        network_state = f"NO_ROUTE_OR_BLOCKED: {type(exc).__name__}"

    try:
        grok_ver = subprocess.check_output(["grok", "--version"], text=True).strip()
    except Exception:  # noqa: BLE001
        grok_ver = "UNKNOWN"

    repo = run / "train-pysr"
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
        porcelain = subprocess.check_output(["git", "status", "--porcelain"], cwd=repo, text=True)
        clean = porcelain.strip() == ""
    except Exception as exc:  # noqa: BLE001
        commit = f"ERROR: {exc}"
        clean = False

    profile = {
        "execution_profile": {
            "actor": "A4",
            "cli_agent": "Grok Build",
            "model_display_name": "Grok 4.5",
            "cli_version": grok_ver,
            "provider": "xAI",
            "agent_mode": "interactive_CLI_workspace_bounded",
            "reasoning_setting": "NOT_EXPOSED",
            "permission_mode": "WORKSPACE_BOUNDED",
            "collaboration_mode": "NOT_EXPOSED",
            "workspace_root": str(act5),
            "repository_path": str(repo),
            "repository_commit": commit,
            "repository_worktree_clean": clean,
            "scientific_compute": "LOCAL_ONLY",
            "remote_scientific_compute": "PROHIBITED",
            "session_started_at": datetime.now(timezone.utc).isoformat(),
            "session_ended_at": None,
            "operating_system": platform.platform(),
            "architecture": platform.machine(),
            "cpu_brand": subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
            if platform.system() == "Darwin"
            else platform.processor(),
            "cpu_count": os.cpu_count(),
            "network_state": network_state,
            "handoff_id": "SRRES-A5-A4-UNIVERSAL-HANDOFF-0.1.0",
            "scientific_act": 5,
            "protocol_id": "SRRES-VP-1.0.0",
        }
    }
    path = out / "execution-profile.json"
    path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(profile, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
