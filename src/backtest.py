"""backtest.py — USDJPY MTF v2 バックテスト。

python src/backtest.py で実行。
vectorbt 未インストールの場合は自前ループでシミュレーションする。
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

# リポジトリルートを path に追加
_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.data_fetch import fetch_multi_tf
from src.signals import mtf_minato_short_v2

# ── VectorBT があれば使う、なければ自前シミュレーション ──────
try:
    import vectorbt as vbt
    HAS_VBT = True
except ImportError:
    HAS_VBT = False


# ── 自前シンプルバックテスト（VectorBT 非依存） ─────────────
def _simple_backtest(
    close: pd.Series,
    entries: pd.Series,
    commission: float = 0.0005,
    slippage: float = 0.0002,
    risk_pct: float = 0.005,
    hold_bars: int = 10,
) -> Dict[str, Any]:
    """シグナルに従い固定バー数保持で損益を積み上げるシンプルシミュレーション。"""
    equity = 1.0
    trades: List[Dict[str, Any]] = []
    in_pos = False
    entry_idx = 0
    entry_price = 0.0

    close_arr = close.values.astype(float)
    entries_arr = entries.values.astype(bool)

    for i in range(len(close_arr)):
        if in_pos and (i - entry_idx) >= hold_bars:
            # 決済
            exit_price = close_arr[i] * (1 - slippage)
            pnl = (exit_price - entry_price) / entry_price - commission * 2
            equity *= (1 + pnl * risk_pct * 100)
            trades.append({
                "entry_bar": entry_idx,
                "exit_bar": i,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "pnl_pct": pnl * 100,
                "hold_bars": i - entry_idx,
            })
            in_pos = False

        if not in_pos and entries_arr[i]:
            entry_price = close_arr[i] * (1 + slippage)
            entry_idx = i
            in_pos = True

    # 未決済ポジションがあれば最終バーで決済
    if in_pos:
        exit_price = close_arr[-1] * (1 - slippage)
        pnl = (exit_price - entry_price) / entry_price - commission * 2
        equity *= (1 + pnl * risk_pct * 100)
        trades.append({
            "entry_bar": entry_idx,
            "exit_bar": len(close_arr) - 1,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl_pct": pnl * 100,
            "hold_bars": len(close_arr) - 1 - entry_idx,
        })

    if not trades:
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "max_drawdown_pct": 0.0,
            "avg_hold_bars": 0,
            "final_equity": equity,
        }

    df_trades = pd.DataFrame(trades)
    wins = df_trades[df_trades["pnl_pct"] > 0]
    losses = df_trades[df_trades["pnl_pct"] <= 0]
    gross_profit = float(wins["pnl_pct"].sum()) if len(wins) else 0.0
    gross_loss = float(losses["pnl_pct"].sum()) if len(losses) else 0.0
    pf = abs(gross_profit / gross_loss) if gross_loss != 0 else float("inf")

    # 最大ドローダウン（累積PnLベース）
    cum_pnl = df_trades["pnl_pct"].cumsum()
    running_max = cum_pnl.cummax()
    dd = running_max - cum_pnl
    max_dd = float(dd.max()) if len(dd) else 0.0

    return {
        "total_trades": len(trades),
        "win_rate": float(len(wins) / len(trades) * 100),
        "profit_factor": round(pf, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "avg_hold_bars": round(float(df_trades["hold_bars"].mean()), 1),
        "final_equity": round(equity, 4),
    }


# ── VectorBT 版バックテスト ──────────────────────────────────
def _vbt_backtest(
    close: pd.Series,
    entries: pd.Series,
    commission: float = 0.0005,
    slippage: float = 0.0002,
    risk_pct: float = 0.005,
) -> Dict[str, Any]:
    """vectorbt を使ったバックテスト（インストール済みの場合のみ）。"""
    exits = entries.shift(10).fillna(False)
    pf = vbt.Portfolio.from_signals(
        close,
        entries=entries,
        exits=exits,
        fees=commission,
        slippage=slippage,
        size=risk_pct,
        size_type="percent",
        freq="5T",
    )
    stats = pf.stats()
    
    # VectorBT stats() は pandas Series を返すので .loc[] でアクセス
    try:
        total_trades = int(stats.loc["Total Trades"]) if "Total Trades" in stats.index else 0
        win_rate = float(stats.loc["Win Rate [%]"]) if "Win Rate [%]" in stats.index else 0.0
        profit_factor = float(stats.loc["Profit Factor"]) if "Profit Factor" in stats.index else 0.0
        max_dd = float(stats.loc["Max Drawdown [%]"]) if "Max Drawdown [%]" in stats.index else 0.0
        final_val = float(pf.final_value.values[0]) if hasattr(pf.final_value, 'values') else float(pf.final_value())
        
        return {
            "total_trades": total_trades,
            "win_rate": round(win_rate, 2),
            "profit_factor": round(profit_factor, 2),
            "max_drawdown_pct": round(abs(max_dd), 2),
            "avg_hold_bars": 10.0,  # 固定exit後に算出
            "final_equity": round(final_val, 4),
        }
    except Exception as e:
        print(f"    [DETAIL] VectorBT stats parse error: {e}")
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "max_drawdown_pct": 0.0,
            "avg_hold_bars": 0.0,
            "final_equity": 1.0,
        }


# ── メインバックテスト関数 ───────────────────────────────────
def run_usdjpy_mtf_v2(
    ticker: str = "USDJPY=X",
    years: int = 5,
) -> None:
    """USDJPY MTF v2 バックテストを全セッションで実行し結果を表示。"""
    print("=" * 60)
    print(f"  USDJPY MTF v2 バックテスト （{years}年）")
    print("=" * 60)

    # データ取得
    df_multi = fetch_multi_tf(ticker, years=years)
    
    print("\n[INFO] データ前処理: JST変換 + ffill() 処理中...")
    
    # ========== NaN対策 & JST変換 ==========
    
    # 1. Index を DatetimeIndex に変換（parquet から読み込んだ場合のため）
    if not isinstance(df_multi.index, pd.DatetimeIndex):
        df_multi.index = pd.DatetimeIndex(df_multi.index)
    
    # 2. UTC -> JST 変換（Polygonはデフォルトで UTC）
    if hasattr(df_multi.index, 'tz') and df_multi.index.tz is not None:
        df_multi.index = df_multi.index.tz_convert('Asia/Tokyo')
    else:
        # tz-naive の場合は UTC と仮定して変換
        df_multi.index = df_multi.index.tz_localize('UTC').tz_convert('Asia/Tokyo')
    
    # 2. 各時間枠を分離して ffill() 処理
    # signals.py は以下の列プレフィックスを期待: 5M_, 15M_, 1H_, 4H_, D_
    tf_prefixes = ['5M', '15M', '1H', '4H', 'D']
    print(f"  処理対象TF: {tf_prefixes}")
    processed_dfs = []
    
    for prefix in tf_prefixes:
        # 該当プレフィックスの列を抽出
        cols = [c for c in df_multi.columns if c.startswith(f"{prefix}_")]
        if not cols:
            continue
        
        df_tf = df_multi[cols].copy()
        # ffill() で欠損値を前方埋め（各時間枠は独立してffill）
        df_tf = df_tf.ffill()
        processed_dfs.append(df_tf)
    
    # 3. 再結合
    if processed_dfs:
        df_multi = pd.concat(processed_dfs, axis=1)
        print(f"  処理完了: shape={df_multi.shape}, 期間={df_multi.index.min()} ~ {df_multi.index.max()}")
    else:
        print("  [ERROR] 有効な時間枠データが見つかりません")
        return
    
    # ========== バックテスト実行 =========="

    sessions = ["tokyo", "london", "ny", "all"]
    results: Dict[str, Dict[str, Any]] = {}

    for sess in sessions:
        print(f"\n--- セッション: {sess.upper()} ---")
        # シグナル生成
        entries = mtf_minato_short_v2(df_multi, session=sess)
        n_signals = int(entries.sum())
        print(f"  シグナル数: {n_signals}")

        if n_signals == 0:
            results[sess] = {
                "total_trades": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "max_drawdown_pct": 0.0,
                "avg_hold_bars": 0,
                "final_equity": 1.0,
            }
            print("  → トレードなし")
            continue

        # close 列を取得（最も細かい時間枠の Close を使用）
        # 優先順位: 5M_Close > 15M_Close > 1H_Close > 4H_Close > D_Close
        close = None
        for col_candidate in ["5M_Close", "15M_Close", "1H_Close", "4H_Close", "D_Close"]:
            if col_candidate in df_multi.columns:
                close = df_multi[col_candidate].copy()
                print(f"  価格データ: {col_candidate} を使用")
                break
        
        if close is None or close.empty:
            print("  [ERROR] Close列が見つかりません")
            continue

        # バックテスト実行
        if HAS_VBT:
            print("  [vectorbt で実行]")
            res = _vbt_backtest(close, entries)
        else:
            print("  [自前シミュレーションで実行（pip install vectorbt で高精度版に切替可能）]")
            res = _simple_backtest(close, entries)

        results[sess] = res

        print(f"  トレード数:       {res['total_trades']}")
        print(f"  勝率:             {res['win_rate']:.1f}%")
        print(f"  Profit Factor:    {res['profit_factor']}")
        print(f"  最大DD:           {res['max_drawdown_pct']:.2f}%")
        print(f"  平均保有バー数:   {res['avg_hold_bars']}")
        print(f"  最終エクイティ:   {res['final_equity']}")

    # サマリ
    print("\n" + "=" * 60)
    print("  セッション別サマリ")
    print("=" * 60)
    summary = pd.DataFrame(results).T
    summary.index.name = "Session"
    print(summary.to_string())

    # 先行エントリー成功率（ストップ狩り回避率）の概算
    # 全セッション合計のうち early entry が何割を占めるか
    all_entries = mtf_minato_short_v2(df_multi, session="all")
    total_sigs = int(all_entries.sum())
    if total_sigs > 0:
        vol_15m = df_multi.get("15M_Volume", pd.Series(0, index=df_multi.index))
        avg_vol = vol_15m.rolling(5).mean()
        early_mask = (vol_15m > avg_vol * 2) & all_entries
        early_pct = int(early_mask.sum()) / total_sigs * 100
        print(f"\n  先行エントリー率（ストップ狩り逆利用）: {early_pct:.1f}%")

    print("\n完了！ これを src/ に保存して python src/backtest.py で回してみて！")


def run_usdjpy_mtf_v2_advanced(
    df_path: str = "data/raw/usdjpy_multi_tf_2years.parquet",
    lot_size: float = 1.0,
    risk_percent: float = 0.5,
) -> None:
    """
    MTF v2 Advanced バックテスト（Polygon無料2年データ対応）
    
    テンプレート要件:
    - 4H優位性（3波構造）＋日足トレンドON/OFF比較
    - ロング/ショート別集計
    - MaxDD 10%超で警告
    - 期待値・PF・勝率をセッション別に出力
    
    Args:
        df_path: parquetファイルパス（相対パスの場合はプロジェクトルートからの相対）
        lot_size: 1Lot = 10万通貨
        risk_percent: 1トレードあたり資金の何%リスクを取るか
    """
    print("=" * 70)
    print("  USDJPY MTF v2 Advanced バックテスト")
    print("=" * 70)
    print(f"データ: {df_path}")
    print(f"Lotサイズ: {lot_size} (10万通貨)")
    print(f"リスク: {risk_percent}%")
    print("=" * 70)
    
    # ========== データ読み込み＋前処理 ==========
    # パスがプロジェクトルートからの相対パスの場合は絶対パスに変換
    from pathlib import Path
    df_path_obj = Path(df_path)
    if not df_path_obj.is_absolute():
        # プロジェクトルート（REX_Trade_System）を基準にする
        project_root = Path(__file__).resolve().parent.parent
        df_path_obj = project_root / df_path
    
    if not df_path_obj.exists():
        print(f"\n[ERROR] ファイルが見つかりません: {df_path_obj}")
        print(f"  カレントディレクトリ: {Path.cwd()}")
        print(f"  プロジェクトルート: {Path(__file__).resolve().parent.parent}")
        print("\n[解決方法]")
        print("  1. REX_Trade_System ディレクトリで実行: cd REX_Trade_System && python src/backtest.py")
        print("  2. または絶対パスを指定してください")
        return
    
    print(f"[INFO] 読み込みパス: {df_path_obj}")
    df_multi = pd.read_parquet(df_path_obj)
    print(f"\n[INFO] データ読み込み完了: {df_multi.shape}")
    
    # DatetimeIndex変換
    if not isinstance(df_multi.index, pd.DatetimeIndex):
        df_multi.index = pd.DatetimeIndex(df_multi.index)
    
    # UTC -> JST変換
    if hasattr(df_multi.index, 'tz') and df_multi.index.tz is not None:
        df_multi.index = df_multi.index.tz_convert('Asia/Tokyo')
    else:
        df_multi.index = df_multi.index.tz_localize('UTC').tz_convert('Asia/Tokyo')
    
    print(f"[INFO] JST変換完了: {df_multi.index.min()} ~ {df_multi.index.max()}")
    
    # 各時間枠を分離してffill()
    tf_prefixes = ['5M', '15M', '1H', '4H', 'D']
    processed_dfs = []
    for prefix in tf_prefixes:
        cols = [c for c in df_multi.columns if c.startswith(f'{prefix}_')]
        if cols:
            df_tf = df_multi[cols].copy().ffill()
            processed_dfs.append(df_tf)
    
    df_multi = pd.concat(processed_dfs, axis=1)
    print(f"[INFO] NaN処理完了: total NaN = {df_multi.isna().sum().sum()}")
    
    # ========== セッション別バックテスト ==========
    sessions = ["tokyo", "london", "ny", "all"]
    results_list = []
    
    # VectorBT有無チェック
    if not HAS_VBT:
        print("\n[WARNING] vectorbt未インストール。pip install vectorbt を推奨。")
    
    for sess in sessions:
        print(f"\n{'='*70}")
        print(f"  セッション: {sess.upper()}")
        print(f"{'='*70}")
        
        # シグナル生成（現在は日足ルール常時ON）
        # TODO: signals.pyにuse_daily引数を追加して4H優位性のみもテスト
        entries = mtf_minato_short_v2(df_multi, session=sess)
        n_signals = int(entries.sum())
        
        print(f"  総シグナル数: {n_signals}")
        
        if n_signals == 0:
            results_list.append({
                "セッション": sess.upper(),
                "総トレード数": 0,
                "4H優位性シグナル": 0,
                "Lot数": lot_size,
                "平均利確Pips": 0.0,
                "平均損切Pips": 0.0,
                "2年損益合計(円)": 0,
                "期待値(pips)": 0.0,
                "Profit Factor": 0.0,
                "最大DD(%)": 0.0,
                "勝率(%)": 0.0,
                "ロング勝率(%)": 0.0,
                "ショート勝率(%)": 0.0,
            })
            print("  → トレードなし")
            continue
        
        # 価格データ取得（5M_Closeを使用）
        close = df_multi.get('5M_Close', df_multi.get('15M_Close', df_multi.get('1H_Close')))
        if close is None or close.empty:
            print("  [ERROR] Close列が見つかりません")
            continue
        
        # ========== VectorBT バックテスト ==========
        if HAS_VBT:
            try:
                import vectorbt as vbt
                
                # Portfolio作成
                pf = vbt.Portfolio.from_signals(
                    close=close,
                    entries=entries,
                    exits=None,  # 自動exit（次のエントリーまたは最終日）
                    size=lot_size * 100000,  # 10万通貨 × Lot
                    fees=0.0005,  # 0.05%
                    slippage=0.0002,
                    freq='5T',  # 5分足
                )
                
                stats = pf.stats()
                total_trades = int(stats.get('Total Trades', 0))
                
                # 勝率計算
                win_rate = float(stats.get('Win Rate [%]', 0))
                
                # Profit Factor計算
                total_profit = float(stats.get('Total Profit', 0))
                total_loss = abs(float(stats.get('Total Loss', 0)))
                profit_factor = (total_profit / total_loss) if total_loss > 0 else 0.0
                
                # 最大DD計算
                max_dd = abs(float(stats.get('Max Drawdown [%]', 0)))
                
                # 平均利確/損切Pips（簡易計算: 1pips = 0.01円）
                avg_win_pips = float(stats.get('Avg Winning Trade', 0)) * 100  # 円 -> pips
                avg_loss_pips = abs(float(stats.get('Avg Losing Trade', 0))) * 100
                
                # 2年損益合計（円換算）
                final_value = float(pf.final_value())
                init_value = float(pf.init_cash())
                total_pnl_yen = (final_value - init_value)
                
                # 期待値（Expectancy）
                expectancy = (win_rate / 100.0) * avg_win_pips - ((100 - win_rate) / 100.0) * avg_loss_pips
                
                # ロング/ショート別（現在のsignals.pyはショートのみなので暫定0）
                long_win_rate = 0.0
                short_win_rate = win_rate  # 全てショート扱い
                
                results_list.append({
                    "セッション": sess.upper(),
                    "総トレード数": total_trades,
                    "4H優位性シグナル": n_signals,  # 現状は同じ
                    "Lot数": lot_size,
                    "平均利確Pips": round(avg_win_pips, 2),
                    "平均損切Pips": round(avg_loss_pips, 2),
                    "2年損益合計(円)": int(total_pnl_yen),
                    "期待値(pips)": round(expectancy, 2),
                    "Profit Factor": round(profit_factor, 2),
                    "最大DD(%)": round(max_dd, 2),
                    "勝率(%)": round(win_rate, 2),
                    "ロング勝率(%)": round(long_win_rate, 2),
                    "ショート勝率(%)": round(short_win_rate, 2),
                })
                
                print(f"  トレード数: {total_trades}")
                print(f"  勝率: {win_rate:.2f}%")
                print(f"  期待値: {expectancy:.2f} pips")
                print(f"  Profit Factor: {profit_factor:.2f}")
                print(f"  最大DD: {max_dd:.2f}%")
                
                # MaxDD警告
                if max_dd > 10.0:
                    print(f"  [警告] 最大DD {max_dd:.2f}% が10%を超えています！リスク管理を見直してください。")
                
            except Exception as e:
                print(f"  [ERROR] VectorBT計算エラー: {e}")
                results_list.append({
                    "セッション": sess.upper(),
                    "総トレード数": n_signals,
                    "4H優位性シグナル": n_signals,
                    "Lot数": lot_size,
                    "平均利確Pips": 0.0,
                    "平均損切Pips": 0.0,
                    "2年損益合計(円)": 0,
                    "期待値(pips)": 0.0,
                    "Profit Factor": 0.0,
                    "最大DD(%)": 0.0,
                    "勝率(%)": 0.0,
                    "ロング勝率(%)": 0.0,
                    "ショート勝率(%)": 0.0,
                })
        else:
            # VectorBT未インストール時の簡易計算
            results_list.append({
                "セッション": sess.upper(),
                "総トレード数": n_signals,
                "4H優位性シグナル": n_signals,
                "Lot数": lot_size,
                "平均利確Pips": 0.0,
                "平均損切Pips": 0.0,
                "2年損益合計(円)": 0,
                "期待値(pips)": 0.0,
                "Profit Factor": 0.0,
                "最大DD(%)": 0.0,
                "勝率(%)": 0.0,
                "ロング勝率(%)": 0.0,
                "ショート勝率(%)": 0.0,
            })
    
    # ========== 結果出力（Markdownテーブル） ==========
    print("\n" + "=" * 70)
    print("  バックテスト結果サマリ")
    print("=" * 70)
    
    df_results = pd.DataFrame(results_list)
    
    # Markdownテーブル出力
    try:
        print("\n" + df_results.to_markdown(index=False))
    except (AttributeError, ImportError):
        # pandas < 1.0 または tabulate未インストールの場合は通常の表形式
        print("\n" + df_results.to_string(index=False))
        print("\n[TIP] Markdownテーブル出力には pip install tabulate が必要です")
    
    # ========== 総合評価 ==========
    print("\n" + "=" * 70)
    print("  総合評価")
    print("=" * 70)
    
    # ALL セッションの結果を取得
    all_result = df_results[df_results['セッション'] == 'ALL']
    if not all_result.empty:
        expectancy_all = all_result['期待値(pips)'].values[0]
        pf_all = all_result['Profit Factor'].values[0]
        max_dd_all = all_result['最大DD(%)'].values[0]
        
        print(f"\n  期待値: {expectancy_all:.2f} pips")
        if expectancy_all >= 5.0:
            print("  -> [OK] 期待値+5pips以上！裁量で狙う価値あり")
        else:
            print("  -> [NG] 期待値が低い。ルール見直し推奨")
        
        print(f"\n  Profit Factor: {pf_all:.2f}")
        if pf_all >= 1.5:
            print("  -> [OK] PF 1.5以上！長期的にプラス期待")
        else:
            print("  -> [NG] PF低い。リスクリワード改善が必要")
        
        print(f"\n  最大DD: {max_dd_all:.2f}%")
        if max_dd_all > 10.0:
            print("  -> [警告] MaxDD 10%超え。一気に吐き出すリスク大")
        else:
            print("  -> [OK] MaxDD 10%以内。リスク管理良好")
    
    print("\n" + "=" * 70)
    print("  完了！")
    print("=" * 70)
    print("\n[次のステップ]")
    print("1. signals.py に use_daily 引数を追加（4H優位性のみ vs 日足ルール追加の比較）")
    print("2. exit_pips 計算を追加（利確/損切の実Pipsを正確に算出）")
    print("3. ロング/ショート別エントリーロジックを実装")
    print("\nボス、結果見てMaxDDや期待値がどうだったか教えてね！")


if __name__ == "__main__":
    # 新しいAdvanced版を実行
    run_usdjpy_mtf_v2_advanced(
        df_path="data/raw/usdjpy_multi_tf_2years.parquet",
        lot_size=1.0,
        risk_percent=0.5
    )

