# 採点の考え方（AtCoder 風の対応）

**「ちゃんと実装できたか」**を一番きれいに出すのは、**AtCoder っぽく「テストで判定」**に寄せることです。本リポの用語をそのイメージに対応させると次のとおり。

| AtCoder 的な概念 | いまのリポでの位置づけ | 備考 |
|-------------------|------------------------|------|
| **サンプル（問題文に載る入出力例）** | 同梱 `data/*`（例: `data/gnss/sample.nmea`）＋ [README / BENCHMARKS](../BENCHMARKS.md) の手順 | 誰でも同じコマンドで再現。 |
| **ジャッジ（採点プログラム）** | 各 `evaluator/*.py`（`metrics`）＋ 任意の [utils/quality_gates.py](../utils/quality_gates.py)（`quality_pass`） | 指標の定義＝**テストの採点ルール**に相当。 |
| **採用 / 不採用** | `quality_pass` や、閾値付き `metrics` の判定 | 同梱デモ用の**粗い**合格線は `quality_gates` にある。**本番データ用は別途、閾値を変える**想定。 |
| **TLE** | `runtime_ms` | **副指標**。主目的は正しさ（上記ジャッジ）。 |
| **隠しテスト** | **まだ同梱していない**（MVPは 1 本のサンプル/タスク） | 本番想定の入力は、リポ**外**や CI の非公開成果物、あるいは将来 `data/<task>/cases/case-XX/` のように**複数を追加**する形が自然。 |
| **全部のケース通過 = AC** | 全ケース `bench run` → 各 `quality_pass` / `metrics` を満たす | 多ケース化したら **ループ＋全成功で AC** という運用にする。 |

## 目指す形（おすすめの次の一歩）

1. **タスクごとに「ケース列」を定義**する（`case_id` ごとに `input` と期待 GT のペア。GNSS なら NMEA 複数、planning なら `scenario-*.json` 複数 など）。
2. **採点ルール**は `evaluator` を単一の正とし、閾値は `quality_gates` または**ケース別の YAML/JSON 設定**に分離する（AtCoder の**部分点**みたいに、将来は重み付けも可能）。
3. **CI**では「同梱サンプルのみ必ず」＋ 必要なら**秘密ケース**はプライベートリポ or Secret 配布（オープンリポのまま中身を出さない）。

`bench run` は **1 回＝1 入出力＋1 採点**なので、**多ケース＝`bench run` をケース分ループ＋最後に合否集計**、が一番そのまま AtCoder 型に近いです。

## いま入っている `quality_pass` との関係

- 単一サンプルに対する**手早い合格フラグ**（同梱デモ向け）です。  
- **厳密な AtCoder 型**にするなら、上の **(1) 多ケース**と **(2) ルールの外部化**に寄せるのが本筋で、`quality_pass` は **「このケース一発で雑に見た判定」**と割り切るか、**ケースごと**に出す拡張に置き換えていくのがよいです。

## 関連

- ベンチの目次・優先順位: [docs/benchmarks/SUMMARY.md](benchmarks/SUMMARY.md)  
- 同梱デモ用閾値: [utils/quality_gates.py](../utils/quality_gates.py)  
- 指標定義: [evaluator/](../evaluator/)  
