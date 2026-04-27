# ベンチ結果（一覧）

## 評価の優先順位（このリポ）

1. **`metrics` / `quality_pass`** … 同梱データで**仕様を満たしたか**（主指標）
2. **`impl.code_metrics`** … 実際に走った実装の**ソース規模・分岐の目安**（アルゴリズム/コード難易の補助。**`runtime_ms` とは独立**）
3. **`task_spec.difficulty_tier`** … **出題上**の段階（1=軽め 3=重め。タスク種別の違い）
4. **`runtime_ms`** … 参考（再現比較には使えるが、主目的ではない）


## タスク別・出題上の難易度（`task_spec`）

| タスク | tier | 系統 | メモ |
|--------|------|------|------|
| `gnss` | 1 | sensors/geometry | NMEA パース＋自己整合。局所的な幾何・時系列内挿。 |
| `lidar` | 2 | point_cloud/clustering | 点群からクラスタ。ラベリング/IoU 系。 |
| `vision` | 2 | image/detection | bbox 検出と mAP(簡易)。前処理・重なり。 |
| `planning` | 3 | grid_path/graph | 格子・障害・経路。探索/制約の扱い。 |
| `control` | 2 | ode/tracking | 1 次系＋目標追従。制御則＋積分。 |


> **疎通＝採点ではない**: 下の **OpenCode Go** ブロックは **`opencode run` 1 回**の接続・応答（`wall_ms`）の記録。 **GNSS / LiDAR / … の `metrics` や本ベンチの比較ではない**。 そのモデルで本当に測る手順: [../OPENCODE_BENCH.md](../OPENCODE_BENCH.md)（生成コード → `model_registry` → `bench run`）。


## OpenCode Go smoke results

1 回 `opencode run` あたりの **wall_ms**（**bench の 5 タスク得点ではない**）。 日付 **2026-04-27 (UTC)** ・[生 JSON](opencode_provider_smoke.json)。

`executed_by`: scripts/refresh_opencode_provider_smoke.py @ sasaki-desktop

| model | wall_ms | ok |
|-------|---------|----|
| `opencode-go/kimi-k2.6` | **4698** ms | OK |
| `opencode-go/qwen3.6-plus` | **7570** ms | OK |
| `opencode-go/deepseek-v4-pro` | **6180** ms | OK |

同梱 `data/*` で `bench run` した**クイック表**。 **正しさ・合格**は各 `docs/benchmarks/<model>.json` の `metrics` / `quality_pass`、**コードの重さ**は `impl.code_metrics` を見る。 未登録 `model` は **baseline 実装**にフォールバック（`impl.used_fallback`）。

**OpenCode Go** 行（`opencode-go/...`）は 5 タスク未実施（`—`）。 最右列 *疎通* は [docs/benchmarks/opencode_provider_smoke.json](opencode_provider_smoke.json) の `opencode run` **1 回**の `wall_ms`（**Go 枠**のモデルID・API/ネット依存）。 更新: `OPENCODE_MODELS=opencode-go/...` で `python3 scripts/refresh_opencode_provider_smoke.py` → 本 SUMMARY 再生成。

| モデル | gnss (ms) | lidar (ms) | vision (ms) | planning (ms) | control (ms) | 5 タスク計 / *疎通* (ms) |
|--------|-----------|------------|-------------|---------------|--------------|------------|
| `baseline` | 0.22 | 2.8 | 12 | 0.30 | 0.10 | **~16** |
| `composer-2-fast` | 0.17 | 2.2 | 2.7 | 0.30 | 0.07 | **~5.5** |
| `opus-4.7` | 0.11 | 1.5 | 2.0 | 0.27 | 0.08 | **~3.9** |
| `opencode-go/kimi-k2.6` | — | — | — | — | — | *疎通 ~4698* |
| `opencode-go/qwen3.6-plus` | — | — | — | — | — | *疎通 ~7570* |
| `opencode-go/deepseek-v4-pro` | — | — | — | — | — | *疎通 ~6180* |

## `runtime_ms` 横棒（5 タスク合計、相対）

最長行をフル幅（`█`）に合わせた**相対比**（**絶対速度の主張ではない**）。 合計は 5 タスク `runtime_ms` の和。**OpenCode Go 行はここに含まない**（疎通は下の専用図）。

```
`baseline`         ██████████████████████  16 ms
`composer-2-fast`  ████████··············  5.5 ms
`opus-4.7`         ██████················  3.9 ms
```

## OpenCode Go 疎通 `wall_ms` 横棒（1 回 `opencode run`、相対）

5 タスク `bench` とは**別物**（`opencode-go/...`）。最長 `wall_ms` をフル幅（`█`）に合わせた**相対比**。

```
`opencode-go/kimi-k2.6`        ██████████████········  4698 ms
`opencode-go/qwen3.6-plus`     ██████████████████████  7570 ms
`opencode-go/deepseek-v4-pro`  ██████████████████····  6180 ms
```

## タスク別 `runtime_ms` 横棒

各タスク内で**モデル同士**を比較（タスク横ではスケールが違うので縦の表と併用）。

### gnss

```
`baseline`         ██████████████████████  0.22 ms
`composer-2-fast`  █████████████████·····  0.17 ms
`opus-4.7`         ███████████···········  0.11 ms
```

### lidar

```
`baseline`         ██████████████████████  2.8 ms
`composer-2-fast`  ██████████████████····  2.2 ms
`opus-4.7`         ████████████··········  1.5 ms
```

### vision

```
`baseline`         ██████████████████████  12 ms
`composer-2-fast`  █████·················  2.7 ms
`opus-4.7`         ████··················  2.0 ms
```

### planning

```
`baseline`         ██████████████████████  0.30 ms
`composer-2-fast`  ██████████████████████  0.30 ms
`opus-4.7`         ███████████████████···  0.27 ms
```

### control

```
`baseline`         ██████████████████████  0.10 ms
`composer-2-fast`  ██████████████········  0.07 ms
`opus-4.7`         █████████████████·····  0.08 ms
```

## 品質・合格（`quality_pass` と `metrics`）

同梱デモでは **bench** 系は `quality_pass` が真になりやすい（各 JSON → `tasks.<task>.quality_pass`）。 精査は**生の** `metrics`。**出題難易**は `task_spec`、**実装の重さ**は `impl.code_metrics`（速さとは別）。 **OpenCode Go 行**に品質指標はない。

## 元データ（JSON）

- [`baseline`](baseline.json)
- [`composer-2-fast`](composer-2-fast.json)
- [`opus-4.7`](opus-4.7.json)
- [OpenCode **Go** 疎通（`opencode run` ・上表の `opencode-go/...` 行）](opencode_provider_smoke.json)
