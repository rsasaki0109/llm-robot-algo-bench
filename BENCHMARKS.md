# ベンチマーク参考結果（同梱サンプル・baseline）

**条件**: リポ内の `data/<task>/` サンプル＋`--model baseline`。**GNSS** は正解を同じ NMEA から整合させているため、**RMSE は数値誤差レベル**になる（baseline の自己一致チェック用途）。**実行日**: 2026-04-27（手元ローカル1回、実行時間は目安）。

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

## 再現手順

```bash
. .venv/bin/activate
pip install -e .
bench run --task gnss   --input data/gnss/sample.nmea   --model baseline
bench run --task lidar  --input data/lidar/points.npy    --model baseline
bench run --task vision --input data/vision/sample.jpg   --model baseline
```

出力 JSON には上記 `metrics` と `runtime_ms` が含まれる。自環境の数値比較用に `results/` に保存して `bench compare --dir results` も可。

## 解釈の注意

- **時間**は CPU・負荷で変動する。CI（GitHub Actions）でもスモークは同じ手順を実行する。
- 実データでは GNSS/検出の指標はサンプルより悪化する。本表は**仕様同梱デモ**の目安に留める。
