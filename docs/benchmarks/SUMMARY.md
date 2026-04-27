# ベンチ結果（一覧）

同梱 `data/*` の **`bench run` → `runtime_ms` の一覧**（**品質**は各 JSON の `metrics` 参照。未登録 `model` は **baseline 実装**のため**数値は同系**）。

**OpenCode Go** 行（`opencode-go/...`）は 5 タスク未実施（`—`）。 最右列 *疎通* は [docs/benchmarks/opencode_provider_smoke.json](opencode_provider_smoke.json) の `opencode run` **1 回**の `wall_ms`（**Go 枠**のモデルID・API/ネット依存）。 更新: `OPENCODE_MODELS=opencode-go/...` で `python3 scripts/refresh_opencode_provider_smoke.py` → 本 SUMMARY 再生成。

| モデル | gnss (ms) | lidar (ms) | vision (ms) | planning (ms) | control (ms) | 5 タスク計 / *疎通* (ms) |
|--------|-----------|------------|-------------|---------------|--------------|------------|
| `baseline` | 0.23 | 6.3 | 12 | 0.33 | 0.12 | **~19** |
| `composer-2-fast` | 0.20 | 1.6 | 3.1 | 0.29 | 0.14 | **~5.3** |
| `opus-4.7` | 0.17 | 2.1 | 2.8 | 0.37 | 0.10 | **~5.5** |
| `opencode-go/kimi-k2.6` | — | — | — | — | — | *疎通 ~8056* |
| `opencode-go/qwen3.6-plus` | — | — | — | — | — | *疎通 ~9482* |
| `opencode-go/deepseek-v4-pro` | — | — | — | — | — | *疎通 ~5136* |

## `runtime_ms` 横棒（5 タスク合計、相対）

最長行をフル幅（`█`）に合わせた**相対比**（**絶対速度の主張ではない**）。 合計は 5 タスク `runtime_ms` の和。**OpenCode Go 行はここに含まない**（疎通は下の専用図）。

```
`baseline`         ██████████████████████  19 ms
`composer-2-fast`  ██████················  5.3 ms
`opus-4.7`         ██████················  5.5 ms
```

## OpenCode Go 疎通 `wall_ms` 横棒（1 回 `opencode run`、相対）

5 タスク `bench` とは**別物**（`opencode-go/...`）。最長 `wall_ms` をフル幅（`█`）に合わせた**相対比**。

```
`opencode-go/kimi-k2.6`        ███████████████████···  8056 ms
`opencode-go/qwen3.6-plus`     ██████████████████████  9482 ms
`opencode-go/deepseek-v4-pro`  ████████████··········  5136 ms
```

## タスク別 `runtime_ms` 横棒

各タスク内で**モデル同士**を比較（タスク横ではスケールが違うので縦の表と併用）。

### gnss

```
`baseline`         ██████████████████████  0.23 ms
`composer-2-fast`  ███████████████████···  0.20 ms
`opus-4.7`         █████████████████·····  0.17 ms
```

### lidar

```
`baseline`         ██████████████████████  6.3 ms
`composer-2-fast`  ██████················  1.6 ms
`opus-4.7`         ███████···············  2.1 ms
```

### vision

```
`baseline`         ██████████████████████  12 ms
`composer-2-fast`  ██████················  3.1 ms
`opus-4.7`         █████·················  2.8 ms
```

### planning

```
`baseline`         ████████████████████··  0.33 ms
`composer-2-fast`  █████████████████·····  0.29 ms
`opus-4.7`         ██████████████████████  0.37 ms
```

### control

```
`baseline`         ███████████████████···  0.12 ms
`composer-2-fast`  ██████████████████████  0.14 ms
`opus-4.7`         █████████████████·····  0.10 ms
```

## 品質（要点・同梱自己整合）

上表の **bench 行**はいずれも **~0 誤差 / 1.0 スコア** 系（NMEA 自己整合、LiDAR 3 クラ、Vision mAP(簡)~1 等・details は各 `metrics`）。**OpenCode Go 行**に品質指標はない。

## 元データ（JSON）

- [`baseline`](baseline.json)
- [`composer-2-fast`](composer-2-fast.json)
- [`opus-4.7`](opus-4.7.json)
- [OpenCode **Go** 疎通（`opencode run` ・上表の `opencode-go/...` 行）](opencode_provider_smoke.json)
