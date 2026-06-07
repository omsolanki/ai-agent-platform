#!/usr/bin/env bash
# Render all D2 diagrams to SVG + PDF (shared theme, horizontal legend).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v d2 >/dev/null 2>&1; then
  echo "Error: d2 CLI not found. Install from https://d2lang.com/" >&2
  exit 1
fi

D2_FLAGS=(--scale 1 --pad 60 --center)

DIAGRAMS=(
  intelligence-workbench
  system-context
  agent-interaction
  agent-state-flow
  base-agent
  workflow-sequence
  workflow-state
  workflow-routing
  memory-architecture
  evaluation-flow
  evaluation-improvement
  observability-traces
  scaling-evolution
  cost-cache
  cost-model-tier
  cost-fallback
  governance-hitl
  deployment-local
  deployment-aws
  deployment-k8s
)

for name in "${DIAGRAMS[@]}"; do
  echo "Rendering ${name} ..."
  combined="${name}.build.d2"
  cat "_theme-a4.d2" "${name}.d2" "_legend.d2" > "$combined"
  d2 "${D2_FLAGS[@]}" "$combined" "${name}.svg"
  d2 "${D2_FLAGS[@]}" "$combined" "${name}.pdf"
  rm -f "$combined"
done

echo "Done. Rendered ${#DIAGRAMS[@]} diagrams (SVG + PDF)."
