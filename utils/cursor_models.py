"""
Cursor エディタのモデル選択と、bench の --model 引数を揃えるための定数。

使い方（例）::

    from utils.cursor_models import COMPOSER_2_FAST, OPUS_4_7
    GNSS[COMPOSER_2_FAST] = my_run_gnss

※ 実際に登録するのは runner/model_registry.py 側。
"""

# Cursor の「Composer」高速系で生成した実装を紐づけるとき
COMPOSER_2_FAST = "composer-2-fast"

# Cursor の「Claude Opus」（4.7 系など）で生成した実装を紐づけるとき
OPUS_4_7 = "opus-4.7"
