from __future__ import annotations

import argparse
import os
from pathlib import Path

import uvicorn

from systemlens.config import load_config
from systemlens.logging_config import setup_logging


def main() -> None:
    parser = argparse.ArgumentParser(prog="systemlens", description="SystemLens local monitor")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Start SystemLens API + agent")
    run_parser.add_argument("--host", type=str, default=None)
    run_parser.add_argument("--port", type=int, default=None)
    run_parser.add_argument("--interval", type=float, default=None)
    run_parser.add_argument("--ssl-cert", type=str, default=None)
    run_parser.add_argument("--ssl-key", type=str, default=None)

    args = parser.parse_args()
    config = load_config()
    setup_logging(config.log_level)

    if args.command == "run":
        host = args.host or os.getenv("HOST") or config.api_host
        env_port = os.getenv("PORT")
        port = args.port or (int(env_port) if env_port and env_port.isdigit() else config.api_port)
        if args.interval is not None:
            config.sample_interval = args.interval
        if args.ssl_cert:
            config.ssl_cert_path = Path(args.ssl_cert)
        if args.ssl_key:
            config.ssl_key_path = Path(args.ssl_key)

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


if __name__ == "__main__":
    main()
