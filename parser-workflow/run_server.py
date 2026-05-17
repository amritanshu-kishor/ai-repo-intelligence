"""Start the API on a port that is free on this machine (Windows-safe)."""

from __future__ import annotations

import socket
import sys

import uvicorn

from config import API_HOST, API_PORT


def port_is_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def find_free_port(host: str, start_port: int, max_attempts: int = 50) -> int:
    for port in range(start_port, start_port + max_attempts):
        if port_is_free(host, port):
            return port
    raise RuntimeError(f"No free TCP port found in range {start_port}-{start_port + max_attempts - 1}")


def main() -> None:
    host = API_HOST
    port = API_PORT

    if not port_is_free(host, port):
        fallback = find_free_port(host, port + 1)
        print(
            f"Port {port} is busy or blocked on {host}. Using {fallback} instead.",
            file=sys.stderr,
        )
        port = fallback

    docs = f"http://{host}:{port}/docs"
    print(f"Starting API at http://{host}:{port}")
    print(f"Swagger UI: {docs}")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
    )


if __name__ == "__main__":
    main()
