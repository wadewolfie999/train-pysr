"""Act 5 scientific-runner network guard.

Denies network socket operations. Allows only local subprocesses required for
Julia/PySR scientific compute and approved local tooling.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(os.environ["SRRES_NETWORK_GUARD_LOG"])
SOCKET_EVENTS = {
    "socket.connect",
    "socket.connect_ex",
    "socket.bind",
    "socket.getaddrinfo",
}

ALLOWED_SUBPROCESS_BASENAMES = {
    "julia",
    "git",  # only for rev-parse HEAD identity checks if needed
}


def log(event: str, detail: object) -> None:
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "detail": str(detail),
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def _basename(argv: object) -> str | None:
    if not isinstance(argv, (list, tuple)) or not argv:
        return None
    first = str(argv[0])
    return Path(first).name


def audit(event: str, args: tuple[object, ...]) -> None:
    if event in SOCKET_EVENTS:
        log("DENIED_NETWORK_EVENT", {"audit_event": event, "args": args})
        raise PermissionError(f"SR-Res Act 5 network guard denied {event}")
    if event == "subprocess.Popen":
        argv = args[1] if len(args) > 1 else None
        base = _basename(argv)
        if base in ALLOWED_SUBPROCESS_BASENAMES:
            # Further constrain git to rev-parse HEAD only.
            if base == "git":
                if not (
                    isinstance(argv, (list, tuple))
                    and list(argv)[1:] == ["rev-parse", "HEAD"]
                ):
                    log("DENIED_SUBPROCESS_EVENT", argv)
                    raise PermissionError(f"Act 5 guard denied subprocess: {argv!r}")
            log("ALLOWED_SUBPROCESS_EVENT", argv)
            return
        # juliacall may invoke the absolute julia path; basename check covers it.
        # Deny everything else, including curl/wget/ssh/python network helpers.
        log("DENIED_SUBPROCESS_EVENT", argv)
        raise PermissionError(f"SR-Res Act 5 network guard denied subprocess: {argv!r}")


sys.addaudithook(audit)
log(
    "NETWORK_GUARD_LOADED",
    {
        "pid": os.getpid(),
        "socket_events_denied": sorted(SOCKET_EVENTS),
        "allowed_subprocess_basenames": sorted(ALLOWED_SUBPROCESS_BASENAMES),
    },
)
