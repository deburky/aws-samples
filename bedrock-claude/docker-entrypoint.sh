#!/bin/bash
set -e

VENV="/app/app/.venv"
export VIRTUAL_ENV="$VENV"
export PATH="$VENV/bin:/root/.local/bin:$PATH"

# ttyd URL exposed to the browser — default to same host on port 7681
export TTYD_URL="${TTYD_URL:-http://localhost:7681}"

THEME='{"background":"#ffffff","foreground":"#1f2937","cursor":"#374151","cursorAccent":"#ffffff","selectionBackground":"#bfdbfe","black":"#1f2937","brightBlack":"#6b7280","red":"#dc2626","brightRed":"#ef4444","green":"#16a34a","brightGreen":"#22c55e","yellow":"#d97706","brightYellow":"#f59e0b","blue":"#2563eb","brightBlue":"#3b82f6","magenta":"#7c3aed","brightMagenta":"#8b5cf6","cyan":"#0891b2","brightCyan":"#06b6d4","white":"#f9fafb","brightWhite":"#ffffff"}'

# Start ttyd (Claude Code, no permission prompts, light theme)
ttyd -p 7681 -W \
  -t "theme=$THEME" \
  -t fontSize=14 \
  claude --dangerously-skip-permissions &

# Start Marimo
exec uv run --python "$VENV/bin/python" \
    marimo run /app/app/text2sql.py \
    --host 0.0.0.0 \
    --port 2718 \
    --no-token
