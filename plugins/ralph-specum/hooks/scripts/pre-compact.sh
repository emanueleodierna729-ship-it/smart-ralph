#!/usr/bin/env bash
# PreCompact Hook for Ralph Specum — Preserves execution context before context compression.
# Outputs a state block that Claude retains in its compressed context so the execution
# loop can resume without losing its place.

INPUT=$(cat)

command -v jq >/dev/null 2>&1 || exit 0

CWD=$(echo "$INPUT" | jq -r '.cwd // empty' 2>/dev/null || true)
if [ -z "$CWD" ]; then
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RALPH_CWD="$CWD"
export RALPH_CWD
source "$SCRIPT_DIR/path-resolver.sh"

SPEC_RELATIVE_PATH=$(ralph_resolve_current 2>/dev/null)
if [ -z "$SPEC_RELATIVE_PATH" ]; then
    exit 0
fi

SPEC_PATH="$CWD/$SPEC_RELATIVE_PATH"
SPEC_NAME=$(basename "$SPEC_RELATIVE_PATH")
STATE_FILE="$SPEC_PATH/.ralph-state.json"

if [ ! -f "$STATE_FILE" ] || ! jq empty "$STATE_FILE" 2>/dev/null; then
    exit 0
fi

PHASE=$(jq -r '.phase // "unknown"' "$STATE_FILE" 2>/dev/null)
if [ "$PHASE" != "execution" ]; then
    exit 0
fi

TASK_INDEX=$(jq -r '.taskIndex // 0' "$STATE_FILE" 2>/dev/null)
TOTAL_TASKS=$(jq -r '.totalTasks // 0' "$STATE_FILE" 2>/dev/null)
TASK_ITERATION=$(jq -r '.taskIteration // 1' "$STATE_FILE" 2>/dev/null)
GLOBAL_ITERATION=$(jq -r '.globalIteration // 1' "$STATE_FILE" 2>/dev/null)
RECOVERY_MODE=$(jq -r '.recoveryMode // false' "$STATE_FILE" 2>/dev/null)

TASKS_FILE="$SPEC_PATH/tasks.md"
PROGRESS_FILE="$SPEC_PATH/.progress.md"

# Extract the current task block from tasks.md
CURRENT_TASK_BLOCK=""
if [ -f "$TASKS_FILE" ] && command -v awk >/dev/null 2>&1; then
    CURRENT_TASK_BLOCK=$(awk -v idx="$TASK_INDEX" '
        BEGIN { count=-1; found=0; block="" }
        /^- \[.\]/ { count++; if (count == idx) { found=1; block=$0 "\n"; next } else { found=0 } }
        found && /^  / { block=block $0 "\n"; next }
        found && /^$/ { block=block $0 "\n"; next }
        found && !/^  / && !/^$/ { exit }
        END { printf "%s", block }
    ' "$TASKS_FILE")
fi

# Read progress summary (last 40 lines to keep it concise)
PROGRESS_SUMMARY=""
if [ -f "$PROGRESS_FILE" ]; then
    PROGRESS_SUMMARY=$(tail -40 "$PROGRESS_FILE" 2>/dev/null)
fi

# Output the preservation block — Claude includes this in its compressed context
cat <<PRECOMPACT_EOF
[RALPH SPECUM — SESSION CONTEXT CHECKPOINT]
Spec: $SPEC_NAME | Phase: execution | Task: $((TASK_INDEX + 1))/$TOTAL_TASKS
Iter: task=$TASK_ITERATION global=$GLOBAL_ITERATION | Recovery: $RECOVERY_MODE
State: $SPEC_PATH/.ralph-state.json

Current task:
$CURRENT_TASK_BLOCK

Progress:
$PROGRESS_SUMMARY

ACTION REQUIRED: The execution loop is still active. After this context compression:
- The stop-hook (Stop event) will automatically output the resume prompt.
- Do NOT restart the spec. Just continue responding and the loop will resume.
- If execution stalls, run: /ralph-specum:implement
PRECOMPACT_EOF

exit 0
