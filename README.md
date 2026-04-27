# llm-robot-algo-bench

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![CI smoke](https://github.com/rsasaki0109/llm-robot-algo-bench/actions/workflows/smoke.yml/badge.svg)

**👉 ベンチ結果** → [docs/benchmarks/SUMMARY.md](docs/benchmarks/SUMMARY.md)

- **JSON＋SUMMARY を同梱データで作り直す（推奨）**: `python3 scripts/refresh_benchmark_docs.py` → `docs/benchmarks/<model>.json` を上書きし、続けて `gen_benchmark_summary.py` で [SUMMARY.md](docs/benchmarks/SUMMARY.md) を更新。
- **SUMMARY だけ**既存 JSON から再生成: `python3 scripts/gen_benchmark_summary.py`。

**比較の主軸**は **正しさ**（`metrics` / `quality_pass`）と、必要なら **実装の複雑度**（`impl.code_metrics`、実ソースの LOC・分岐目安）。**`runtime_ms` は補助**。**出題上の難易度**は `task_spec.difficulty_tier`（タスク種別）で分けている。詳細は [SUMMARY.md](docs/benchmarks/SUMMARY.md) 冒頭。  
**AtCoder 風に「テストで AC か」をやるイメージ**は [docs/BENCH_JUDGE.md](docs/BENCH_JUDGE.md)（サンプル／ジャッジ／隠しテストの対応表と、多ケース化の次の一歩）。

**SUMMARY の見方（重要）**:

- **AC (`quality_pass`)**: 5 タスク中 **何本「合格」したか**（例 `4/5`）
- **Impl (`!fallback`)**: 5 タスク中 **何本「フォールバック無し」で動いたか**（例 `1/5`）。ここが低いと「そのモデルの実装ができた」とは言いにくい（baseline が代わりに走っている）。

**何ができる？** ロボ向け **5 タスク**（**GNSS / LiDAR / 画像 / 計画 `planning` / 制御 `control`）のパイプラインに対し、**同じ入力**で **生成アルゴ or baseline** を走らせ、**数値＋JSON** で比較する。**GPU 不要・ローカル CLI**（`bench run`）。

**知覚（センサ・画像）**に加え、**動作計画（グリッド上の経路）**と **制御（1 次系追従）** も**同列のタスク**として入っています（`tasks/`＋`evaluator/`＋`model_registry`）。

---

## 各モデル（LLM）別ベンチマーク結果

**同じ同梱サンプル**（`data/*` 各タスク）に対する**主要指標**を並べる。**ここを更新していく**と、来訪者が一発で比較できます。

### 知覚・センサ系

| モデル名 (`--model`) | 実体 | GNSS: RMSE / 速度誤差 | LiDAR: 数 / IoU | Vision: mAP(簡) / p0.5 / IoU | 測定日 (UTC) |
|---------------------|------|----------------------|-----------------|-----------------------------|-------------|
| `baseline` | 同梱実装 | ~0 / ~0 | 1.0 / 1.0 | 1.0 / 1.0 / 0.98 | 2026-04-27 |
| `composer-2-fast` | *現状* baseline と同一実装※ | ≈0 / ≈0 | 1.0 / 1.0 | 1.0 / 1.0 / 0.98 | 2026-04-27 |
| `opus-4.7` | *現状* baseline と同一実装※ | ≈0 / ≈0 | 1.0 / 1.0 | 1.0 / 1.0 / 0.98 | 2026-04-27 |
| *未登録名* | → baseline フォールバック | 〃 | 〃 | 〃 | － |
| *（例）* `xxx` | `model_registry` に個別登録 | ― | ― | ― | ― |

※ **`composer-2-fast`** / **`opus-4.7`** など未登録の `--model` は、いま **実行コードは `baseline` と同じ**（`runner/model_registry` のフォールバック）。**将来、LLM 生成の別実装を紐づけたら**、各モデル行の数値は独立して意味を持つ。

### 計画・制御

| モデル | planning: 到達 / 長さ超過 / 衝突なし / way MAE | control: `rmse` / `max_abs` | 測定日 (UTC) |
|--------|----------------------------------------------|----------------------------|-------------|
| `baseline` | 1.0 / 0 / 1.0 / 0.0 | 0 / 0 | 2026-04-27 |
| `composer-2-fast` | 1.0 / 0 / 1.0 / 0.0 ※上と同条件 | 0 / 0 ※上と同条件 | 2026-04-27 |
| `opus-4.7` | 1.0 / 0 / 1.0 / 0.0 ※上と同条件 | 0 / 0 ※上と同条件 | 2026-04-27 |
| *未登録名* | 〃 | 〃 | － |
| *（例）* `xxx` | ― 追記 ― | ― 追記 ― | ― |

**出し方（追記用）** — 同梱パス例:

```bash
bench run --task gnss      --input data/gnss/sample.nmea       --model <名前>
bench run --task lidar     --input data/lidar/points.npy        --model <名前>
bench run --task vision    --input data/vision/sample.jpg     --model <名前>
bench run --task planning  --input data/planning/scenario.json  --model <名前>
bench run --task control   --input data/control/scenario.json   --model <名前>
```

手作業で `results/*.json` の `metrics` を上表に貼る運用も可。一括なら **上記 `refresh_benchmark_docs.py`**。比較表は `bench compare --dir results`（`leaderboard.md` に `runtime_ms` 横棒付き）。

補足: 同梱デモの数値解釈・再現コマンドの詳細は **[BENCHMARKS.md](BENCHMARKS.md)**。`--model` ごとの**生 JSON 指標**: [composer-2-fast](docs/benchmarks/composer-2-fast.json) / [opus-4.7](docs/benchmarks/opus-4.7.json)（**いずれも現状 baseline フォールバック**）。

### 参考：タスク別に何を測るか

| タスク | 同梱データで何を見る？ | 主な指標 | 目安 `runtime_ms`* |
|--------|------------------------|----------|--------------------|
| **gnss** | NMEA → ENU ＋ 速度 | `rmse`, `speed_error` | **~0.2** |
| **lidar** | 点群クラスタ | `cluster_count_score`, `mean_iou` | **~6** |
| **vision** | 人物 bbox | `map50_simple`, `precision@0.5`, `mean_iou_matched` | **~13** |
| **planning** | 2D 格子＋障害、A* 経路 | `reaches_goal`, `length_excess`, `collision_free`, `waypoint_mae` | **~0.2** |
| **control** | 1 次系＋P 制御追従 | `rmse`, `max_abs`, `mean_abs` | **~0.1** |

\*1台のPCで前後。実データの別セットで測る場合は、表の「備考」列にデータ名を足すとよい。

---

## プロジェクト概要

`llm-robot-algo-bench` は、**LLM が生成したロボティクス用アルゴリズム**（やスタブ）を、**同一入出力**で差し替え、指標付きで比較する**ベンチマーク基盤（MVP）**です。GPU 不要の依存のみ。CLI から入れて JSON を受け取れます。

## 「LLMがロボットアルゴリズムを書けるか？」

実運用の前に、生成コードが**センサ形式・座標系**を扱い、**再現**できるかを分けたい。本リポは、

- **タスク定義**（入出力と評価式）を先に固定し、
- **runner** は「同じI/Oで実行」だけ、
- **evaluator** は指標計算だけ、

に分け、**将来、LLM生成コードを `model` に差し替え**しやすい形にしています（現状 `baseline` 実装＋レジストリ）。

### model 名と実装

`--model` は **`runner/model_registry.py`** の辞書で解決。未登録名は **`baseline` にフォールバック**。

**Cursor での書き方**: エディタ内で **Composer（2 Fast）** や **Opus 4.7** を選んで生成したコードを、上の `composer-2-fast` / `opus-4.7` に紐づけて登録する（**[docs/CURSOR.md](docs/CURSOR.md)**）。定数だけ使う場合は `utils/cursor_models.py` の `COMPOSER_2_FAST` / `OPUS_4_7`。

**OpenCode CLI**（端末）で **`opencode models`** / **`opencode run -m provider/model`** を使う場合は **[docs/OPENCODE.md](docs/OPENCODE.md)**。サブスクリプション内の最新IDは `opencode models --refresh` で確認 → 一括 `bench` は **`scripts/bench_opencode_smoke.sh`**。**疎通ログ**（`bench` の得点ではない）: [opencode_provider_smoke.json](docs/benchmarks/opencode_provider_smoke.json)。**5 タスクを本当に測るには** [docs/OPENCODE_BENCH.md](docs/OPENCODE_BENCH.md)（生成コードを `model_registry` に載せる）。

## タスク一覧（MVP＝5 本）

| タスク | 入力 | 処理（baseline） | 指標（例） |
|--------|------|------------------|------------|
| `gnss` | NMEA | GGA → 第1 GGA 原点 ENU、時刻差分で速度 | `rmse`, `speed_error` |
| `lidar` | `.npy` / 簡易 PCD | `DBSCAN` | `cluster_count_score`, `mean_iou` ほか |
| `vision` | 画像 | 輪郭＋簡易人物 bbox（失敗時 HOG フォールバック） | `map50_simple` 等 |
| `planning` | JSON（格子・始点終点） | 4 近傍 A-star 経路 | 上表 |
| `control` | JSON（`p_ref`・`dt`・`K` 等） | 飽和付き 1 次追従 | 上表 |

## 前提

- Python 3.10 以上
- 推奨: 仮想環境

## インストール

```bash
cd /path/to/llm-robot-algo-bench
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

`pip` が使えない場合: `PYTHONPATH=.` を付けて `python -m cli.main run ...` でも可。

## CLI

```text
bench run  --task <gnss|lidar|vision|planning|control> --input <path> --model <name> [--out OUT] [--ground-truth PATH] [--noise F] [--viz]
bench eval --task <...>  --result <result.json> [--out OUT] [--ground-truth PATH]
bench compare --dir <results_dir>
```

- **`run`**: baseline（または登録実装）を実行し、正解があれば `metrics` を付けて `results/` に JSON（`--out`で指定可）
- **`eval`**: 保存済み `result.json` から再評価
- **`compare`**: 複数 JSON を表に（`leaderboard.md` / `.csv`）。GitHub の「About」文案は **[GITHUB_ABOUT.md](GITHUB_ABOUT.md)**（コピペ用）

## 出力 JSON（例）

```json
{
  "task": "gnss",
  "model": "baseline",
  "metrics": { "rmse": 0.0, "speed_error": 0.0 },
  "runtime_ms": 0.2
}
```

`predictions` 等は追試用に同梱。

## 拡張ロードマップ（上の先）

| 層 | 例（次の一手） | 方針 |
|----|---------------|------|
| **計画** | ダイクストラ以外の法則、時刻窓、キノダイナミクス的コスト | `tasks/planning/` 差し替え＋`evaluator` 拡張 |
| **制御** | 2 次系、状態制約、簡易 MPC / PID チューニング比較 | `tasks/control/` 差し替え |
| **知覚・推定** | **SLAM / センサ融合**、追加センサ | 新 `tasks/*` ＋ evaluator |
| **横断** | `model_registry`、README 表、CI | 既存のまま |

**制御と計画は本リポで既にタスク化済み**（`planning` / `control`）。**LLM コード差し替え**は `model_registry` か一時生成＋`importlib`。**CI**は `.github/workflows/smoke.yml`（5 タスクスモーク）。

---

## 同梱サンプル

- GNSS: `data/gnss/sample.nmea`, `data/gnss/ground_truth.json`
- LiDAR: `data/lidar/points.npy`, `data/lidar/ground_truth.json`
- Vision: `data/vision/sample.jpg`, `data/vision/ground_truth.json`
- Planning: `data/planning/scenario.json`, `data/planning/ground_truth.json`（`ref_path` 付き）
- Control: `data/control/scenario.json`, `data/control/ground_truth.json`（`ref_trajectory` 付き）

**数値の詳しい表** → [BENCHMARKS.md](BENCHMARKS.md)  
**GitHub の「About」用テキスト** → [GITHUB_ABOUT.md](GITHUB_ABOUT.md)

## 付録: GNSS 正解

NMEA を変えたら `data/gnss/ground_truth.json` を baseline と同じ手順で揃え直すこと。

## ライセンス

未設定。必要に応じて好きなライセンス行を足してください。
