"""Launch claude interactively with the orchestrator system prompt.

Windows cmd.exe has an ~8192 character limit for command arguments,
but master-prompt.md is ~31KB. This helper reads the file and passes
it via subprocess, bypassing the shell argument length limit.
"""
import subprocess
import sys
import os


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_file = os.path.join(script_dir, "master-prompt.md")

    with open(prompt_file, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    args = ["claude", "--system-prompt", system_prompt]

    # Model (required first arg)
    if len(sys.argv) > 1 and sys.argv[1]:
        args.extend(["--model", sys.argv[1]])

    # Permission flags (optional remaining args)
    for arg in sys.argv[2:]:
        if arg:
            args.append(arg)

    sys.exit(subprocess.call(args))


if __name__ == "__main__":
    main()
