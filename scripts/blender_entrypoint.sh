#!/bin/bash
set -eo pipefail

# Ensure passes and scenes bus directories exist
mkdir -p /workspace/passes /workspace/scenes

# If command arguments are provided, execute them directly
if [ "$#" -gt 0 ]; then
    exec "$@"
fi

# Otherwise launch the default background worker runner
exec python3 /opt/scripts/blender_runner.py
