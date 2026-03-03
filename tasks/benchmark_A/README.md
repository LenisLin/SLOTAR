# Benchmark A Pipeline (Skeleton)

This task directory contains benchmark-specific orchestration code.
It must implement Plan B:
- structural zeros are bypassed at task level
- `src/slotar` solver is fail-fast and raises ValueError on invalid inputs

Edit `pipeline.py` to load your benchmark A dataset and produce:
- metrics table (with uot_status/bypass_reason)
- events table (may be empty initially)