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


同梱 `data/*` で `bench run` した**クイック表**。 **正しさ・合格**は各 `docs/benchmarks/<model>.json` の `metrics` / `quality_pass`、**コードの重さ**は `impl.code_metrics` を見る。 未登録 `model` は **baseline 実装**にフォールバック（`impl.used_fallback`）。

| モデル | AC (`quality_pass`) | AC（タスク別） | Impl（非フォールバック） | gnss (ms) | lidar (ms) | vision (ms) | planning (ms) | control (ms) | 5 タスク計 (ms) |
|--------|--------------------|------------|-------------------------|-----------|------------|-------------|---------------|--------------|------------|
| `baseline` | **5/5** | G✓ L✓ V✓ P✓ C✓ | 5/5 | 0.21 | 5.9 | 8.9 | 0.19 | 0.09 | **~15** |
| `opencode-go_kimi-k2.6` | **5/5** | G✓ L✓ V✓ P✓ C✓ | 5/5 | 0.31 | 9.5 | 595 | 0.67 | 0.40 | **~605** |
| `opencode-go_qwen3.6-plus` | **4/5** | G✗ L✓ V✓ P✓ C✓ | 5/5 | 0.64 | 2.4 | 238 | 0.81 | 0.36 | **~242** |
| `opencode-go_deepseek-v4-pro` | **5/5** | G✓ L✓ V✓ P✓ C✓ | 5/5 | 0.47 | 2.8 | 323 | 0.68 | 0.37 | **~327** |
| `composer-2-fast` | **4/5** | G✗ L✓ V✓ P✓ C✓ | 0/5 | 0.85 | 2.2 | 572 | 0.30 | 0.14 | **~575** |
| `opus-4.7` | **4/5** | G✗ L✓ V✓ P✓ C✓ | 0/5 | 0.87 | 2.1 | 575 | 0.32 | 0.12 | **~578** |

## `runtime_ms` 横棒（5 タスク合計、相対）

最長行をフル幅（`█`）に合わせた**相対比**（**絶対速度の主張ではない**）。 合計は 5 タスク `runtime_ms` の和。

```
`baseline`                     █·····················  15 ms
`opencode-go_kimi-k2.6`        ██████████████████████  605 ms
`opencode-go_qwen3.6-plus`     █████████·············  242 ms
`opencode-go_deepseek-v4-pro`  ████████████··········  327 ms
`composer-2-fast`              █████████████████████·  575 ms
`opus-4.7`                     █████████████████████·  578 ms
```

## タスク別 `runtime_ms` 横棒

各タスク内で**モデル同士**を比較（タスク横ではスケールが違うので縦の表と併用）。

### gnss

```
`baseline`                     █████·················  0.21 ms
`opencode-go_kimi-k2.6`        ████████··············  0.31 ms
`opencode-go_qwen3.6-plus`     ████████████████······  0.64 ms
`opencode-go_deepseek-v4-pro`  ████████████··········  0.47 ms
`composer-2-fast`              █████████████████████·  0.85 ms
`opus-4.7`                     ██████████████████████  0.87 ms
```

### lidar

```
`baseline`                     ██████████████········  5.9 ms
`opencode-go_kimi-k2.6`        ██████████████████████  9.5 ms
`opencode-go_qwen3.6-plus`     ██████················  2.4 ms
`opencode-go_deepseek-v4-pro`  ███████···············  2.8 ms
`composer-2-fast`              █████·················  2.2 ms
`opus-4.7`                     █████·················  2.1 ms
```

### vision

```
`baseline`                     ······················  8.9 ms
`opencode-go_kimi-k2.6`        ██████████████████████  595 ms
`opencode-go_qwen3.6-plus`     █████████·············  238 ms
`opencode-go_deepseek-v4-pro`  ████████████··········  323 ms
`composer-2-fast`              █████████████████████·  572 ms
`opus-4.7`                     █████████████████████·  575 ms
```

### planning

```
`baseline`                     █████·················  0.19 ms
`opencode-go_kimi-k2.6`        ██████████████████····  0.67 ms
`opencode-go_qwen3.6-plus`     ██████████████████████  0.81 ms
`opencode-go_deepseek-v4-pro`  ███████████████████···  0.68 ms
`composer-2-fast`              ████████··············  0.30 ms
`opus-4.7`                     █████████·············  0.32 ms
```

### control

```
`baseline`                     █████·················  0.09 ms
`opencode-go_kimi-k2.6`        ██████████████████████  0.40 ms
`opencode-go_qwen3.6-plus`     ████████████████████··  0.36 ms
`opencode-go_deepseek-v4-pro`  █████████████████████·  0.37 ms
`composer-2-fast`              ████████··············  0.14 ms
`opus-4.7`                     ███████···············  0.12 ms
```

## 品質・合格（`quality_pass` と `metrics`）

同梱デモでは **bench** 系は `quality_pass` が真になりやすい（各 JSON → `tasks.<task>.quality_pass`）。 精査は**生の** `metrics`。**出題難易**は `task_spec`、**実装の重さ**は `impl.code_metrics`（速さとは別）。 **OpenCode Go 行**に品質指標はない。

## 元データ（JSON）

- [`baseline`](baseline.json)
- [`composer-2-fast`](composer-2-fast.json)
- [`opencode-go_deepseek-v4-pro`](opencode-go_deepseek-v4-pro.json)
- [`opencode-go_kimi-k2.6`](opencode-go_kimi-k2.6.json)
- [`opencode-go_qwen3.6-plus`](opencode-go_qwen3.6-plus.json)
- [`opus-4.7`](opus-4.7.json)
