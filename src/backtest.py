"""backtest.py — USDJPY MTF v2 バックテスト（#011 統合レンジロジック版）。

python src/backtest.py で実行。

変更履歴:
  Phase A: swing_detector.py 追加・Long/Short分岐骨格
  Phase B: entry_logic.py 追加・3段階エントリー条件実装（1H DB）
  #007: 指値エントリー + 2段階 SL
  #009: 15M DB + 5M DB エントリーに全面再設計
        exit_logic.py 統合（フェーズ別決済）
        デバッグ出力 a/b/c/d/e 追加
  #011: check_15m_range_low() 統合（DB/IHS/ASCENDING）
        4H Swing 幅ガード追加
        デバッグ出力 f/g/h/i 追加（パターン別勝率）
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Windows cp932 端末でも日本語・特殊文字を出力できるよう UTF-8 に強制
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd

_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.swing_detector import (
    _build_direction_5m,
    get_nearest_swing_high,
    get_nearest_swing_low,
)
from src.entry_logic import MAX_REENTRY, MIN_4H_SWING_PIPS, WICKTOL_PIPS, DIRECTION_MODE, evaluate_entry
from src.exit_logic import manage_exit

try:
    import vectorbt as vbt
    HAS_VBT = True
except ImportError:
    HAS_VBT = False


# ── 定数 ──────────────────────────────────────────────────────
LONG_LOT_MULTIPLIER  = 1.0
SHORT_LOT_MULTIPLIER = 1.0
WARMUP_BARS = 1728
# 計算根拠: 4H足 lookback=30 → 30本 × 4時間 × 12本/時間(5M) = 1,440本
# 安全マージンとして 4H足 n=3 分を加算 → 30 * 48 + 3 * 48 = 1,584 → 切り上げ 1,728（120日相当）


# ── データ読み込みヘルパー ─────────────────────────────────────
def _load_and_preprocess(
    df_path: str = "data/raw/usdjpy_multi_tf_2years.parquet",
) -> pd.DataFrame:
    """Parquet データを読み込み、UTC→JST 変換・ffill 前処理を行う。"""
    df_path_obj = Path(df_path)
    if not df_path_obj.is_absolute():
        project_root = Path(__file__).resolve().parent.parent
        df_path_obj = project_root / df_path

    if not df_path_obj.exists():
        raise FileNotFoundError(
            f"データファイルが見つかりません: {df_path_obj}\n"
            f"  → python src/data_fetch.py を先に実行してください"
        )

    df_multi = pd.read_parquet(df_path_obj)

    if not isinstance(df_multi.index, pd.DatetimeIndex):
        df_multi.index = pd.DatetimeIndex(df_multi.index)

    if hasattr(df_multi.index, "tz") and df_multi.index.tz is not None:
        df_multi.index = df_multi.index.tz_convert("Asia/Tokyo")
    else:
        df_multi.index = df_multi.index.tz_localize("UTC").tz_convert("Asia/Tokyo")

    tf_prefixes = ["5M", "15M", "1H", "4H", "D"]
    processed_dfs = []
    for prefix in tf_prefixes:
        cols = [c for c in df_multi.columns if c.startswith(f"{prefix}_")]
        if cols:
            processed_dfs.append(df_multi[cols].copy().ffill())

    return pd.concat(processed_dfs, axis=1)


# ── 全バースキャン：エントリーイベント収集 ────────────────────────
def _scan_all_bars_for_entry(
    df_multi: pd.DataFrame,
    df_5m_raw: pd.DataFrame,
    direction_series: pd.Series,
    df_4h_full: pd.DataFrame,
    df_1h_full: pd.DataFrame,
    df_15m_full: pd.DataFrame,
) -> tuple[List[dict], dict]:
    """全 5M バーを走査してエントリーイベントを収集する（#009 新ロジック）。

    Returns:
        entry_events: list of dict
            {bar_idx, direction, entry_price, neck_1h, neck_4h, fib_score, timestamp}
        debug_a: dict
            {db_15m_found, db_5m_confirmed, wicktol_invalid}
    """
    ts_4h  = df_4h_full.index.values
    ts_1h  = df_1h_full.index.values
    ts_15m = df_15m_full.index.values
    ts_5m  = df_multi.index.values

    n_bars = len(df_multi)
    warmup = WARMUP_BARS

    reentry_count_long  = 0
    reentry_count_short = 0
    last_sl_long   = float("nan")
    last_sh_short  = float("nan")

    entry_events: List[dict] = []
    debug_a = {
        'db_15m_found': 0, 'db_5m_confirmed': 0, 'wicktol_invalid': 0,
        'swing_guard_skip': 0, 'sl3_over_skip': 0, 'swing_none_skip': 0,
    }

    print(f"  [INFO] {n_bars} 本のバーをスキャン中（warm-up {warmup} 本スキップ）...")

    skip_counts: Dict[str, int] = {}

    for i in range(warmup, n_bars - 1):
        ts = ts_5m[i]
        direction = direction_series.iloc[i]

        if direction == "NONE":
            skip_counts['NONE方向'] = skip_counts.get('NONE方向', 0) + 1
            continue

        idx_4h  = int(np.searchsorted(ts_4h,  ts, side="right")) - 1
        idx_1h  = int(np.searchsorted(ts_1h,  ts, side="right")) - 1
        idx_15m = int(np.searchsorted(ts_15m, ts, side="right")) - 1

        if idx_4h < 10 or idx_1h < 6 or idx_15m < 6:
            skip_counts['データ不足'] = skip_counts.get('データ不足', 0) + 1
            continue

        sh_4h = get_nearest_swing_high(df_4h_full["High"], idx_4h, n=3, lookback=20)
        sl_4h = get_nearest_swing_low(df_4h_full["Low"],   idx_4h, n=3, lookback=20)

        # ── 4H Swing None チェック（フォールバック修正後の対応）──
        # None のまま再エントリー管理の演算に渡すと TypeError になるため早期スキップ
        if sh_4h is None or sl_4h is None:
            debug_a['swing_none_skip'] += 1
            skip_counts['4H Swing 未検出(None)'] = skip_counts.get('4H Swing 未検出(None)', 0) + 1
            continue

        # 再エントリー管理
        if direction == "LONG":
            if not np.isnan(last_sl_long) and abs(sl_4h - last_sl_long) > (sh_4h - sl_4h) * 0.05:
                reentry_count_long = 0
                last_sl_long = sl_4h
            elif np.isnan(last_sl_long):
                last_sl_long = sl_4h
            if reentry_count_long > MAX_REENTRY:
                skip_counts['再エントリー上限'] = skip_counts.get('再エントリー上限', 0) + 1
                continue
        else:
            if not np.isnan(last_sh_short) and abs(sh_4h - last_sh_short) > (sh_4h - sl_4h) * 0.05:
                reentry_count_short = 0
                last_sh_short = sh_4h
            elif np.isnan(last_sh_short):
                last_sh_short = sh_4h
            if reentry_count_short > MAX_REENTRY:
                skip_counts['再エントリー上限'] = skip_counts.get('再エントリー上限', 0) + 1
                continue

        neck_4h = sh_4h if direction == "LONG" else sl_4h

        # 15M window
        low_15m_w  = df_15m_full["Low"].iloc[:idx_15m + 1]
        high_15m_w = df_15m_full["High"].iloc[:idx_15m + 1]

        # 5M window（直近20本）
        lo = max(0, i - 20)
        low_5m_w   = df_5m_raw["Low"].iloc[lo:i + 1]
        high_5m_w  = df_5m_raw["High"].iloc[lo:i + 1]
        close_5m_w = df_5m_raw["Close"].iloc[lo:i + 1]
        open_5m_w  = df_5m_raw["Open"].iloc[lo:i + 1]

        current_price = float(df_5m_raw["Close"].iloc[i])

        result = evaluate_entry(
            price=current_price,
            direction=direction,
            swing_high_4h=sh_4h,
            swing_low_4h=sl_4h,
            neck_4h=neck_4h,
            low_15m=low_15m_w,
            high_15m=high_15m_w,
            close_5m=close_5m_w,
            open_5m=open_5m_w,
            low_5m=low_5m_w,
            high_5m=high_5m_w,
        )

        # デバッグ a カウント
        if result.get('swing_guard_skip'):
            debug_a['swing_guard_skip'] += 1
        if result.get('sl3_over_skip'):
            debug_a['sl3_over_skip'] += 1
        if result['db_15m_found']:
            debug_a['db_15m_found'] += 1
        if result['wicktol_invalid']:
            debug_a['wicktol_invalid'] += 1
        if not result['enter']:
            skip_counts[result['reason']] = skip_counts.get(result['reason'], 0) + 1
            continue

        debug_a['db_5m_confirmed'] += 1

        # 1H ネックライン取得（エントリー時点）
        if direction == "LONG":
            neck_1h = get_nearest_swing_high(df_1h_full["High"], idx_1h, n=3, lookback=50)
        else:
            neck_1h = get_nearest_swing_low(df_1h_full["Low"], idx_1h, n=3, lookback=50)

        # 1H Swing 未検出の場合はエントリースキップ（exit_logic が None で演算クラッシュするため）
        if neck_1h is None:
            skip_counts['1H neck 未検出(None)'] = skip_counts.get('1H neck 未検出(None)', 0) + 1
            continue

        # エントリーイベント登録（次の 5M 始値）
        entry_price = float(df_5m_raw["Open"].iloc[i + 1])
        entry_ts    = df_multi.index[i + 1]

        entry_events.append({
            'bar_idx'    : i + 1,
            'direction'  : direction,
            'entry_price': entry_price,
            'neck_1h'    : neck_1h,
            'neck_4h'    : neck_4h,
            'fib_score'  : result['fib_score'],
            'timestamp'  : entry_ts,
            'pattern'    : result.get('pattern', ''),
        })

        # ── Swing 可視化 PNG 自動保存（Phase 1）──
        try:
            from src.plotter import plot_swing_check
            from pathlib import Path as _Path
            _plots_dir = _Path(__file__).resolve().parents[1] / "logs" / "plots"
            _plots_dir.mkdir(parents=True, exist_ok=True)
            _fname = f"{entry_ts.strftime('%Y%m%d_%H%M')}_{direction}_swing.png"
            plot_swing_check(
                df_5m   = df_5m_raw,
                df_4h   = df_4h_full,
                df_15m  = df_15m_full,
                center_time = entry_ts,
                direction   = direction,
                save_path   = str(_plots_dir / _fname),
                sh_4h   = sh_4h,
                sl_4h   = sl_4h,
            )
        except Exception as _e:
            print(f"    [WARN] plot_swing_check failed: {_e}")

        if direction == "LONG":
            reentry_count_long += 1
        else:
            reentry_count_short += 1

    print("\n  スキップ理由の内訳:")
    for reason, count in sorted(skip_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"    {reason}: {count}件")

    return entry_events, debug_a


# ── ポジション状態機械シミュレーション ────────────────────────────
def _simulate_trades_mtf(
    entry_events: List[dict],
    df_5m: pd.DataFrame,
    df_15m: pd.DataFrame,
    df_1h: pd.DataFrame,
) -> tuple[List[dict], dict]:
    """フェーズ別決済ロジックで全エントリーをシミュレーションする。

    Returns:
        trades: list of trade dict
        debug_bcd: dict (b/c/d デバッグ統計)
    """
    if not entry_events:
        return [], {'pre_1h': 0, 'pre_4h': 0, 'post_4h': 0,
                    'neck_1h_reached': 0, 'neck_4h_reached': 0}

    # バーインデックス順にソート
    events_by_bar: Dict[int, dict] = {e['bar_idx']: e for e in entry_events}

    trades: List[dict] = []
    debug_bcd = {'pre_1h': 0, 'pre_4h': 0, 'post_4h': 0,
                 'neck_1h_reached': 0, 'neck_4h_reached': 0}

    in_pos = False
    position: dict = {}

    n_bars = len(df_5m)

    for i in range(n_bars):
        if in_pos:
            result = manage_exit(
                position=position,
                bar_5m_idx=i,
                df_5m=df_5m,
                df_15m=df_15m,
                df_1h=df_1h,
            )

            # フェーズ遷移を反映
            old_phase = position['exit_phase']
            new_phase = result['new_phase']
            if new_phase != old_phase:
                position['exit_phase'] = new_phase
                if new_phase == 'pre_4h':
                    debug_bcd['neck_1h_reached'] += 1
                elif new_phase == 'post_4h':
                    debug_bcd['neck_4h_reached'] += 1

            position['swing_confirmed_5m'] = result['new_swing_confirmed']

            if result['action'] in ('exit_all', 'exit_half'):
                direction  = position['direction']
                ep         = position['entry_price']
                exit_price = float(df_5m['Close'].iloc[i])

                if direction == 'LONG':
                    pnl_pips = (exit_price - ep) * 100
                else:
                    pnl_pips = (ep - exit_price) * 100

                exit_phase_at_close = position['exit_phase']
                trades.append({
                    'entry_bar'  : position['entry_bar'],
                    'exit_bar'   : i,
                    'direction'  : direction,
                    'entry_price': ep,
                    'exit_price' : exit_price,
                    'pnl_pips'   : pnl_pips,
                    'exit_reason': result['reason'],
                    'exit_phase' : exit_phase_at_close,
                    'hold_bars'  : i - position['entry_bar'],
                    'fib_score'  : position.get('fib_score', 0),
                    'pattern'    : position.get('entry_pattern', ''),
                })
                debug_bcd[exit_phase_at_close] = debug_bcd.get(exit_phase_at_close, 0) + 1

                if result['action'] == 'exit_all':
                    in_pos = False
                else:
                    # exit_half: ポジション継続（半値決済済みフラグのみ）
                    position['half_exited'] = True

        # 新規エントリー（ポジションなしの場合のみ）
        if not in_pos and i in events_by_bar:
            ev = events_by_bar[i]
            position = {
                'direction'          : ev['direction'],
                'entry_price'        : ev['entry_price'],
                'entry_bar'          : i,
                'neck_1h'            : ev['neck_1h'],
                'neck_4h'            : ev['neck_4h'],
                'exit_phase'         : 'pre_1h',
                'half_exited'        : False,
                'swing_confirmed_5m' : False,
                'fib_score'          : ev['fib_score'],
                'entry_pattern'      : ev.get('pattern', ''),
            }
            in_pos = True

    # 未決済ポジションを最終バーで強制決済
    if in_pos:
        direction  = position['direction']
        ep         = position['entry_price']
        exit_price = float(df_5m['Close'].iloc[-1])
        if direction == 'LONG':
            pnl_pips = (exit_price - ep) * 100
        else:
            pnl_pips = (ep - exit_price) * 100
        trades.append({
            'entry_bar'  : position['entry_bar'],
            'exit_bar'   : n_bars - 1,
            'direction'  : direction,
            'entry_price': ep,
            'exit_price' : exit_price,
            'pnl_pips'   : pnl_pips,
            'exit_reason': 'FINAL_BAR',
            'exit_phase' : position['exit_phase'],
            'hold_bars'  : n_bars - 1 - position['entry_bar'],
            'fib_score'  : position.get('fib_score', 0),
            'pattern'    : position.get('entry_pattern', ''),
        })

    return trades, debug_bcd


# ── 結果集計 ────────────────────────────────────────────────────
def _calc_stats(trades: List[dict]) -> Dict[str, Any]:
    if not trades:
        return {
            'total_trades': 0, 'long_trades': 0, 'short_trades': 0,
            'win_rate': 0.0, 'long_win_rate': 0.0, 'short_win_rate': 0.0,
            'profit_factor': 0.0, 'max_drawdown_pips': 0.0,
            'avg_hold_bars': 0, 'total_pnl_pips': 0.0,
        }

    df_t   = pd.DataFrame(trades)
    df_l   = df_t[df_t['direction'] == 'LONG']
    df_s   = df_t[df_t['direction'] == 'SHORT']
    wins   = df_t[df_t['pnl_pips'] > 0]
    losses = df_t[df_t['pnl_pips'] <= 0]

    gp = float(wins['pnl_pips'].sum())   if len(wins)   else 0.0
    gl = float(losses['pnl_pips'].sum()) if len(losses) else 0.0
    pf = abs(gp / gl) if gl != 0 else float('inf')

    cum_pnl     = df_t['pnl_pips'].cumsum()
    running_max = cum_pnl.cummax()
    max_dd      = float((running_max - cum_pnl).max()) if len(cum_pnl) else 0.0

    def _wr(df):
        return float((df['pnl_pips'] > 0).sum() / len(df) * 100) if len(df) else 0.0

    return {
        'total_trades'      : len(trades),
        'long_trades'       : len(df_l),
        'short_trades'      : len(df_s),
        'win_rate'          : round(float(len(wins) / len(trades) * 100), 2),
        'long_win_rate'     : round(_wr(df_l), 2),
        'short_win_rate'    : round(_wr(df_s), 2),
        'profit_factor'     : round(pf, 2),
        'max_drawdown_pips' : round(max_dd, 2),
        'avg_hold_bars'     : round(float(df_t['hold_bars'].mean()), 1),
        'total_pnl_pips'    : round(float(df_t['pnl_pips'].sum()), 2),
    }


# ── メインバックテスト関数（#009 版） ─────────────────────────────
def run_rex_mtf_backtest(
    df_path: str = "data/raw/usdjpy_multi_tf_2years.parquet",
    lot_size: float = 1.0,
) -> None:
    """ミナト流 MTF バックテスト（#009 — 15M DB + 5M DB エントリー）。"""
    t0 = time.time()

    print("=" * 70)
    print("  REX MTF Backtest #011 (統合レンジロジック + 4H Swing ガード)")
    print("=" * 70)
    print(f"データ: {df_path}")
    print(f"DIRECTION_MODE: {DIRECTION_MODE}  |  WARMUP_BARS: {WARMUP_BARS}")
    print(f"WICKTOL_PIPS: {WICKTOL_PIPS}  |  MIN_4H_SWING_PIPS: {MIN_4H_SWING_PIPS}  |  Lot: {lot_size}")
    print("=" * 70)

    # ── Step 1: データ読み込み ──
    print("\n[STEP 1] データ読み込み + 前処理...")
    df_multi = _load_and_preprocess(df_path)
    n_bars = len(df_multi)
    print(f"  完了: {df_multi.shape}, 期間={df_multi.index.min()} ~ {df_multi.index.max()}")

    df_5m_raw = df_multi[["5M_High", "5M_Low", "5M_Open", "5M_Close"]].rename(
        columns={"5M_High": "High", "5M_Low": "Low",
                 "5M_Open": "Open", "5M_Close": "Close"}
    )

    # ── Step 2: resample（一括プリコンピュート） ──
    print("\n[STEP 2] 4H/1H/15M resample中...")
    df_4h_full = df_5m_raw.resample("4h").agg(
        {"High": "max", "Low": "min", "Open": "first", "Close": "last"}
    ).dropna()
    df_1h_full = df_5m_raw.resample("1h").agg(
        {"High": "max", "Low": "min", "Open": "first", "Close": "last"}
    ).dropna()
    df_15m_full = df_5m_raw.resample("15min").agg(
        {"High": "max", "Low": "min", "Open": "first", "Close": "last"}
    ).dropna()
    print(f"  4H: {len(df_4h_full)}本, 1H: {len(df_1h_full)}本, 15M: {len(df_15m_full)}本")

    # ── Step 3: 4H 方向プリコンピュート ──
    print("\n[STEP 3] 4H 方向プリコンピュート...")
    direction_series = _build_direction_5m(df_5m_raw, n=3, lookback=20)
    dir_counts = direction_series.value_counts()
    print(f"  方向分布: LONG={dir_counts.get('LONG', 0)}, SHORT={dir_counts.get('SHORT', 0)}, NONE={dir_counts.get('NONE', 0)}")

    # ── Step 4: エントリースキャン ──
    print("\n[STEP 4] エントリースキャン（15M DB + 5M DB）...")
    entry_events, debug_a = _scan_all_bars_for_entry(
        df_multi, df_5m_raw, direction_series,
        df_4h_full, df_1h_full, df_15m_full,
    )

    n_long  = sum(1 for e in entry_events if e['direction'] == 'LONG')
    n_short = sum(1 for e in entry_events if e['direction'] == 'SHORT')
    print(f"\n  エントリー件数: LONG={n_long}件, SHORT={n_short}件")

    if not entry_events:
        print("\n  [WARNING] エントリーが 0 件です。パラメータを確認してください。")
        return

    # ── Step 5: シミュレーション ──
    print("\n[STEP 5] フェーズ別決済シミュレーション...")
    trades, debug_bcd = _simulate_trades_mtf(
        entry_events, df_5m_raw, df_15m_full, df_1h_full
    )

    res     = _calc_stats(trades)
    elapsed = time.time() - t0

    # ── 結果出力 ──
    print("\n" + "=" * 70)
    print("  バックテスト結果サマリ")
    print("=" * 70)
    print(f"\n  総トレード数:         {res['total_trades']}")
    print(f"  うち Long:            {res['long_trades']}")
    print(f"  うち Short:           {res['short_trades']}")
    print(f"\n  全体勝率:             {res['win_rate']:.2f}%")
    print(f"  Long 勝率:            {res['long_win_rate']:.2f}%")
    print(f"  Short 勝率:           {res['short_win_rate']:.2f}%")
    print(f"\n  Profit Factor:        {res['profit_factor']}")
    print(f"  最大 DD (pips):       {res['max_drawdown_pips']:.2f}")
    print(f"  総損益 (pips):        {res['total_pnl_pips']:.2f}")
    print(f"  平均保有バー数:       {res['avg_hold_bars']}")

    # ── デバッグ出力 a/b/c/d/e ──
    total_entries = len(entry_events)
    print("\n" + "=" * 70)
    print("  デバッグ出力")
    print("=" * 70)

    print(f"\n[a] エントリー件数の内訳")
    print(f"    15M DB 検出件数:              {debug_a['db_15m_found']}")
    print(f"    5M DB 確定件数 (実エントリー): {debug_a['db_5m_confirmed']}")
    print(f"    WICKTOL 超過で無効化:          {debug_a['wicktol_invalid']}")

    print(f"\n[b] exit_phase 別の決済件数")
    print(f"    pre_1h  フェーズ (15M/5M ダウ崩れ): {debug_bcd.get('pre_1h', 0)}件")
    print(f"    pre_4h  フェーズ (5M ダウ崩れ):     {debug_bcd.get('pre_4h', 0)}件")
    print(f"    post_4h フェーズ (15M ダウ崩れ):    {debug_bcd.get('post_4h', 0)}件")

    neck1h_rate = debug_bcd['neck_1h_reached'] / max(total_entries, 1) * 100
    print(f"\n[c] 1H ネック到達率:  {debug_bcd['neck_1h_reached']}/{total_entries} = {neck1h_rate:.1f}%")

    neck4h_rate = debug_bcd['neck_4h_reached'] / max(total_entries, 1) * 100
    print(f"\n[d] 4H ネック + 1H 実体確定率:  {debug_bcd['neck_4h_reached']}/{total_entries} = {neck4h_rate:.1f}%")

    print(f"\n[e] WICKTOL_PIPS 現在設定値:  {WICKTOL_PIPS} pips")

    # ── デバッグ出力 f/g/h/i ──
    _all_patterns_long  = ['DB', 'IHS', 'ASCENDING']
    _all_patterns_short = ['DT', 'HNS', 'DESCENDING']
    _all_patterns = _all_patterns_long + _all_patterns_short

    df_t = pd.DataFrame(trades) if trades else pd.DataFrame()

    print(f"\n[f] パターン別エントリー件数")
    if len(df_t) > 0 and 'pattern' in df_t.columns:
        pat_counts = df_t['pattern'].value_counts()
        for p in _all_patterns:
            cnt = int(pat_counts.get(p, 0))
            pct = cnt / len(df_t) * 100
            if cnt > 0:
                print(f"    {p:12s}: {cnt:3d} 件 ({pct:.1f}%)")
    else:
        print("    (データなし)")

    print(f"\n[g] 4H Swing 関連スキップ件数")
    print(f"    4H Swing 未検出（None）スキップ : {debug_a['swing_none_skip']} 件")
    print(f"    4H Swing 幅不足スキップ         : {debug_a['swing_guard_skip']} 件（< {MIN_4H_SWING_PIPS:.0f} pips）")

    print(f"\n[h] SL3/SH3 上限超過によるスキップ件数")
    print(f"    {debug_a['sl3_over_skip']} 件スキップ（等距離ルール違反）")

    print(f"\n[i] パターン別 勝率・平均損益")
    if len(df_t) > 0 and 'pattern' in df_t.columns:
        for p in _all_patterns:
            pt = df_t[df_t['pattern'] == p]
            if len(pt) == 0:
                continue
            wr  = float((pt['pnl_pips'] > 0).sum() / len(pt) * 100)
            avg = float(pt['pnl_pips'].mean())
            print(f"    {p:12s}: 勝率 {wr:5.1f}%  平均 {avg:+6.1f} pips  ({len(pt)} 件)")
    else:
        print("    (データなし)")

    print(f"\n[j] 実行モード")
    print(f"    DIRECTION_MODE : {DIRECTION_MODE}")
    print(f"    WARMUP_BARS    : {WARMUP_BARS} 本スキップ（データ冒頭 120 日相当）")
    effective_bars = n_bars - WARMUP_BARS
    print(f"    有効バー数      : {effective_bars:,} 本 / {n_bars:,} 本中")

    print(f"\n  実行時間: {elapsed:.1f}秒")

    # ── 総合評価 ──
    print("\n" + "=" * 70)
    print("  総合評価")
    print("=" * 70)

    avg_pnl = res['total_pnl_pips'] / max(res['total_trades'], 1)
    print(f"\n  期待値(pips/trade): {avg_pnl:.2f}")
    if avg_pnl >= 5.0:
        print("  → [OK] 期待値 +5pips 以上")
    else:
        print("  → [NG] 期待値が低い。ルール見直し推奨")

    pf = res['profit_factor']
    if pf >= 1.5:
        print(f"\n  → [OK] PF {pf:.2f} — 1.5 以上")
    else:
        print(f"\n  → [NG] PF {pf:.2f} — 低い")

    max_dd = res['max_drawdown_pips']
    if max_dd > 300.0:
        print(f"\n  → [警告] MaxDD {max_dd:.1f}pips — 300 超え")
    else:
        print(f"\n  → [OK] MaxDD {max_dd:.1f}pips")

    print("\n" + "=" * 70)
    print("  [次のステップ]")
    print("  ・デバッグ i のパターン別勝率を確認 → DB/IHS/ASCENDING の差を評価")
    print("  ・WICKTOL_PIPS: 0.0 → 5.0 → 10.0 の順でテスト")
    print("  ・MIN_4H_SWING_PIPS の調整検討（デバッグ g 件数を参考に）")
    print("=" * 70)
    print("\nボス、結果を確認してください！")


# ── 後方互換スタブ ────────────────────────────────────────────────
def run_usdjpy_mtf_v2(*args, **kwargs) -> None:
    print("[WARNING] run_usdjpy_mtf_v2 は旧バージョンです。run_rex_mtf_backtest() を使用してください。")


def run_usdjpy_mtf_v2_advanced(
    df_path: str = "data/raw/usdjpy_multi_tf_2years.parquet",
    lot_size: float = 1.0,
    **kwargs,
) -> None:
    print("[WARNING] run_usdjpy_mtf_v2_advanced は旧バージョンです。")
    run_rex_mtf_backtest(df_path=df_path, lot_size=lot_size)


if __name__ == "__main__":
    run_rex_mtf_backtest(
        df_path="data/raw/usdjpy_multi_tf_2years.parquet",
        lot_size=1.0,
    )
