from __future__ import annotations

import argparse
import asyncio
import os
import socket
import threading
import time
from pathlib import Path

import uvicorn

from systemlens.config import load_config
from systemlens.logging_config import setup_logging


def _pick_port(host: str, preferred_port: int) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, preferred_port))
        except OSError:
            sock.bind((host, 0))
        return sock.getsockname()[1]


def _serve_in_thread(host: str, port: int, ssl_cert: Path | None, ssl_key: Path | None) -> tuple[threading.Thread, uvicorn.Server]:
    config = uvicorn.Config(
        "systemlens.api.app:app",
        host=host,
        port=port,
        reload=False,
        ssl_certfile=str(ssl_cert) if ssl_cert else None,
        ssl_keyfile=str(ssl_key) if ssl_key else None,
        log_level="info",
    )
    server = uvicorn.Server(config)

    def run_server() -> None:
        asyncio.run(server.serve())

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    return thread, server


def _run_desktop(config: object, host: str, port: int) -> None:
    try:
        import webview
    except ImportError as exc:
        raise RuntimeError("pywebview is required for desktop mode. Install the desktop dependencies and try again.") from exc

    ssl_cert = Path(config.ssl_cert_path) if getattr(config, "ssl_cert_path", None) else None
    ssl_key = Path(config.ssl_key_path) if getattr(config, "ssl_key_path", None) else None
    actual_port = _pick_port(host, port)
    scheme = "https" if ssl_cert and ssl_key else "http"
    _thread, server = _serve_in_thread(host, actual_port, ssl_cert, ssl_key)
    url_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    url = f"{scheme}://{url_host}:{actual_port}"

    # Wait for the local API to become reachable before showing the window.
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)

    webview.create_window("SystemLens", url, width=1400, height=920, min_size=(1024, 720), confirm_close=True)
    webview.start(debug=False)


def main() -> None:
    parser = argparse.ArgumentParser(prog="systemlens", description="SystemLens local monitor")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Start SystemLens API + agent")
    run_parser.add_argument("--host", type=str, default=None)
    run_parser.add_argument("--port", type=int, default=None)
    run_parser.add_argument("--interval", type=float, default=None)
    run_parser.add_argument("--ssl-cert", type=str, default=None)
    run_parser.add_argument("--ssl-key", type=str, default=None)

    desktop_parser = subparsers.add_parser("desktop", help="Start SystemLens as a native desktop app")
    desktop_parser.add_argument("--host", type=str, default=None)
    desktop_parser.add_argument("--port", type=int, default=None)
    desktop_parser.add_argument("--interval", type=float, default=None)
    desktop_parser.add_argument("--ssl-cert", type=str, default=None)
    desktop_parser.add_argument("--ssl-key", type=str, default=None)

    parser.set_defaults(command="desktop")

    args = parser.parse_args()
    config = load_config()
    setup_logging(config.log_level)

    selected_command = args.command or "desktop"
    host = getattr(args, "host", None) or os.getenv("HOST") or config.api_host
    env_port = os.getenv("PORT")
    port = getattr(args, "port", None) or (int(env_port) if env_port and env_port.isdigit() else config.api_port)
    if getattr(args, "interval", None) is not None:
        config.sample_interval = args.interval
    if getattr(args, "ssl_cert", None):
        config.ssl_cert_path = Path(args.ssl_cert)
    if getattr(args, "ssl_key", None):
        config.ssl_key_path = Path(args.ssl_key)

    if selected_command == "run":
        scheme = "https" if config.ssl_cert_path and config.ssl_key_path else "http"
        print(f"SystemLens running at {scheme}://{host}:{port}")
        print("Press CTRL+C to stop")
        ssl_cert = Path(config.ssl_cert_path) if config.ssl_cert_path else None
        ssl_key = Path(config.ssl_key_path) if config.ssl_key_path else None
        uvicorn.run(
            "systemlens.api.app:app",
            host=host,
            port=port,
            reload=False,
            ssl_certfile=str(ssl_cert) if ssl_cert else None,
            ssl_keyfile=str(ssl_key) if ssl_key else None,
        )
    elif selected_command == "desktop":
        print("Starting SystemLens desktop app...")
        _run_desktop(config, host, port)


if __name__ == "__main__":
    main()
