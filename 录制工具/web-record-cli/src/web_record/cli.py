"""CLI entry point for record."""

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from .debug import set_debug, debug, info, warn, error, step


def _load_env_files(output: str = ".") -> list[str]:
    candidates = [
        Path.cwd() / ".env",
        Path(output).expanduser() / ".env",
    ]
    loaded: list[str] = []
    seen: set[Path] = set()

    for candidate in candidates:
        path = candidate.resolve()
        if path in seen:
            continue
        seen.add(path)
        if path.is_file():
            load_dotenv(dotenv_path=path, override=False)
            loaded.append(str(path))

    return loaded


def main():
    parser = argparse.ArgumentParser(prog="record")
    subparsers = parser.add_subparsers(dest="command", required=True)

    record_parser = subparsers.add_parser("record", help="Record HTTP requests from a URL")
    record_parser.add_argument("url", help="Target URL to record")
    record_parser.add_argument(
        "--output",
        "-o",
        default=".",
        help="Root output directory (default: current directory)",
    )
    record_parser.add_argument(
        "--cdp-port",
        type=int,
        default=9222,
        help="CDP debugging port (default: 9222)",
    )
    record_parser.add_argument(
        "--enable-vision",
        action="store_true",
        default=False,
        help="Enable multimodal AI screenshot analysis (requires WEB_VISION_API_KEY + WEB_VISION_BASE_URL + WEB_VISION_MODEL env vars)",
    )
    record_parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Enable detailed debug output",
    )

    args = parser.parse_args()

    set_debug(args.debug)

    if args.command == "record":
        from .recorder.browser import BrowserRecorder

        output_dir = os.path.abspath(args.output)
        os.makedirs(output_dir, exist_ok=True)
        loaded_env_files = _load_env_files(output_dir)
        if loaded_env_files:
            debug(f".env loaded: {', '.join(loaded_env_files)}")
        else:
            debug(".env not found in current/output directory")
        info(f"Output directory: {output_dir}")

        info(f"Starting recording for: {args.url}")
        step("Click the PCR button in the browser to stop recording...")

        vision_api_key = None
        vision_base_url = None
        vision_model = os.environ.get("WEB_VISION_MODEL", "qwen3.6-flash-2026-04-16")
        if args.enable_vision:
            vision_api_key = os.environ.get("WEB_VISION_API_KEY")
            vision_base_url = os.environ.get("WEB_VISION_BASE_URL")
            debug(f"WEB_VISION_API_KEY={vision_api_key}")
            debug(f"WEB_VISION_BASE_URL={vision_base_url}")
            debug(f"WEB_VISION_MODEL={vision_model}")
            debug(
                f"WEB_VISION_API_KEY={'已设置' if vision_api_key else '未设置'}, "
                f"WEB_VISION_BASE_URL={'已设置' if vision_base_url else '未设置'}"
            )
            if not vision_api_key or not vision_base_url:
                warn("--enable-vision set but WEB_VISION_API_KEY or WEB_VISION_BASE_URL not found in env")
                warn("Vision analysis disabled")
            else:
                info(f"Vision analysis enabled with model: {vision_model}")

        recorder = BrowserRecorder(
            args.url,
            output_dir=output_dir,
            vision_api_key=vision_api_key,
            vision_base_url=vision_base_url,
            vision_model=vision_model,
        )

        async def run():
            await recorder.start(cdp_port=args.cdp_port)
            while recorder.browser:
                await asyncio.sleep(0.5)

        try:
            asyncio.run(run())
        except KeyboardInterrupt:
            info("Recording interrupted by user")

        count, idx = recorder.save_current_recording()
        if count > 0:
            info(f"Saved {count} remaining requests to raw{idx:02d}.json")
        elif recorder._record_count > 0:
            info(f"Total recordings: {recorder._record_count}")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
