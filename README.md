# llm-robot-algo-bench

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![CI smoke](https://github.com/rsasaki0109/llm-robot-algo-bench/actions/workflows/smoke.yml/badge.svg)

**何ができる？** ロボティクス向けの小さな3タスク（**GNSS / LiDAR / 画像**）について、**同じ入力**で **生成アルゴor baseline** を走らせ、**数値＋JSON**で比較する。**GPU不要・ローカルCLI**（`bench run`）。

---

## 各モデル（LLM）別ベンチマーク結果

**同じ同梱サンプル**（`data/gnss`, `data/lidar`, `data/vision`）に対する**主要指標**を並べる。**ここを更新していく**と、来訪者が一発で比較できます。

| モデル名 (`--model`) | 実体の説明 | GNSS: RMSE (m) / 速度誤差 (m/s) | LiDAR: 数一致 / mean IoU | Vision: mAP(簡) / p@0.5 / マッチ IoU | 測定日 (UTC) |
|---------------------|------------|--------------------------------|--------------------------|--------------------------------------|-------------|
| `baseline` | 同梱の参考実装 | ~0 / ~0 | 1.0 / 1.0 | 1.0 / 1.0 / 0.98 | 2026-04-27 |
| *（未登録の名前）* | レジストリ未登録時は上と**同じ** baseline | 〃 | 〃 | 〃 | － |
| *（例）* `gpt-4.1` 等 | 生成コードを `model_registry` 登録後 | ― 追記 ― | ― 追記 ― | ― 追記 ― | ― |

**出し方（追記用）** — 3タスクとも同梱パスで実行:

```bash
bench run --task gnss   --input data/gnss/sample.nmea   --model <名前>
bench run --task lidar  --input data/lidar/points.npy   --model <名前>
bench run --task vision --input data/vision/sample.jpg  --model <名前>
```

出力 `results/*.json` の `metrics` を上表に**1行**まとめて貼る（PR・コミットでOK）。`bench compare --dir results` で一覧化も可。

補足: 同梱デモの数値解釈・再現コマンドの詳細は **[BENCHMARKS.md](BENCHMARKS.md)**。

### 参考：タスク別に何を測るか

| タスク | 同梱データで何を見る？ | 主な指標 | 目安 `runtime_ms`* |
|--------|------------------------|----------|--------------------|
| **gnss** | NMEA → ENU ＋ 速度 | `rmse`, `speed_error` | **~0.2** |
| **lidar** | 点群クラスタ | `cluster_count_score`, `mean_iou` | **~6** |
| **vision** | 人物 bbox | `map50_simple`, `precision@0.5`, `mean_iou_matched` | **~13** |

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

## 3タスク（MVP）一覧

| タスク | 入力 | 処理（baseline） | 指標（例） |
|--------|------|------------------|------------|
| `gnss` | NMEA | GGA → 第1 GGA 原点 ENU、時刻差分で速度 | `rmse`, `speed_error` |
| `lidar` | `.npy` / 簡易PCD | `DBSCAN` | `cluster_count_score`, `mean_iou` ほか |
| `vision` | 画像 | 輪郭＋簡易人物 bbox（失敗時 HOG フォールバック） | `map50_simple` 等 |

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
bench run  --task <gnss|lidar|vision> --input <path> --model <name> [--out OUT] [--ground-truth PATH] [--noise F] [--viz]
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

## 拡張

- **SLAM / 融合**など: 独立 `tasks/*` ＋ evaluator を足す
- **LLM コード差し替え**: `model_registry` か、一時生成＋`importlib`
- **CI**: `.github/workflows/smoke.yml` で同梱サンプルに `bench run`

## 同梱サンプル

- GNSS: `data/gnss/sample.nmea`, `data/gnss/ground_truth.json`
- LiDAR: `data/lidar/points.npy`, `data/lidar/ground_truth.json`
- Vision: `data/vision/sample.jpg`, `data/vision/ground_truth.json`

**数値の詳しい表** → [BENCHMARKS.md](BENCHMARKS.md)  
**GitHub の「About」用テキスト** → [GITHUB_ABOUT.md](GITHUB_ABOUT.md)

## 付録: GNSS 正解

NMEA を変えたら `data/gnss/ground_truth.json` を baseline と同じ手順で揃え直すこと。

## ライセンス

未設定。必要に応じて好きなライセンス行を足してください。
