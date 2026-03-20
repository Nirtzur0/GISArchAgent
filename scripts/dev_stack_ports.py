#!/usr/bin/env python3
"""Resolve a usable local port for the dev stack."""

from __future__ import annotations

import argparse
import socket


def is_port_available(host: str, port: int) -> bool:
    """Return True when the host/port can be bound by a new process."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def resolve_port(host: str, requested_port: int) -> int:
    """Resolve the requested port to the next free local port if needed."""
    candidate = requested_port
    while not is_port_available(host, candidate):
        candidate += 1
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True, type=int)
    args = parser.parse_args()
    print(resolve_port(args.host, args.port))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
