#!/usr/bin/env python3
"""Watch a file for a specific string and exit when found.

Usage:
  python .claude/watch-for.py <file_path> <search_string> [--timeout <seconds>]

Examples:
  python .claude/watch-for.py .claude/workspaces/INIT-016/findings.txt EXPLORATION_COMPLETE
  python .claude/watch-for.py .claude/workspaces/INIT-016/findings.txt EXPLORATION_COMPLETE --timeout 300

Polls every 3 seconds. Prints file content when match found.
Exits with code 0 on match, 1 on timeout, 2 on error.
"""

import sys
import os
import time
import argparse

def main():
    parser = argparse.ArgumentParser(description="Watch file for string")
    parser.add_argument("file_path", help="File to watch")
    parser.add_argument("search_string", help="String to look for")
    parser.add_argument("--timeout", type=int, default=600, help="Timeout in seconds (default 600)")
    parser.add_argument("--tail", type=int, default=0, help="Only print last N lines on match (0 = all)")
    parser.add_argument("--quiet", action="store_true", help="Only print FOUND/TIMEOUT, not file content")
    args = parser.parse_args()

    start = time.time()
    checks = 0

    while True:
        elapsed = time.time() - start
        if elapsed > args.timeout:
            print(f"TIMEOUT after {args.timeout}s watching {args.file_path} for '{args.search_string}'")
            sys.exit(1)

        if os.path.exists(args.file_path):
            try:
                with open(args.file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                if args.search_string in content:
                    if args.quiet:
                        print(f"FOUND '{args.search_string}' in {args.file_path} after {elapsed:.0f}s")
                    else:
                        print(f"FOUND '{args.search_string}' after {elapsed:.0f}s in {args.file_path}")
                        if args.tail > 0:
                            lines = content.strip().split('\n')
                            print('\n'.join(lines[-args.tail:]))
                    sys.stdout.flush()
                    os._exit(0)
            except Exception:
                pass

        checks += 1
        if checks % 10 == 0:
            print(f"  ... waiting ({elapsed:.0f}s elapsed, file {'exists' if os.path.exists(args.file_path) else 'not found'})")

        time.sleep(3)

if __name__ == "__main__":
    main()
