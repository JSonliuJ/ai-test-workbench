"""CLI entry point for record"""
import argparse
import asyncio
import json
import os
import sys

def get_dated_output_dir(base_output: str) -> str:
    """Get output directory named by date and sequence number.

    Creates directories like: ./api-docs/2026-05-05-001, ./api-docs/2026-05-05-002, etc.
    """
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    base_path = os.path.abspath(base_output)

    # Find existing directories for today
    existing = []
    if os.path.isdir(base_path):
        for name in os.listdir(base_path):
            if name.startswith(today + "-"):
                try:
                    seq = int(name.split("-")[-1])
                    existing.append(seq)
                except ValueError:
                    pass

    # Determine next sequence number
    next_seq = max(existing) + 1 if existing else 1

    # Create new directory with zero-padded sequence
    output_dir = os.path.join(base_path, f"{today}-{next_seq:03d}")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def main():
    parser = argparse.ArgumentParser(prog="record")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # record command
    record_parser = subparsers.add_parser("record", help="Record HTTP requests from a URL")
    record_parser.add_argument("url", help="Target URL to record")
    record_parser.add_argument(
        "--output", "-o",
        default="./AI-接口采集",
        help="Base output directory for documentation (default: ./AI-接口采集)"
    )
    record_parser.add_argument(
        "--include-static",
        action="store_true",
        default=False,
        help="Include static resources (JS, CSS, images, etc.) in the recording. Default: filter them out"
    )
    record_parser.add_argument(
        "--exclude-pattern",
        action="append",
        dest="exclude_patterns",
        help="Additional URL patterns to exclude (can be used multiple times)"
    )
    record_parser.add_argument(
        "--cdp-port",
        type=int,
        default=9222,
        help="CDP debugging port (default: 9222)"
    )

    args = parser.parse_args()

    if args.command == "record":
        from .recorder.browser import BrowserRecorder

        # Use base output directory directly, BrowserRecorder will create batch_id subdirectory
        output_dir = os.path.abspath(args.output)
        print(f"Output directory: {output_dir}")

        # Run recording
        print(f"Starting recording for: {args.url}")
        print("Click the PCR button in the browser to stop recording...")

        recorder = BrowserRecorder(args.url, filter_static=not args.include_static, exclude_patterns=args.exclude_patterns, output_dir=output_dir)

        async def run():
            await recorder.start(cdp_port=args.cdp_port)
            while recorder.browser:
                await asyncio.sleep(0.5)

        try:
            asyncio.run(run())
        except KeyboardInterrupt:
            print("\nRecording interrupted by user")

        # Save any remaining recording (user might have clicked REC but not STP)
        count, idx = recorder.save_current_recording()
        if count > 0:
            print(f"Saved {count} remaining requests to raw{idx:02d}.json")
        elif recorder._record_count > 0:
            print(f"\nTotal recordings: {recorder._record_count}")

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
