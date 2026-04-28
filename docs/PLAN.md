# 開発計画・ロードマップ（単一メモ）

LLM ロボアルゴベンチの **いま何があり／これから何をするか** をここにまとめる。細かい採点の語彙（サンプル／ジャッジ／隠しテスト）は [BENCH_JUDGE.md](BENCH_JUDGE.md)。多ケース用ディレクトリの置き場メモは [tests/bench_cases/README.md](../tests/bench_cases/README.md)。

---

## 結論（現状）

| 項目 | 状態 |
|------|------|
| 5 タスク（GNSS / LiDAR / vision / planning / control） | 同梱データ・evaluator・`bench run` で利用可能 |
| `model_registry` + `tasks/generated/` | LLM 生成コードの差し替え・フォールバック検知 |
| 同梱ベンチ結果 | `docs/benchmarks/SUMMARY.md` + 各 `*.json` |
| CI | `.github/workflows/smoke.yml`（5 タスク baseline） |
| 多ケース・隠しテスト | **未実装**（設計だけ [BENCH_JUDGE.md](BENCH_JUDGE.md)） |

---

## フェーズ 1 — 信頼して使ってもらう（優先度高）

1. **README / SUMMARY と実装のズレ防止**  
   数値の正本は `docs/benchmarks/*.json` と SUMMARY。手で README の表を触ったあとは `scripts/refresh_benchmark_docs.py` で揃える運用（[GITHUB_ABOUT.md](../GITHUB_ABOUT.md) 参照）。

2. **期待値の明示（クレーム回避）**  
   `quality_pass` はデモ閾値（`utils/quality_gates.py`）。本番データでは閾値・指標を別途定義する前提を README / 本書で維持。

3. **（任意）デモ GIF / 短い動画**  
   `bench run` 一連を README に載せると初見の離脱が減る。素材はリポ外でも可。

---

## フェーズ 2 — AtCoder 型に近づける（多ケース）

**目的**: 単一サンプルでの「雑 AC」から、**ケース列での合否**へ。

| 項目 | 内容 |
|------|------|
| データ布局の例 | `data/<task>/cases/case-01/` … のように input + GT を並べる（案は [tests/bench_cases/README.md](../tests/bench_cases/README.md)） |
| 実行 | `bench run` をケースごとにループし、`metrics` / `quality_pass` をケース別に記録 → 全体 AC は「全ケース通過」など集約ルールで定義 |
| 閾値 | `quality_gates` をケース別 YAML/JSON に逃がす案（[BENCH_JUDGE.md](BENCH_JUDGE.md)） |
| CI | 同梱ケースは必ず回す。秘密ケースは別リポジトリ or Secret 成果物 |

補助スクリプト（例: `scripts/run_all_cases.py`）は **インタフェースが固まってから** でよい。

---

## フェーズ 3 — タスク横の拡張（あれば）

旧 README にあった「層ごとの次の一手」のイメージを**優先度は固定しない**メモとして残す。

| 層 | 例 | 方針 |
|----|-----|------|
| **Planning** | 別ヒューリスティック、対角コストの出し分け、時刻窓 | `tasks/planning/` 差し替え + evaluator 拡張 |
| **Control** | 2 次系、PID/MPC 比較 | `tasks/control/` + evaluator |
| **知覚・推定** | SLAM、センサ融合 | 新 `tasks/*` と evaluator を追加 |
| **横断** | `model_registry`、ドキュメント、CI の強化 | 既存パターンを踏襲 |

---

## やらないこと（スコープ外の例）

- 商用ロボの安全認証・リアルタイム保証をこのリポだけで提供する。
- 特定ベンダのクラウド API を前提にした実行（CLI はローカル第一）。

---

## 関連リンク

| 文書 | 役割 |
|------|------|
| [BENCH_JUDGE.md](BENCH_JUDGE.md) | 採点メタファと `quality_pass` の位置づけ |
| [benchmarks/SUMMARY.md](benchmarks/SUMMARY.md) | 現在の数値一覧 |
| [OPENCODE_BENCH.md](OPENCODE_BENCH.md) | OpenCode で 5 タスクを本番計測する手順 |
| [BENCHMARKS.md](../BENCHMARKS.md) | 再現手順・指標の読み方 |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | PR・CI との揃え方 |

---

## 更新ルール

計画の変更は **本ファイルを正** とし、散在させない。`BENCH_JUDGE.md` は「用語・設計思想」、`tests/bench_cases/README.md` は「ディレクトリ例の最小メモ」に留める。
