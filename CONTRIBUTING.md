# Contributing

Thanks for improving **llm-robot-algo-bench**.

## Quick checks (before a PR)

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e .
# Same commands as CI — all five tasks on bundled sample data:
bench run --task gnss      --input data/gnss/sample.nmea       --model baseline --out /tmp/r_gnss.json
bench run --task lidar     --input data/lidar/points.npy       --model baseline --out /tmp/r_lidar.json
bench run --task vision    --input data/vision/sample.jpg      --model baseline --out /tmp/r_vision.json
bench run --task planning  --input data/planning/scenario.json --model baseline --out /tmp/r_plan.json
bench run --task control   --input data/control/scenario.json   --model baseline --out /tmp/r_ctrl.json
```

CI runs these on Python **3.10** and **3.12** (see `.github/workflows/smoke.yml`).

## What belongs in this repo

- **Benchmark harness**: tasks, evaluators, CLI, reproducible bundled `data/`.
- **Docs**: keep claims aligned with what `bench run` actually measures (see `docs/BENCH_JUDGE.md` for design limits).
- **Roadmap**: avoid duplicating long-term plans in multiple files — update **`docs/PLAN.md`** instead.

## Changing benchmark numbers in `docs/benchmarks/`

Prefer regenerating snapshots instead of hand-editing JSON:

```bash
python3 scripts/refresh_benchmark_docs.py
```

Then review `docs/benchmarks/SUMMARY.md` and the per-model JSON files.

## Adding a model implementation

1. Implement `run_<task>(...)` under `tasks/` or `tasks/generated/<model_slug>/`.
2. Register names in `runner/model_registry.py`.
3. Run `refresh_benchmark_docs.py` (or document why not).

If you are unsure, open an issue with the intended `--model` string and task coverage.
