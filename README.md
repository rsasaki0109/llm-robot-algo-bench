# llm-robot-algo-bench

## プロジェクト概要

`llm-robot-algo-bench` は、**LLM が生成したロボティクス用アルゴリズム（またはそのスタブ）**を、**同一入出力仕様**で差し替え、指標付きで比較するための**ローカル実行向け**ベンチマーク基盤（MVP）です。GPU 不要の依存のみで、CLI から入力データを与え、JSON で結果を受け取ります。

## 「LLMがロボットアルゴリズムを書けるか？」

実運用に即して評価するには、生成コードが**センサ形式・座標系・制約**を正しく扱い、**再現性のある**形で出せるかを切り分ける必要があります。本ツールは、

- **タスク定義**（入出力と評価式）を先に固定し、
- **runner** が同じ I/O 契約のもと「コードを実行」する責務に閉じ、
- **evaluator** はメトリクス計算に閉じる、

という分離で、**将来 LLM 生成コードの差し替え**（あるいはバンドル/動的 import）に耐える形にしています。

### model 名と実装の対応

`--model` は **`runner/model_registry.py`** の辞書で実装に解決されます。未登録名は従来どおり **`baseline`** にフォールバックします。別アルゴリズムを足すなら、各タスクの `run_*` 関数を実装し、`GNSS` / `LIDAR` / `VISION` に1行足してください。

## 3タスク（MVP）

| タスク | 入力 | 処理（baseline） | 指標（例） |
|--------|------|------------------|------------|
| `gnss` | NMEA（`.txt` 想定。サンプルは `sample.nmea`） | GGA 取得 → 第1 GGA 原点 ENU 変換、時刻差分で速度 | `rmse`, `speed_error` |
| `lidar` | 点群（`.npy` または簡易 ASCII PCD） | `DBSCAN` | `cluster_count_score`, `mean_iou` ほか |
| `vision` | 画像（`.jpg` 等、OpenCVで読み込み） | 輪郭＋条件で縦長ブロブ、ダメなら HOG フォールバック | `map50_simple`, `precision@0.5`, `recall@0.5`, `mean_iou_matched` |

各タスクの正解（または参照）データは `data/<task>/ground_truth.json`（LiDAR は `cluster_labels` が点順と一致）に置きます。GNSS の正解は**同じ NMEA をパーサ＋WGS84→ENU した結果**に合わせてあり、baseline では自整合（RMSE ≈ 0）になります。

## 前提

- Python 3.10 以上
- 推奨: 仮想環境（`python3 -m venv .venv`）

## インストール

```bash
cd /path/to/llm-robot-algo-bench
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

`pip install` が使えない場合は、プロジェクトルートを `PYTHONPATH` に加えて `python -m cli.main` を実行しても同様です（例: `PYTHONPATH=. python -m cli.main run ...`）。

## CLI 使い方

```text
bench run  --task <gnss|lidar|vision> --input <path> --model <name> [--out OUT] [--ground-truth PATH] [--noise F] [--viz]
bench eval --task <gnss|lidar|vision>  --result <result.json> [--out OUT] [--ground-truth PATH]
bench compare --dir <results_dir>
```

- **`run`**: 指定タスクの baseline を動かし、データディレクトリ内の正解があれば即時に `metrics` を付与して JSON を `results/` に保存（`--out` で上書き可）。
- **`eval`**: 既存 `result.json` の `predictions` から再評価（正解パス差し替え可）。
- **`compare`**: ディレクトリ内の `*.json`（`metrics` 付き）を集め、`leaderboard.md` / `leaderboard.csv` を生成。`leaderboard*.json` は除外。

## 出力 JSON の形（必須フィールド例）

```json
{
  "task": "gnss",
  "model": "gpt-5",
  "metrics": {
    "rmse": 0.0,
    "speed_error": 0.0
  },
  "runtime_ms": 0.2
}
```

`run` の完全な成果物には、追試験用に `input` や `predictions` も入ります。

## 拡張の方向

- **SLAM / センサ融合**: `tasks/slam/`, `evaluator/slam.py` のように、独立モジュール＋専用 evaluator を追加し、`runner.executor.run_task` に分岐を足す想定。
- **LLM 生成コード差し替え**: 上記レジストリ（`runner/model_registry.py`）に登録する、または一時ディレクトリに生成コードを書き `importlib` で読み込む等。
- **CI**: `.github/workflows/smoke.yml` で同梱サンプルに対する `bench run` を回します。
- **重い検出器**: 依存（例: 追加の DNN 重み）を分離し、オプション group でインストール。

## サンプル（リポジトリ同梱）

- GNSS: `data/gnss/sample.nmea`, `data/gnss/ground_truth.json`
- LiDAR: `data/lidar/points.npy`, `data/lidar/ground_truth.json`
- Vision: `data/vision/sample.jpg`, `data/vision/ground_truth.json`

## 付録: 正解再生成（GNSS）

NMEA 本文を変えたら、`data/gnss/ground_truth.json` を baseline と同じ手順の値に揃えてください。開発者向けに、パーサ＋`lla2enu` から一発で書き出すスニペットをリポジトリ内ドキュメントに残すのが安全です（現リポはサンプル用に揃え済み）。

## ライセンス

本リポジトリ利用に際して、利用目的に合わせて必要ならライセンス行を追記してください（未設定のまま利用可のテンプレートとして扱います）。
