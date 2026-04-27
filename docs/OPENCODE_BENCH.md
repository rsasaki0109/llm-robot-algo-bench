# OpenCode を「5 タスクのベンチ」に載せる（疎通では足りない理由）

`opencode run` 1 発・`wall_ms` だけの記録（[opencode_provider_smoke.json](benchmarks/opencode_provider_smoke.json)）は、**API が通るかの確認**に過ぎない。**ロボ 5 タスクの採点（`metrics` / `quality_pass`）ではない。**

**本当に** OpenCode 上のモデル（Kimi / Qwen 等）の実装力を測るには、同モデル（または同セッション）で**コードを生成し**、本リポに **1 行追加する**必要がある:

1. OpenCode で `tasks/<task>/baseline.py` 等を文脈に、**タスク用の `run_*` 実装**を生成（[prompts/opencode_bench_gnss.md](../prompts/opencode_bench_gnss.md) など）。
2. 生成物を `tasks/.../your_impl.py` として保存。
3. [runner/model_registry.py](../runner/model_registry.py) に `GNSS[...] = your_impl.run_gnss` のように**登録名**（例 `opencode-kimi-20260201`）を紐づける。
4. `bench run --task gnss --input data/gnss/sample.nmea --model opencode-kimi-20260201` … **5 タスクぶん**繰り返し（または一括用スクリプト）。
5. その `results/*.json` や [refresh_benchmark_docs.py](../scripts/refresh_benchmark_docs.py) で **docs 用スナップショット**に載せる。

**SUMMARY 表に「`opencode-go/...` 行」があるのは、疎通の記録用**であり、**bench の点数表ではない**（[OPENCODE.md](OPENCODE.md) も併覧）。

`composer-2-fast` / `opus-4.7` も同様: **未登録なら baseline と同じ実装**が走るので、「そのモデル専用の採点」には**レジストリ登録**が要る。詳細は [CURSOR.md](CURSOR.md)。
