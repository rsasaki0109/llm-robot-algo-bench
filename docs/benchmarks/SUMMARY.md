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

| モデル | gnss (ms) | lidar (ms) | vision (ms) | planning (ms) | control (ms) | 5 タスク計 (ms) |
|--------|-----------|------------|-------------|---------------|--------------|------------|
| `baseline` | 0.22 | 2.8 | 12 | 0.30 | 0.10 | **~16** |
| `composer-2-fast` | 0.17 | 2.2 | 2.7 | 0.30 | 0.07 | **~5.5** |
| `opus-4.7` | 0.11 | 1.5 | 2.0 | 0.27 | 0.08 | **~3.9** |

## `runtime_ms` 横棒（5 タスク合計、相対）

最長行をフル幅（`█`）に合わせた**相対比**（**絶対速度の主張ではない**）。 合計は 5 タスク `runtime_ms` の和。

```
`baseline`         ██████████████████████  16 ms
`composer-2-fast`  ████████··············  5.5 ms
`opus-4.7`         ██████················  3.9 ms
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
