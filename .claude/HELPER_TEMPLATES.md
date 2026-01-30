# HELPER BLOCK TEMPLATES — Copy & Paste Ready

Use these templates when you need to delegate work to Haiku helpers.
Just fill in the bracketed placeholders [LIKE_THIS] and use.

---

## Template 1: EXPLORATION HELPER
For: Analyzing files, understanding code structure, gathering context

```
EXPLORATION HELPER for [INITIATIVE_ID]
Model: Haiku
Workspace: .claude/workspaces/[INITIATIVE_ID]/

MANDATORY FIRST STEP: Read .claude/HELPER_WORKER_SYSTEM.md

TASK: Read and analyze the following files:
  [LIST_FILES_TO_READ: one per line]

ANALYSIS NEEDED:
  [DESCRIBE_WHAT_YOU_NEED_TO_KNOW]

OUTPUT: Write findings to .claude/workspaces/[INITIATIVE_ID]/findings.txt
FORMAT:
  [DESCRIBE_FORMAT: file paths with line numbers, summaries, code snippets, etc.]

When done, write "EXPLORATION_COMPLETE" as the last line of findings.txt.
```

Example:
```
EXPLORATION HELPER for INIT-020
Model: Haiku
Workspace: .claude/workspaces/INIT-020/

MANDATORY FIRST STEP: Read .claude/HELPER_WORKER_SYSTEM.md

TASK: Analyze error handling patterns in the worker-daemon.py

ANALYSIS NEEDED:
  1. Find all error handling blocks (try/except or if error checks)
  2. Report line numbers, error types, and handling approach
  3. Identify any gaps in error coverage
  4. Summarize in 20 lines max

OUTPUT: Write findings to .claude/workspaces/INIT-020/findings.txt
FORMAT:
  - List each error handler with line number and type
  - Show the handling code (2-3 lines)
  - List any missing error handlers

When done, write "EXPLORATION_COMPLETE" as the last line of findings.txt.
```

---

## Template 2: CODE SEARCH HELPER
For: Finding patterns, locating functions, searching for specific code

```
CODE SEARCH HELPER for [INITIATIVE_ID]
Model: Haiku
Workspace: .claude/workspaces/[INITIATIVE_ID]/

MANDATORY FIRST STEP: Read .claude/HELPER_WORKER_SYSTEM.md

TASK: Search codebase for [WHAT_TO_SEARCH]

SEARCH PATTERNS:
  [DESCRIBE_PATTERNS: what regex, keywords, or patterns to find]

SCOPE:
  Files: [WHICH_FILES: *.py, src/**, etc]
  Depth: [HOW_MANY_MATCHES: first 20, all, etc]

OUTPUT: Write findings to .claude/workspaces/[INITIATIVE_ID]/findings.txt
FORMAT:
  file_path:line_number:match_context

When done, write "SEARCH_COMPLETE" as the last line of findings.txt.
```

Example:
```
CODE SEARCH HELPER for INIT-021
Model: Haiku

TASK: Find all function definitions in worker-daemon.py

SEARCH PATTERN: ^def [a-z_]+\(

SCOPE:
  Files: .claude/worker-daemon.py
  Return: all matches with line numbers

OUTPUT: Write findings to .claude/workspaces/INIT-021/findings.txt
FORMAT:
  line_number: function_name(parameters)

When done, write "SEARCH_COMPLETE" as the last line.
```

---

## Template 3: FILE AUDIT HELPER
For: Verifying file structure, checking completeness, auditing against checklist

```
FILE AUDIT HELPER for [INITIATIVE_ID]
Model: Haiku

MANDATORY FIRST STEP: Read .claude/HELPER_WORKER_SYSTEM.md

TASK: Audit the following files against requirements:
  [LIST_FILES: one per line]

CHECKLIST:
  [LIST_REQUIREMENTS: one per line, e.g., 'Contains error handling', 'Has docstrings', etc]

OUTPUT: Write findings to .claude/workspaces/[INITIATIVE_ID]/findings.txt
FORMAT:
  ✓ Requirement [N]: [status, details, line numbers if relevant]
  ✗ Requirement [N]: [what's missing, where to add it]

When done, write "AUDIT_COMPLETE" as the last line.
```

---

## Template 4: CONTEXT HELPER
For: Checking workspace status, reading workspace files, summarizing progress

```
CONTEXT HELPER for [INITIATIVE_ID]
Model: Haiku

MANDATORY FIRST STEP: Read .claude/HELPER_WORKER_SYSTEM.md

TASK: Check and summarize workspace status

FILES_TO_READ:
  .claude/workspaces/[INITIATIVE_ID]/instructions.txt
  .claude/workspaces/[INITIATIVE_ID]/findings.txt
  .claude/workspaces/[INITIATIVE_ID]/results/

SUMMARY_NEEDED:
  1. List all pending tasks
  2. Report findings so far
  3. Summarize completed work
  4. List any blockers

OUTPUT: Write findings to .claude/workspaces/[INITIATIVE_ID]/status_summary.txt

When done, write "STATUS_COMPLETE" as the last line.
```

---

## How To Use These Templates

1. Copy the template that matches your need
2. Fill in [BRACKETED_PLACEHOLDERS]
3. Create file: .claude/pending_workers/[INITIATIVE_ID]_[helper_type].txt
4. Paste the filled-in template into that file
5. Create manifest.json with:
   ```json
   {
     "initiative_id": "[INITIATIVE_ID]",
     "workers": [{"file": "[INITIATIVE_ID]_[helper_type].txt", "model": "haiku", "type": "helper"}]
   }
   ```
6. Wait for findings.txt to appear and contain "_COMPLETE"

---

## When To Use Each Template

- **EXPLORATION**: Need to understand code, analyze structure, gather context
- **CODE SEARCH**: Need to find where something is, locate patterns, count occurrences
- **FILE AUDIT**: Need to verify something exists, check completeness, validate structure
- **CONTEXT**: Need to check on progress, read workspace files, summarize status

**Rule of thumb**: If you're thinking "I need to read this file", use EXPLORATION template instead.
