#!/usr/bin/env bash
# OpenCode CLI の疎通（任意）＋ 本リポの bench 5 タスク一括。
# 使い方:
#   chmod +x scripts/bench_opencode_smoke.sh
#   ./scripts/bench_opencode_smoke.sh
#   BENCH_MODEL=baseline OPENCODE_MODEL="anthropic/claude-3-5-haiku-20241022" ./scripts/bench_opencode_smoke.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

BENCH_MODEL="${BENCH_MODEL:-baseline}"
OPENCODE_MODEL="${OPENCODE_MODEL:-}"

if ! command -v opencode &>/dev/null; then
  echo "opencode が PATH にありません。インストール: https://opencode.ai/docs/cli/" >&2
  exit 1
fi

echo "==> opencode: モデル一覧の更新 (models.dev) ==="
if opencode models --refresh &>/dev/null; then
  echo "  models キャッシュ更新済 (詳細: opencode models / opencode models --refresh -v )"
else
  echo "  警告: models --refresh に失敗 (ネットワーク等)。続行します。" >&2
fi

if [[ -n "$OPENCODE_MODEL" ]]; then
  echo "==> opencode: 疎通 ($OPENCODE_MODEL) — subscription/API の範囲で使えるか確認 ==="
  opencode run -m "$OPENCODE_MODEL" "Reply with exactly one line: SMOKE_OK"
  echo "OK (opencode run 完了)"
else
  echo "OPENCODE_MODEL 未設定: OpenCode 疎通はスキップ。指定例: export OPENCODE_MODEL=anthropic/<id>"
  echo "利用可能ID確認: opencode models"
fi

if [[ ! -d "$ROOT/.venv" ]]; then
  echo "仮想環境を作成します: python3 -m venv .venv" >&2
  python3 -m venv .venv
fi
# shellcheck source=/dev/null
. "$ROOT/.venv/bin/activate"
pip install -e . -q

echo "==> bench: 5 タスク (--model $BENCH_MODEL) ==="
run_bench() {
  local task=$1
  local inp=$2
  local out
  out="$(mktemp "/tmp/llm_robot_bench_${task}.XXXXXX.json")"
  bench run --task "$task" --input "$inp" --model "$BENCH_MODEL" --out "$out"
  echo "  $task -> $out"
}
run_bench gnss   data/gnss/sample.nmea
run_bench lidar  data/lidar/points.npy
run_bench vision data/vision/sample.jpg
run_bench planning data/planning/scenario.json
run_bench control  data/control/scenario.json
echo "==> 完了. metrics は各 JSON または bench compare --dir <dir> 参照 ==="
