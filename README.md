# llm-robot-algo-bench

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/rsasaki0109/llm-robot-algo-bench/actions/workflows/smoke.yml/badge.svg)](https://github.com/rsasaki0109/llm-robot-algo-bench/actions/workflows/smoke.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Benchmark LLM-written robotics code** on one machine: **GNSS · LiDAR · vision · grid planning · 1st-order control** — same inputs, JSON metrics, **no GPU required**.

日本語: **同じサンプルデータ**で「生成アルゴリズム vs baseline」を並べ、**正しさ（metrics / quality_pass）**と実装の重さを見るための **CLI ベンチ**です（研究・再現向け MVP）。

---

## Why use this?

| You want… | This repo gives… |
|-----------|------------------|
| Fair comparison of **different `--model` implementations** | Fixed tasks + evaluators + bundled ground truth |
| **Planning + control**, not only perception | Five parallel tracks (`tasks/` + `evaluator/`) |
| Something that runs **locally** with numpy/sklearn/OpenCV | Install via `pip install -e .`, then `bench run …` |
| A starting point for **OpenCode / Cursor** workflows | Hooks + docs under `docs/` (`OPENCODE_BENCH.md`, `CURSOR.md`) |

If this saves you time, consider leaving a **star** — it helps others discover the project.

---

## 30-second quick start

```bash
git clone https://github.com/rsasaki0109/llm-robot-algo-bench.git
cd llm-robot-algo-bench
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
bench run --task gnss --input data/gnss/sample.nmea --model baseline --out /tmp/out.json
python3 -c "import json; print(json.load(open('/tmp/out.json'))['metrics'])"
```

Full five-task smoke matches CI — see [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Leaderboard (bundled data, reproducible)

Canonical table (updated when snapshots refresh):

👉 **[docs/benchmarks/SUMMARY.md](docs/benchmarks/SUMMARY.md)**

Compact snapshot (see SUMMARY for bars and details):

| Model | AC (`quality_pass`) | Per-task | Impl (non-fallback) |
|-------|---------------------|----------|----------------------|
| `baseline` | 5/5 | G✓ L✓ V✓ P✓ C✓ | 5/5 |
| `opencode-go_kimi-k2.6` | 5/5 | G✓ L✓ V✓ P✓ C✓ | 5/5 |
| `opencode-go_qwen3.6-plus` | 5/5 | G✓ L✓ V✓ P✓ C✓ | 5/5 |
| `opencode-go_deepseek-v4-pro` | 5/5 | G✓ L✓ V✓ P✓ C✓ | 5/5 |
| `composer-2-fast` / `opus-4.7` | 4/5* | … | 0/5* |

\*Unregistered `--model` names **fall back to `baseline` code** — metrics look good but **Impl 0/5** means you are not measuring custom weights. See `runner/model_registry.py`.

Regenerate JSON + SUMMARY from bundled data:

```bash
python3 scripts/refresh_benchmark_docs.py
```

---

## Scope & limitations (read before citing)

- **Research / benchmark harness**, not a certified robotics stack or safety proof.
- **`quality_pass`** uses **demo thresholds** in `utils/quality_gates.py` — tune for your own data.
- **Single sample per task** in the repo; multi-case “hidden tests” are described as a next step in [docs/BENCH_JUDGE.md](docs/BENCH_JUDGE.md).
- **OpenCode / LLM output varies** — generation scripts and timeouts are documented in `docs/OPENCODE.md` and `docs/OPENCODE_BENCH.md`.

---

## Documentation map

| Doc | Purpose |
|-----|---------|
| [docs/benchmarks/SUMMARY.md](docs/benchmarks/SUMMARY.md) | Main results & runtime bars |
| [BENCHMARKS.md](BENCHMARKS.md) | How to reproduce and read metrics |
| [docs/BENCH_JUDGE.md](docs/BENCH_JUDGE.md) | AtCoder-style mapping (samples / judge / future multi-case) |
| [docs/OPENCODE_BENCH.md](docs/OPENCODE_BENCH.md) | Why API smoke ≠ full bench; full 5-task flow |
| [GITHUB_ABOUT.md](GITHUB_ABOUT.md) | Copy-paste for repo **Description** & **Topics** (discovery / SEO) |
| [CONTRIBUTING.md](CONTRIBUTING.md) | PR checklist & CI commands |

---

## CLI

```text
bench run  --task <gnss|lidar|vision|planning|control> --input <path> --model <name> [--out OUT] [--ground-truth PATH] [--noise F] [--viz]
bench eval --task <...> --result <result.json> [--out OUT] [--ground-truth PATH]
bench compare --dir <results_dir>
```

- **`run`**: execute registered implementation (or baseline fallback), attach `metrics` when GT exists.
- **`eval`**: re-score saved JSON.
- **`compare`**: table / `leaderboard.md` / CSV.

---

## Tasks (MVP = 5)

| Task | Input | Notes |
|------|-------|-------|
| `gnss` | NMEA | ENU trajectory + speed vs GT |
| `lidar` | `.npy` point cloud | Clustering vs GT labels |
| `vision` | Image | Detection vs GT boxes |
| `planning` | Grid JSON | Path vs reference |
| `control` | Scenario JSON | Tracking vs reference trajectory |

## Installation

```bash
cd /path/to/llm-robot-algo-bench
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

Without install: `PYTHONPATH=. python -m cli.main run …`

---

## Sample data

| Task | Input | Ground truth |
|------|-------|--------------|
| GNSS | `data/gnss/sample.nmea` | `data/gnss/ground_truth.json` |
| LiDAR | `data/lidar/points.npy` | `data/lidar/ground_truth.json` |
| Vision | `data/vision/sample.jpg` | `data/vision/ground_truth.json` |
| Planning | `data/planning/scenario.json` | `data/planning/ground_truth.json` |
| Control | `data/control/scenario.json` | `data/control/ground_truth.json` |

---

## Model registry & LLM workflows

- **`--model`** resolves through **`runner/model_registry.py`**; unknown names → **baseline**.
- **Cursor**: [docs/CURSOR.md](docs/CURSOR.md)
- **OpenCode CLI**: [docs/OPENCODE.md](docs/OPENCODE.md) — full five-task benchmark: [docs/OPENCODE_BENCH.md](docs/OPENCODE_BENCH.md), helper **`scripts/generate_opencode_models.py`**.

---

## Output JSON (shape)

```json
{
  "task": "gnss",
  "model": "baseline",
  "metrics": { "rmse": 0.0, "speed_error": 0.0 },
  "runtime_ms": 0.2
}
```

`predictions` and paths are included for debugging / re-evaluation.

---

## Evaluation priorities (this repo)

1. **`metrics` / `quality_pass`** — correctness on bundled data  
2. **`impl.code_metrics`** — complexity of the code that actually ran  
3. **`task_spec.difficulty_tier`** — task family difficulty  
4. **`runtime_ms`** — secondary  

Details: [SUMMARY.md](docs/benchmarks/SUMMARY.md) introduction.

---

## Contributing

Issues and PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). Security expectations: [SECURITY.md](SECURITY.md).

---

## License

[MIT](LICENSE)
