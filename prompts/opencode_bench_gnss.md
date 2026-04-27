# OpenCode 向け: GNSS タスク差し替えプロンプト（例）

`opencode run` に渡すときは `-f` で当リポのファイルを添付するとよい。

---

あなたは `tasks/gnss/baseline.py` の **入出力互換**を保ったまま、同じ `run_gnss(input_path, model=..., noise_m=0.0) -> dict` シグネチャで新しい実装案を出して。

- 戻りは少なくとも `enu_trajectory`（各点に `t_s`, `e_m`, `n_m`, `u_m`）と `speed_m_s` の list。
- 既存の NMEA パーサ `tasks.gnss.nmea` は再利用してよい。
- 最後に、このファイルを1つの Python モジュールとして丸ごと貼る形式で出力して。

---

English:

Keep the same public API as `run_gnss` in `tasks/gnss/baseline.py`, reuse `tasks.gnss.nmea` if helpful, and output a single self-contained module body.
