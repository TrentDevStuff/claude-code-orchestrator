"""Service lifecycle management commands"""

import typer
import subprocess
import os
import signal
import time
import psutil
from pathlib import Path
from typing import Optional
from rich.console import Console

from ..config import config_manager
from ..utils import (
    print_success,
    print_error,
    print_warning,
    print_info,
    print_section,
    format_duration,
    create_status_table,
)

app = typer.Typer(help="Service lifecycle management")
console = Console()

PID_FILE = Path.home() / ".claude-api" / "service.pid"


def get_service_pid() -> Optional[int]:
    """Get running service PID from file"""
    if not PID_FILE.exists():
        return None

    try:
        pid = int(PID_FILE.read_text().strip())
        # Check if process is actually running
        if psutil.pid_exists(pid):
            return pid
        else:
            # Clean up stale PID file
            PID_FILE.unlink()
            return None
    except:
        return None


def save_service_pid(pid: int):
    """Save service PID to file"""
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(pid))


def remove_service_pid():
    """Remove PID file"""
    if PID_FILE.exists():
        PID_FILE.unlink()


@app.command()
def start(
    port: Optional[int] = typer.Option(None, help="Override port"),
    background: bool = typer.Option(False, "--background", "-b", help="Run in background"),
    no_deps_check: bool = typer.Option(False, help="Skip dependency checks"),
    logs: bool = typer.Option(False, "--logs", "-l", help="Tail logs after starting"),
):
    """Start the API service"""

    try:
        config = config_manager.load()
        service_dir = config.service.directory
        service_port = port or config.service.port

        # Check if already running
        pid = get_service_pid()
        if pid:
            print_warning(f"Service already running (PID: {pid})")
            print_info(f"Service URL: http://localhost:{service_port}")
            return

        # Dependency checks
        if not no_deps_check:
            print_info("Checking dependencies...")

            # Check Redis
            try:
                import redis
                r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=2)
                r.ping()
                print_success("Redis: running")
            except:
                print_warning("Redis: not running (optional for basic usage)")

            # Check Claude CLI
            try:
                subprocess.run(
                    ["claude", "--version"],
                    capture_output=True,
                    check=True,
                    timeout=5
                )
                print_success("Claude CLI: installed")
            except:
                print_error("Claude CLI: not found", "Install from: https://docs.anthropic.com/en/docs/claude-code")
                raise typer.Exit(1)

            # Check agents/skills
            agents_dir = Path.home() / ".claude" / "agents"
            skills_dir = Path.home() / ".claude" / "skills"

            if agents_dir.exists():
                agent_count = len(list(agents_dir.glob("*.md")))
                print_success(f"Agents: {agent_count} discovered")
            else:
                print_warning("Agents directory not found")

            if skills_dir.exists():
                skill_count = len(list(skills_dir.glob("*/skill.json")))
                print_success(f"Skills: {skill_count} discovered")
            else:
                print_warning("Skills directory not found")

        # Check port availability
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', service_port))
        sock.close()

        if result == 0:
            print_error(f"Port {service_port} already in use")
            raise typer.Exit(1)

        print_success(f"Port {service_port} available")

        # Start service
        print_info(f"Starting Claude Code API Service on port {service_port}...")

        cmd = ["python", str(service_dir / "main.py")]
        env = os.environ.copy()
        env["PORT"] = str(service_port)

        if background:
            # Start in background
            process = subprocess.Popen(
                cmd,
                cwd=service_dir,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )

            # Wait a moment for startup
            time.sleep(2)

            # Check if it started
            if process.poll() is None:
                save_service_pid(process.pid)
                print_success(f"Service started (PID: {process.pid})")
                print_success(f"Service URL: http://localhost:{service_port}")
                print_success(f"API Docs: http://localhost:{service_port}/docs")

                if logs:
                    print_info("Tailing logs... (Ctrl+C to stop)")
                    _tail_logs(follow=True)
            else:
                print_error("Service failed to start")
                raise typer.Exit(1)

        else:
            # Run in foreground
            print_info("Service running in foreground (Ctrl+C to stop)")
            try:
                subprocess.run(cmd, cwd=service_dir, env=env)
            except KeyboardInterrupt:
                print_info("\nStopping service...")
                remove_service_pid()

    except Exception as e:
        print_error(f"Failed to start service: {str(e)}")
        raise typer.Exit(1)


@app.command()
def stop(
    force: bool = typer.Option(False, "--force", "-f", help="Force kill if graceful shutdown fails"),
    timeout: int = typer.Option(30, help="Shutdown timeout in seconds"),
):
    """Stop the running service"""

    try:
        pid = get_service_pid()

        if not pid:
            print_warning("Service is not running")
            return

        print_success(f"Found service (PID: {pid})")

        try:
            process = psutil.Process(pid)

            # Try graceful shutdown first
            print_info("Sending shutdown signal...")
            process.terminate()

            # Wait for process to exit
            print_info(f"Waiting for graceful shutdown (timeout: {timeout}s)...")
            process.wait(timeout=timeout)

            print_success("Service stopped successfully")
            remove_service_pid()

        except psutil.TimeoutExpired:
            if force:
                print_warning("Graceful shutdown timed out, force killing...")
                process.kill()
                process.wait(timeout=5)
                print_success("Service force-killed")
                remove_service_pid()
            else:
                print_error(
                    "Graceful shutdown timed out",
                    "Use --force to force kill"
                )
                raise typer.Exit(1)

        except psutil.NoSuchProcess:
            print_warning("Process already stopped")
            remove_service_pid()

    except Exception as e:
        print_error(f"Failed to stop service: {str(e)}")
        raise typer.Exit(1)


@app.command()
def restart(
    port: Optional[int] = typer.Option(None, help="Override port"),
):
    """Restart the service"""
    print_info("Restarting service...")

    # Stop if running
    pid = get_service_pid()
    if pid:
        stop.callback(force=False, timeout=30)
        time.sleep(2)

    # Start
    start.callback(port=port, background=True, no_deps_check=True, logs=False)


@app.command()
def status(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Check service status"""

    try:
        from ..api_client import APIClient

        config = config_manager.load()
        client = APIClient()

        pid = get_service_pid()
        running = pid is not None

        if not running:
            print_error("Service is not running", "Start with: claude-api service start")
            raise typer.Exit(1)

        # Get process info
        process = psutil.Process(pid)
        uptime = time.time() - process.create_time()

        # Get service health
        try:
            health = client.get_health()
        except:
            health = None

        # Build status table
        items = [
            ("Running", "✓ Yes"),
            ("PID", str(pid)),
            ("Port", str(config.service.port)),
            ("Uptime", format_duration(uptime)),
            ("Memory", f"{process.memory_info().rss / 1024 / 1024:.1f} MB"),
            ("CPU", f"{process.cpu_percent(interval=0.1):.1f}%"),
        ]

        if health:
            items.append(("Health", "✓ OK"))
        else:
            items.append(("Health", "✗ Not responding"))

        table = create_status_table("Service Status", items)
        console.print(table)

        # Dependencies
        print()
        dep_items = []

        # Check Redis
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=1)
            r.ping()
            dep_items.append(("Redis", "✓ Running (port 6379)"))
        except:
            dep_items.append(("Redis", "✗ Not running"))

        # Check agents/skills
        agents_dir = Path.home() / ".claude" / "agents"
        skills_dir = Path.home() / ".claude" / "skills"

        if agents_dir.exists():
            agent_count = len(list(agents_dir.glob("*.md")))
            dep_items.append(("Agents", f"✓ {agent_count} discovered"))
        else:
            dep_items.append(("Agents", "✗ Directory not found"))

        if skills_dir.exists():
            skill_count = len(list(skills_dir.glob("*/skill.json")))
            dep_items.append(("Skills", f"✓ {skill_count} discovered"))
        else:
            dep_items.append(("Skills", "✗ Directory not found"))

        dep_table = create_status_table("Dependencies", dep_items)
        console.print(dep_table)

    except Exception as e:
        print_error(f"Failed to get status: {str(e)}")
        raise typer.Exit(1)


def _tail_logs(lines: int = 50, follow: bool = False, level: Optional[str] = None, search: Optional[str] = None):
    """Internal log tailing function"""
    # For now, just tail the output
    # In future, could tail from log files
    print_warning("Log tailing from files not yet implemented")
    print_info("Run service in foreground to see logs: claude-api service start")


@app.command()
def logs(
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines to show"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow logs (tail -f style)"),
    level: Optional[str] = typer.Option(None, help="Filter by level (DEBUG, INFO, WARNING, ERROR)"),
    search: Optional[str] = typer.Option(None, help="Search for pattern"),
):
    """Tail service logs"""
    _tail_logs(lines=lines, follow=follow, level=level, search=search)
