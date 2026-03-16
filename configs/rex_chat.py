"""REX Chat — CLIエントリポイント（--trade / --news / 対話モード）。

各機能は src/ 配下のモジュールに分離済み。
このファイルは CLI の組み立てと対話ループのみを担当する。
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from configs.settings import ROOT_DIR, PNG_DATA_DIR, TEXT_LOG_DIR  # noqa: E402
from src.chat import call_grok_chat_completions  # noqa: E402
from src.history import load_conversation_history, save_conversation_history  # noqa: E402
from src.market import fetch_trade_data  # noqa: E402
from src.news import get_gm_news  # noqa: E402
from src.plotter import save_normalized_plot  # noqa: E402
from src.regime import build_regime_snapshot  # noqa: E402
from src.utils import ensure_dir_exists  # noqa: E402


def main() -> int:
    load_dotenv(ROOT_DIR / ".env")

    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        print(
            "ERROR: XAI_API_KEY が見つかりません。.env か環境変数に設定してください。",
            file=sys.stderr,
        )
        return 2

    model = os.getenv("XAI_MODEL", "grok-4")

    history_path = Path(
        os.getenv(
            "XAI_HISTORY_FILE",
            TEXT_LOG_DIR / "conversation_history.json",
        )
    )

    # Rex_Prompt..txt の読み込み（REX_PROMPT_FILE）は node 側へ移管。
    # ここではファイルに紐づけず、固定の system プロンプトのみ使用する。
    base_messages: List[Dict[str, str]] = [
        {
            "role": "system",
            "content": "あなたはRex。Minatoの永遠のパートナーで、GMトレードとシステム構築のプロ。常に日本語で温かく論理的に答える。",
        }
    ]

    loaded = load_conversation_history(history_path)
    if loaded and any(m.get("role") == "system" for m in loaded):
        messages: List[Dict[str, str]] = list(loaded)  # type: ignore[assignment]
    else:
        messages = base_messages + (loaded or [])

    parser = argparse.ArgumentParser(description="REX Chat with trade/news mode")
    parser.add_argument(
        "--trade",
        action="store_true",
        help="8ペア30日データ自動取得＋プロット生成＆挿入",
    )
    parser.add_argument(
        "--news",
        action="store_true",
        help="GMキーワードニュース取得＆挿入 (BRICS/CBDC/地政学)",
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        help="一回きりのプロンプト（省略時は対話モード）",
    )
    args = parser.parse_args()

    if args.trade or args.news:
        news_text = ""
        if args.news:
            keywords = "CBDC US economy japan stock europe emerging geopolitics middle east ukraine"
            news_text = get_gm_news(keywords)
            print(f"[--news] GMニュース取得:\n{news_text}")

        if args.trade:
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            print(f"[--trade] 8ペア30日データ取得中: {start_date} 〜 {end_date}")

            df_all, pair_snapshots, multi_data_text = fetch_trade_data(days=30)

            if pair_snapshots:
                try:
                    regime_label, regime_summary, regime_yaml = build_regime_snapshot(
                        start_date, end_date, pair_snapshots
                    )
                    regime_path = PNG_DATA_DIR / f"{end_date:%Y_%m_%d}_snapshot.yaml"
                    ensure_dir_exists(regime_path.parent)
                    regime_path.write_text(regime_yaml, encoding="utf-8")
                    print(f"[--trade] レジームスナップショット保存: {regime_path}")
                    multi_data_text = (
                        multi_data_text
                        + "\n\n"
                        + f"[regime] {regime_label} ({regime_summary})"
                    )
                except Exception as e:
                    print(f"[--trade] レジーム判定/保存でエラー: {e}", file=sys.stderr)

            system_content = f"最新8ペア30日データ:\n{multi_data_text}\nこのデータを見てGM戦略を提案して。"
            if news_text:
                system_content += f"\nニュース:\n{news_text}"

            messages.insert(
                0,
                {"role": "system", "content": system_content},
            )

            if not df_all.empty:
                try:
                    plot_path = save_normalized_plot(df_all)
                    print(f"[--trade] プロット保存: {plot_path}")
                except Exception as e:
                    print(f"[--trade] プロット保存でエラー: {e}", file=sys.stderr)

            print(multi_data_text)
            print("\n[完了] データ/ニュース挿入！ Rexに戦略相談しよう！")

        elif args.news:
            system_content = f"最新GMニュース:\n{news_text}\nこのニュースを踏まえてGM戦略の観点から分析して。"
            messages.insert(0, {"role": "system", "content": system_content})
            print("\n[完了] ニュース挿入！ Rexに戦略相談しよう！")


    arg_prompt = " ".join(args.prompt).strip()
    if arg_prompt:
        messages.append({"role": "user", "content": arg_prompt})
        try:
            text = call_grok_chat_completions(
                api_key=api_key, model=model, messages=messages
            )
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
        messages.append({"role": "assistant", "content": text})
        try:
            save_conversation_history(history_path, messages, model=model)
        except Exception:
            pass
        print(str(text).strip())
        return 0

    print(f"Grok Assistant ready (model={model}). 空行で終了します。")
    print(
        "（8ペア30日データ＋プロットを使うには: python main.py --trade で起動）"
    )

    while True:
        try:
            prompt = input("> ").strip()
        except EOFError:
            break

        if not prompt:
            break

        messages.append({"role": "user", "content": prompt})
        try:
            text = call_grok_chat_completions(
                api_key=api_key, model=model, messages=messages
            )
            messages.append({"role": "assistant", "content": text})
            save_conversation_history(history_path, messages, model=model)
            print(str(text).strip())
            print()
        except Exception as e:
            messages.pop()  # 送信に失敗したユーザーメッセージを戻す（履歴に残さない）
            print(f"ERROR: {e}", file=sys.stderr)
            print(
                "同じ内容でもう一度送るか、別のメッセージを入力して続行できます。空行で終了。",
                file=sys.stderr,
            )
            print()

    try:
        save_conversation_history(history_path, messages, model=model)
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
