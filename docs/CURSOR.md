# Cursor 内でモデルを選んでベンチ用コードを書く

このリポは **CLI の外**で [Cursor](https://cursor.com) を開き、**チャット／Composer のモデル**を切り替えてアルゴリズム案・コードを生成する想定です。`bench run --model <名前>` の `<名前>` と、**Cursor で選ぶモデル**の対応は下表です。

## 推奨対応（このリポのスラッグ）

| Cursor で選ぶモデル（UI 表記は更新され得る） | `bench run --model` に渡す値 | 用途の目安 |
|---------------------------------------------|------------------------------|------------|
| **Composer**（高速系 / *Composer 2 Fast* など） | `composer-2-fast` | 短い差分・繰り返し試行、レジストリ用の実装を素早く書く |
| **Claude Opus**（*4.7* など最新系） | `opus-4.7` | 難しい幾何・制御・エッジケースの整理に向く前提で試す |

※ 未登録の `--model` は **いまは `baseline` 実装にフォールバック**する。生成したコードを **`runner/model_registry.py`** に登録したあと、同じ `--model` で**初めて独自実装が走る**。

## 手順（ざっくり）

1. Cursor で本リポを開く。
2. チャットまたは **Composer** を開き、**モデルピッカー**で上表のどちらかを選ぶ（例: *Composer* を速い方、*Opus* を重い方）。
3. `tasks/<task>/` の入出力仕様に合わせて `run_*` 相当の関数を生成してもらい、ファイルに保存する。
4. `runner/model_registry.py` の `GNSS` / `PLANNING` 等の辞書に  
   `"composer-2-fast"` または `"opus-4.7"` → その関数  
   を追加する。
5. 同梱 `data/` で  
   `bench run --task … --model composer-2-fast`  
   などを実行し、[README の表](../README.md) を更新する。

## 注意

- **Cursor API を `bench` が直接呼ぶわけではない**（ローカル CLI とエディタは別）。運用は「Cursor で編集 → 保存 → ターミナルで `bench`」。
- Cursor 側のモデル名・バージョンは製品更新で変わるため、**迷ったら UI の表示名と、このリポの JSON スナップショット（`docs/benchmarks/*.json`）の `model` フィールド**を揃える。
