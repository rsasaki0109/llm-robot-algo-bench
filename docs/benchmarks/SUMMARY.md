# ベンチ結果（一覧）

同梱 `data/*` ・**`runtime_ms` だけ**まず見る用（**品質指標**は各 JSON の `metrics` 参照。未登録 `model` は **baseline 実装**のため**数値は同系**）。

| モデル | gnss (ms) | lidar (ms) | vision (ms) | planning (ms) | control (ms) | 概算計 (ms) |
|--------|-----------|------------|-------------|---------------|--------------|------------|
| `baseline` | 0.23 | 5.8 | 12 | 0.37 | 0.14 | **~19** |
| `composer-2-fast` | 0.22 | 2.7 | 19 | 0.37 | 0.15 | **~23** |
| `opus-4.7` | 3.8 | 5.6 | 17 | 3.5 | 0.15 | **~30** |

## 品質（要点・同梱自己整合）

いずれも **~0 誤差 / 1.0 スコア** 系（NMEA 自己整合、LiDAR 3 クラ、Vision mAP(簡)~1 等・details は各 `metrics`）。

## 元データ（JSON）

- [`baseline`](baseline.json)
- [`composer-2-fast`](composer-2-fast.json)
- [`opus-4.7`](opus-4.7.json)
- [OpenCode 疎通のみ（bench 得点以外）](opencode_provider_smoke.json)
