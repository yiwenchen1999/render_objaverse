#!/bin/bash
# =============================================================================
# Wrapper: run a command while logging nvidia-smi GPU usage to a file.
# Usage:
#   bash SonyAIClusterUtil/run_with_gpu_monitor.sh -- <your command>
#   bash SonyAIClusterUtil/run_with_gpu_monitor.sh -- "$BLENDER_BIN" -b -P render_3dmodels_dense_polyhaven.py -- --group_start 0 --group_end 1 ...
#
# Output: slurm_logs/gpu_usage_<timestamp>.csv (or $GPU_LOG_PATH if set)
# =============================================================================

set -euo pipefail

mkdir -p slurm_logs
LOG="${GPU_LOG_PATH:-slurm_logs/gpu_usage_$(date +%Y%m%d_%H%M%S).csv}"

# Find the first '--' to split wrapper args from the actual command
for i in "$@"; do
  if [[ "$i" == "--" ]]; then
    shift
    break
  fi
  shift
done

if [[ $# -eq 0 ]]; then
  echo "Usage: $0 -- <command> [args...]"
  echo "Example: $0 -- blender -b -P script.py -- --group_start 0 --group_end 1"
  exit 1
fi

cleanup() {
  [[ -n "${NPID:-}" ]] && kill "$NPID" 2>/dev/null || true
}
trap cleanup EXIT

# Start nvidia-smi logging (1s interval, CSV format)
echo "GPU monitor logging to $LOG"
nvidia-smi --query-gpu=timestamp,utilization.gpu,utilization.memory,memory.used,memory.total --format=csv -l 1 > "$LOG" 2>/dev/null &
NPID=$!

# Run the actual command
"$@"
