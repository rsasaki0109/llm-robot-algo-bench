# GitHub リポジトリの「About」設定メモ

GitHub の **Settings はファイルでは置けない**ため、**リポのトップ** → 歯車（⚙）「About」欄に、下をコピペして使ってください。検索・関連リポ・スターに効きます。

## README のクイック表との同期

ルート [README.md](README.md) に **短いリーダーボード表**がある場合、[docs/benchmarks/SUMMARY.md](docs/benchmarks/SUMMARY.md) と数字がずれないよう、`refresh_benchmark_docs.py` のあと必要なら README のスナップショット行だけ更新してください。**正本は常に SUMMARY / `docs/benchmarks/*.json`** とします。

## Description（1行・英語向け / 国際閲覧用）

```
Lightweight, GPU-free Python CLI to benchmark LLM-generated robotics code: perception (GNSS, LiDAR, vision) plus planning (grid A*) and control (1st-order tracking). Swappable `model` hooks + JSON metrics.
```

**日本メインにしたい場合（短）:**

```
GPU不要。GNSS/点群/画像に加えグリッド計画(Planning)と追従制御(Control)をCLI＋JSONで比較。LLMのalgo差し替え可。
```

## Website（任意）

- 使わない: 空のまま
- 入れる: ドキュメント用 GitHub Pages や、公開ノートの URL
- デフォルト案: リポの URL  
  `https://github.com/rsasaki0109/llm-robot-algo-bench`（**実際のユーザー名/リポ名に合わせて**書き換え）

## Topics（推奨タグ。検索用）

下からコピーして、About の「Add topics」に足す想定（スペース区切りで GitHub に入力、または `,` 区切り）:

```
benchmark robotics llm generative-ai python
gnss nmea enu
lidar point-cloud dbscan
computer-vision opencv
motion-planning path-planning
control-theory tracking
cli numpy scikit-learn
```

短くするなら最低限:

```
benchmark robotics llm python gnss lidar computer-vision motion-planning control
```

## README の CI バッジ（フォーク先）

[README](README.md) 冒頭の `actions/.../smoke.yml/badge.svg` も、**`OWNER/REPO` を自身のリポ名**に合わせると、緑バッジが意図どおり出ます。

## チェックボックス

- [ ] **Releases** を使うなら、初回 v0.1.0 など
- [ ] **Packages** 不要なら何もしなくてよい
- [ ] スター・フォーク用に **Repository name** は短いまま、**Description** は上記で埋める

README の冒頭に**結果が一目で分かる表**を置いてあるので、About と合わせて初見で「何のリポか・何が出るか」が伝わります。
