# Orchestrator Tools — Reusable PowerShell commands for Claude Code orchestrator
# Usage from Git Bash: powershell -ExecutionPolicy Bypass -File .claude/orch-tools.ps1 <command> [args...]

param(
    [Parameter(Position=0)]
    [string]$Command,

    [Parameter(Position=1, ValueFromRemainingArguments=$true)]
    [string[]]$ExtraArgs
)

$ProjectDir = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$ClaudeDir = Join-Path $ProjectDir ".claude"

function JoinPaths {
    param([string[]]$Parts)
    $result = $Parts[0]
    for ($i = 1; $i -lt $Parts.Count; $i++) {
        $result = Join-Path $result $Parts[$i]
    }
    return $result
}

switch ($Command) {
    "daemon-status" {
        $pidFile = Join-Path $ClaudeDir ".daemon-pid"
        if (Test-Path $pidFile) {
            $daemonPid = (Get-Content $pidFile -Raw).Trim()
            try {
                $proc = Get-Process -Id $daemonPid -ErrorAction Stop
                Write-Output "DAEMON_RUNNING pid=$daemonPid name=$($proc.ProcessName) start=$($proc.StartTime)"
            } catch {
                Write-Output "DAEMON_DEAD pid=$daemonPid"
            }
        } else {
            Write-Output "DAEMON_NO_PID"
        }
    }

    "daemon-log" {
        $logFile = Join-Path $ClaudeDir ".daemon.log"
        $lines = if ($ExtraArgs.Count -gt 0) { [int]$ExtraArgs[0] } else { 30 }
        if (Test-Path $logFile) {
            Get-Content $logFile -Tail $lines -Encoding UTF8
        } else {
            Write-Output "NO_LOG_FILE"
        }
    }

    "daemon-start" {
        $daemonScript = Join-Path $ClaudeDir "worker-daemon.py"
        $logFile = Join-Path $ClaudeDir ".daemon.log"
        # Kill existing daemon first
        $pidFile = Join-Path $ClaudeDir ".daemon-pid"
        if (Test-Path $pidFile) {
            $oldPid = (Get-Content $pidFile -Raw).Trim()
            try { Stop-Process -Id $oldPid -Force -ErrorAction SilentlyContinue } catch {}
            Start-Sleep -Seconds 1
        }
        # Start new daemon with unbuffered output
        $proc = Start-Process -FilePath "python" -ArgumentList "-u", $daemonScript `
            -RedirectStandardOutput $logFile -RedirectStandardError "$logFile.err" `
            -PassThru -WindowStyle Hidden
        Write-Output "DAEMON_STARTED pid=$($proc.Id)"
    }

    "daemon-stop" {
        $pidFile = Join-Path $ClaudeDir ".daemon-pid"
        if (Test-Path $pidFile) {
            $daemonPid = (Get-Content $pidFile -Raw).Trim()
            try {
                Stop-Process -Id $daemonPid -Force -ErrorAction Stop
                Write-Output "DAEMON_STOPPED pid=$daemonPid"
            } catch {
                Write-Output "DAEMON_ALREADY_DEAD pid=$daemonPid"
            }
        } else {
            Write-Output "DAEMON_NO_PID"
        }
    }

    "daemon-restart" {
        & $PSCommandPath "daemon-stop"
        Start-Sleep -Seconds 2
        & $PSCommandPath "daemon-start"
    }

    "list-python" {
        Get-Process -Name python* -ErrorAction SilentlyContinue |
            Select-Object Id, ProcessName, StartTime |
            Format-Table -AutoSize | Out-String
    }

    "kill-pid" {
        if ($ExtraArgs.Count -gt 0) {
            $targetPid = $ExtraArgs[0]
            try {
                Stop-Process -Id $targetPid -Force -ErrorAction Stop
                Write-Output "KILLED pid=$targetPid"
            } catch {
                Write-Output "KILL_FAILED pid=$targetPid error=$($_.Exception.Message)"
            }
        } else {
            Write-Output "USAGE: kill-pid <pid>"
        }
    }

    "check-worker" {
        if ($ExtraArgs.Count -gt 0) {
            $initId = $ExtraArgs[0]
            $pidsDir = JoinPaths @($ClaudeDir, "workspaces", $initId, "pids")
            if (Test-Path $pidsDir) {
                Get-ChildItem $pidsDir -Filter "*.pid" | ForEach-Object {
                    $workerPid = (Get-Content $_.FullName -Raw).Trim()
                    $workerType = $_.BaseName
                    try {
                        $proc = Get-Process -Id $workerPid -ErrorAction Stop
                        Write-Output "WORKER_RUNNING type=$workerType pid=$workerPid"
                    } catch {
                        Write-Output "WORKER_DEAD type=$workerType pid=$workerPid"
                    }
                }
            } else {
                Write-Output "NO_PIDS_DIR init=$initId"
            }
        } else {
            Write-Output "USAGE: check-worker <initiative-id>"
        }
    }

    "session-output" {
        if ($ExtraArgs.Count -gt 0) {
            $initId = $ExtraArgs[0]
            $outputFile = JoinPaths @($ClaudeDir, "workspaces", $initId, "session_output.json")
            if (Test-Path $outputFile) {
                try {
                    $content = Get-Content $outputFile -Raw -Encoding UTF8
                } catch {
                    $content = Get-Content $outputFile -Raw
                }
                $content = $content -replace "`0", ""
                Write-Output $content.Trim()
            } else {
                Write-Output "NO_OUTPUT_FILE init=$initId"
            }
        } else {
            Write-Output "USAGE: session-output <initiative-id>"
        }
    }

    default {
        Write-Output "Orchestrator Tools"
        Write-Output "=================="
        Write-Output "Commands:"
        Write-Output "  daemon-status       Check if daemon is running"
        Write-Output "  daemon-log [N]      Show last N lines of daemon log (default 30)"
        Write-Output "  daemon-start        Start daemon (kills existing first)"
        Write-Output "  daemon-stop         Stop daemon"
        Write-Output "  daemon-restart      Restart daemon"
        Write-Output "  list-python         List all Python processes"
        Write-Output "  kill-pid <pid>      Kill a specific process"
        Write-Output "  check-worker <id>   Check worker PIDs for an initiative"
        Write-Output "  session-output <id> Read session output for an initiative"
        Write-Output ""
        Write-Output "Usage from Git Bash:"
        Write-Output "  powershell -ExecutionPolicy Bypass -File .claude/orch-tools.ps1 daemon-status"
    }
}
