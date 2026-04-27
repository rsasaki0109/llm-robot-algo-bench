# ベンチマーク参考（数値の詳細）

**各モデル・各 LLM の比較表は [README 冒頭付近](README.md) の「各モデル（LLM）別ベンチマーク結果」セクションを主に更新するのが推奨**（来訪者が一発で比較できる）。本ファイルは、同梱デモ条件の**詳細**と**再現手順**のメモ用です。

### `composer-2-fast`（`--model composer-2-fast`）

| 内容 | 値 |
|------|-----|
| 実行コード | 未登録のため **baseline と同一**（上と同指標。将来レジストリで差し替え可） |
| 生ログ（JSON まとめ） | [docs/benchmarks/composer-2-fast.json](docs/benchmarks/composer-2-fast.json)（`executed_by` 付きで再計測可） |
| 計測日 | 2026-04-27 (UTC) |

`runtime_ms` は**毎回変動**。直近のエージェント実行例: gnss 0.22, lidar 2.70, vision 19.5, planning 0.37, control 0.13 前後（**CPU・負荷依存**）。

### `opus-4.7`（`--model opus-4.7`）

| 内容 | 値 |
|------|-----|
| 実行コード | 未登録のため **baseline と同一**（指標は同梱自己整合。将来差し替え可） |
| 生ログ（JSON まとめ） | [docs/benchmarks/opus-4.7.json](docs/benchmarks/opus-4.7.json) |
| 計測日 | 2026-04-27 (UTC) |

`runtime_ms` 例: gnss 0.26, lidar 2.42, vision 14.4, planning 0.33, control 0.12（**環境で変動**）。**algo の差**は出ない（baseline 同一実装のため）が、**`--model` 名付きの検証**として同じ手順を踏める。

---

**条件**: リポ内の `data/<task>/` サンプル＋`--model baseline`（上の baseline 行）。**GNSS** は正解を同じ NMEA から整合させているため、**RMSE は数値誤差レベル**になる（baseline の自己一致チェック用途）。**実行日**: 2026-04-27（手元ローカル1回、実行時間は目安）。

## 指標

### GNSS（`data/gnss/sample.nmea`）

| メトリクス | 値（参考） |
|------------|------------|
| `rmse` [m] | ≈ 7.3e-13（≈0） |
| `speed_error` [m/s] | ≈ 4.1e-13（≈0） |
| `runtime_ms` | 約 0.2 |

### LiDAR（`data/lidar/points.npy`）

| メトリクス | 値（参考） |
|------------|------------|
| `cluster_count_score` | 1.0 |
| `mean_iou` | 1.0 |
| `n_pred_clusters` / `n_true_clusters` | 3 / 3 |
| `runtime_ms` | 約 5.7 |

### Vision（`data/vision/sample.jpg`）

| メトリクス | 値（参考） |
|------------|------------|
| `map50_simple` | 1.0 |
| `precision@0.5` | 1.0 |
| `recall@0.5` | 1.0 |
| `mean_iou_matched` | 約 0.984 |
| `runtime_ms` | 約 13.3 |

### Planning（`data/planning/scenario.json`）

| メトリクス | 値（参考） |
|------------|------------|
| `reaches_goal` | 1.0 |
| `length_excess` | 0.0 |
| `collision_free` | 1.0 |
| `waypoint_mae` | 0.0 |
| `runtime_ms` | 約 0.2 |

### Control（`data/control/scenario.json`）

| メトリクス | 値（参考） |
|------------|------------|
| `rmse` | 0.0（自己一致） |
| `max_abs` / `mean_abs` | 0.0 |
| `runtime_ms` | 約 0.1 |

## 再現手順

```bash
. .venv/bin/activate
pip install -e .
bench run --task gnss   --input data/gnss/sample.nmea   --model baseline
bench run --task lidar  --input data/lidar/points.npy    --model baseline
bench run --task vision --input data/vision/sample.jpg   --model baseline
bench run --task planning --input data/planning/scenario.json  --model baseline
bench run --task control  --input data/control/scenario.json   --model baseline
```

出力 JSON には上記 `metrics` と `runtime_ms` が含まれる。自環境の数値比較用に `results/` に保存して `bench compare --dir results` も可。

## 解釈の注意

- **時間**は CPU・負荷で変動する。CI（GitHub Actions）でもスモークは同じ手順を実行する。
- 実データでは GNSS/検出の指標はサンプルより悪化する。本表は**仕様同梱デモ**の目安に留める。
