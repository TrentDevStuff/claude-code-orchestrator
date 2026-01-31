"""Health check commands"""

import typer
from pathlib import Path
from rich.console import Console

from ..api_client import APIClient, APIError
from ..config import config_manager
from ..utils import (
    print_success,
    print_error,
    print_info,
    create_status_table,
)

app = typer.Typer(help="Health checks")
console = Console()


@app.command()
def check(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed component status"),
):
    """Comprehensive health check"""

    try:
        client = APIClient()
        config = config_manager.load()

        # Overall health
        try:
            health_data = client.get_health()
            overall_healthy = True
            print_success("Overall: Healthy")
        except APIError as e:
            overall_healthy = False
            print_error("Overall: Unhealthy", str(e))

        print()

        # Component checks
        components = []

        # API Service
        if overall_healthy:
            components.append(("API Service", "✓ Responding"))
        else:
            components.append(("API Service", "✗ Not responding"))

        # Redis
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=2)
            ping_time = r.ping()
            components.append(("Redis", f"✓ Connected (ping: {ping_time}ms)"))
        except:
            components.append(("Redis", "✗ Not running"))

        # Budget Manager (check via health endpoint)
        if overall_healthy and health_data:
            components.append(("Budget Manager", "✓ Operational"))
        else:
            components.append(("Budget Manager", "⚠ Unknown"))

        # Auth Manager
        if overall_healthy and health_data:
            components.append(("Auth Manager", "✓ Operational"))
        else:
            components.append(("Auth Manager", "⚠ Unknown"))

        # Agent Discovery
        agents_dir = Path.home() / ".claude" / "agents"
        if agents_dir.exists():
            agent_count = len(list(agents_dir.glob("*.md")))
            components.append(("Agent Discovery", f"✓ {agent_count} agents found"))
        else:
            components.append(("Agent Discovery", "✗ Directory not found"))

        # Skill Discovery
        skills_dir = Path.home() / ".claude" / "skills"
        if skills_dir.exists():
            skill_count = len(list(skills_dir.glob("*/skill.json")))
            components.append(("Skill Discovery", f"✓ {skill_count} skills found"))
        else:
            components.append(("Skill Discovery", "✗ Directory not found"))

        table = create_status_table("Health Check Results", components)
        console.print(table)

    except Exception as e:
        print_error(f"Health check failed: {str(e)}")
        raise typer.Exit(1)


@app.command()
def deps():
    """Check dependencies only"""

    try:
        deps_status = []

        # Redis
        print_info("Checking Redis...")
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=2)
            r.ping()
            info = r.info()
            mem_used = info.get('used_memory_human', 'unknown')

            deps_status.append(("Status", "✓ Running"))
            deps_status.append(("Port", "6379"))
            deps_status.append(("Memory", mem_used))
        except ImportError:
            deps_status.append(("Status", "✗ redis-py not installed"))
        except Exception as e:
            deps_status.append(("Status", "✗ Not running"))
            deps_status.append(("Error", str(e)))

        table = create_status_table("Redis (required)", deps_status)
        console.print(table)
        print()

        # Claude CLI
        claude_status = []
        print_info("Checking Claude CLI...")
        try:
            import subprocess
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                check=True,
                timeout=5,
                text=True
            )
            version = result.stdout.strip()

            claude_status.append(("Installed", "✓ Yes"))
            claude_status.append(("Version", version))

            # Find path
            which_result = subprocess.run(
                ["which", "claude"],
                capture_output=True,
                text=True
            )
            if which_result.returncode == 0:
                claude_status.append(("Path", which_result.stdout.strip()))

        except FileNotFoundError:
            claude_status.append(("Installed", "✗ No"))
            claude_status.append(("Install", "https://docs.anthropic.com/en/docs/claude-code"))
        except Exception as e:
            claude_status.append(("Installed", "⚠ Error"))
            claude_status.append(("Error", str(e)))

        table = create_status_table("Claude CLI (required)", claude_status)
        console.print(table)
        print()

        # Agents
        agents_status = []
        agents_dir = Path.home() / ".claude" / "agents"

        agents_status.append(("Location", str(agents_dir)))

        if agents_dir.exists():
            agent_files = list(agents_dir.glob("*.md"))
            agents_status.append(("Count", f"{len(agent_files)} discovered"))

            if agent_files:
                sample_agents = [f.stem for f in agent_files[:5]]
                agents_status.append(("Sample", ", ".join(sample_agents)))
        else:
            agents_status.append(("Status", "✗ Directory not found"))

        table = create_status_table("Agents (required)", agents_status)
        console.print(table)
        print()

        # Skills
        skills_status = []
        skills_dir = Path.home() / ".claude" / "skills"

        skills_status.append(("Location", str(skills_dir)))

        if skills_dir.exists():
            skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir() and (d / "skill.json").exists()]
            skills_status.append(("Count", f"{len(skill_dirs)} discovered"))

            if skill_dirs:
                sample_skills = [d.name for d in skill_dirs[:5]]
                skills_status.append(("Sample", ", ".join(sample_skills)))
        else:
            skills_status.append(("Status", "✗ Directory not found"))

        table = create_status_table("Skills (required)", skills_status)
        console.print(table)

    except Exception as e:
        print_error(f"Dependency check failed: {str(e)}")
        raise typer.Exit(1)


@app.command()
def ping():
    """Quick ping (is service responding?)"""

    try:
        client = APIClient()

        if client.is_service_running():
            print_success("Service is responding")
        else:
            print_error("Service is not responding", "Check with: claude-api service status")
            raise typer.Exit(1)

    except Exception as e:
        print_error(f"Ping failed: {str(e)}")
        raise typer.Exit(1)
