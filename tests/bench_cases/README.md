# 将来: 多ケース採用（AtCoder 型）の置き場

いまの MVP は `data/<task>/` に **1 本**のサンプル＋`ground_truth.json` です。  
**複数ケース**（サンプル追加・**隠し用はリポ外でも可**）にするときの例:

- 案 A: 本リポ内に `data/gnss/cases/case-01/`, `case-02/` … を置き、各に `input` と `ground_truth.json`。
- 案 B: 同じタスク内で `sample.nmea`, `edge_case.nmea`（GT は 1 ファイルに合わない場合はケース専用 GT を併置）。

採点は毎回 `bench run` → 既存 `evaluator` の `metrics` で一貫させる。  
方針の詳細は [docs/BENCH_JUDGE.md](../../docs/BENCH_JUDGE.md) を参照。
