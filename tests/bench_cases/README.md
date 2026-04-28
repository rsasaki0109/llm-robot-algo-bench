# bench_cases（将来用）

多ケース・AtCoder 型への拡張の **ディレクトリ例のメモ**のみ。

**ロードマップ・優先度・全体の「これから」は [docs/PLAN.md](../../docs/PLAN.md) に集約**している。

## データ布局の例（参考）

いまの MVP は `data/<task>/` に **1 本**のサンプル＋`ground_truth.json`。複数ケース化するときの例:

- **案 A**: `data/gnss/cases/case-01/`, `case-02/` … にそれぞれ input と `ground_truth.json`。
- **案 B**: 同じタスク内で `sample.nmea`, `edge_case.nmea`（GT はケース専用ファイルを併置）。

採点は毎回 `bench run` → 既存 `evaluator` の `metrics` で一貫させる（詳細は [docs/BENCH_JUDGE.md](../../docs/BENCH_JUDGE.md)）。
