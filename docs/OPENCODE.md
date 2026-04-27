# OpenCode CLI で「最新モデル」＆ベンチ検証

[OpenCode](https://opencode.ai) はターミナル用のコーディングエージェントで、`opencode run -m provider/model` の形で**モデルを指定**できます。サブスクリプションや API キーで使える範囲は **`opencode auth login`** 済みのプロバイダに依存します（[CLI ドキュメント](https://opencode.ai/docs/cli/)）。

本リポの **`bench` は OpenCode の中で動くわけではない**ので、次の2段階に分かれます。

1. **OpenCode 側**: 使える**最新**の `provider/model` を選び、必要ならコード生成用プロンプトを実行する。  
2. **本リポ側**: 生成物を `runner/model_registry.py` に登録したあと、従来どおり `bench run --model <登録名>` で数値比較。

## 1. 準備

```bash
# OpenCode 本体（未導入なら公式の手順: https://opencode.ai/docs/cli/）
opencode --version

# プロバイダログイン（API キー / サブスクリプション範囲は各サービスの設定に従う）
opencode auth login
```

## 2. 最新のモデル一覧（**OpenCode Go** 等の subscription で `opencode-go/...` が増えることあり）

`opencode models --refresh` のあと、利用可能行を確認。例（環境・プランで異なる）:

- `opencode/...`（無償/製品同梱の軽量系）
- `opencode-go/glm-5.1`, `opencode-go/kimi-k2.6`, `opencode-go/qwen3.6-plus` など（**Go** サブスク枠。実名は毎回 `opencode models` 参照）

**subscription の範囲で**使う ID を選び、次章の `OPENCODE_MODEL` にその**丸ごと1行**を入れる。一覧の取り方:

```bash
opencode models --refresh
opencode models
opencode models opencode-go
```

表示される **`<provider>/<model_id>`** を、そのまま `-m` に渡せます。  
（Cursor の *Composer* / *Opus* とは**別物**。OpenCode では上記の表記に合わせる。）

## 3. 接続スモーク（短い1発）

サブスクリプション内で使いたい1つを `OPENCODE_MODEL` に入れて実行:

```bash
# 例: OpenCode Go 枠（実際の行は毎回 `opencode models` で確かめる）
export OPENCODE_MODEL="opencode-go/glm-5.1"

opencode run -m "$OPENCODE_MODEL" "Reply with exactly: PING_OK"
```

エラーなら**キー・枠・モデルID**の見直し（`opencode auth list` など）。

## 4. 本リポの5タスクを一括 `bench`（登録済みの `--model` 名用）

`bench` の `--model` は **このリポの `model_registry` 名**（例: `baseline`, あなたが登録した `my-opus-v1`）。  
OpenCode の `provider/model` 文字列をそのまま使う**必要はない**（紐づけは人間が登録名で行う）。

一括スクリプト例:

```bash
cd /path/to/llm-robot-algo-bench
./scripts/bench_opencode_smoke.sh
# または: BENCH_MODEL=baseline OPENCODE_MODEL=anthropic/... ./scripts/bench_opencode_smoke.sh
```

- `OPENCODE_MODEL` を**セットした場合**: 先に OpenCode へ短い疎通を1回。  
- `BENCH_MODEL`（デフォルト `baseline`）: このリポの `bench run --model` に渡す。

## 5. 生成コードを「検証の一本化」に载せる

1. `opencode run -m "$OPENCODE_MODEL" -f tasks/gnss/baseline.py` のように、**既存 baseline を文脈に**プロンプト（[prompts/opencode_bench_gnss.md](../prompts/opencode_bench_gnss.md) 参照）。  
2. 出力を `tasks/gnss/my_impl.py` 等に保存。  
3. `runner/model_registry.py` の `GNSS` に例: `"opencode-gnss-20260427": my_impl.run_gnss` を追加。  
4. `bench run --task gnss --input data/gnss/sample.nmea --model opencode-gnss-20260427`  
5. [README](README.md) の表に行を足す。

## 参考

- [docs/CURSOR.md](CURSOR.md)（Cursor 側の Composer / Opus と `--model` スラッグの整理）  
- 環境変数 `OPENCODE_ENABLE_EXPERIMENTAL_MODELS=1` で**実験的モデル**を有効にできる場合あり（[OpenCode env](https://opencode.ai/docs/cli/)）
