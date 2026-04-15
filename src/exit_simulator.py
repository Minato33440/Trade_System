"""exit_simulator.py — 決済シミュレーション（#026b）

logs/window_scan_entries.csv（12件）の各エントリーに対して
4段階決済ロジックを適用し、P&L / PF / 勝率 / MaxDD を算出する。

実装方式: 方式B（独自実装）
理由: manage_exit() は neck_1h を半値決済トリガーとするが、
      ADR D-6 では neck_4h が半値決済トリガー（仕様不一致のため方式B採用）。
      また manage_exit() は df_15m / df_1h を分離引数で要求するため
      シミュレーター内での呼び出しコストが高い。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.swing_detector import detect_swing_highs, detect_swing_lows
from src.window_scanner import resample_tf

# ── 定数 ──────────────────────────────────────────────────────────────────────

PIP_SIZE = 0.01
DIRECTION = 'LONG'  # 全エントリー LONG（DB / ASCENDING パターン）

# ── パス ──────────────────────────────────────────────────────────────────────

DATA_PATH   = _repo_root / 'data' / 'raw' / 'usdjpy_multi_tf_2years.parquet'
ENTRIES_CSV = _repo_root / 'logs' / 'window_scan_entries.csv'
OUT_CSV     = _repo_root / 'logs' / 'window_scan_exits.csv'

# ── データ読み込み ─────────────────────────────────────────────────────────────

df_raw = pd.read_parquet(DATA_PATH)
df_5m = df_raw[['5M_Open', '5M_High', '5M_Low', '5M_Close']].rename(
    columns={
        '5M_Open':  'open',
        '5M_High':  'high',
        '5M_Low':   'low',
        '5M_Close': 'close',
    }
).dropna()

entries = pd.read_csv(ENTRIES_CSV)

print(f"Data loaded: 5M={len(df_5m)} bars")
print(f"Entries: {len(entries)} rows")
print(f"Columns: {list(entries.columns)}")


# ── 補助関数 ──────────────────────────────────────────────────────────────────

def check_swing_confirmed_5m(df: pd.DataFrame, idx: int) -> bool:
    """5M SH または SL が確定したかチェック（n=2）"""
    if idx < 5:
        return False
    window = df.iloc[max(0, idx - 10):idx + 1]
    sh = detect_swing_highs(window['high'], n=2)
    sl = detect_swing_lows(window['low'], n=2)
    return bool(sh.any() or sl.any())


def check_5m_dow_break_simple(df: pd.DataFrame, idx: int, direction: str = 'LONG') -> bool:
    """5M ダウ崩れ判定（直近 SL が前回 SL を下回った = LONG）"""
    if idx < 10:
        return False
    window = df.iloc[max(0, idx - 20):idx + 1]
    if direction == 'LONG':
        sl_flags = detect_swing_lows(window['low'], n=2)
        sl_vals = window['low'][sl_flags]
        if len(sl_vals) >= 2:
            return bool(sl_vals.iloc[-1] < sl_vals.iloc[-2])
    return False


def check_15m_dow_break_simple(df: pd.DataFrame, idx: int, direction: str = 'LONG') -> bool:
    """15M ダウ崩れ判定（5M を 15M にリサンプルして直近 SL 比較）"""
    if idx < 30:
        return False
    window_5m = df.iloc[max(0, idx - 60):idx + 1]
    df_15m = resample_tf(window_5m, '15min')
    if len(df_15m) < 10:
        return False
    if direction == 'LONG':
        sl_flags = detect_swing_lows(df_15m['low'], n=3)
        sl_vals = df_15m['low'][sl_flags]
        if len(sl_vals) >= 2:
            return bool(sl_vals.iloc[-1] < sl_vals.iloc[-2])
    return False


def check_1h_close_above_neck(df: pd.DataFrame, idx: int, neck_4h: float) -> bool:
    """1H 足 Close が neck_4h を上抜け確定したか。

    label='right', closed='right' リサンプルでは 1H バーの最終 5M 足は minute==0。
    その足の Close = 1H Close となる。
    """
    ts = df.index[idx]
    if hasattr(ts, 'minute') and ts.minute == 0:
        close_1h = float(df.iloc[idx]['close'])
        return close_1h > neck_4h
    return False


# ── 決済シミュレーション ──────────────────────────────────────────────────────

def simulate_exit(
    df_5m_after: pd.DataFrame,
    entry_price: float,
    neck_4h: float,
    sl_4h: float,  # noqa: ARG001 — 将来のハードストップ用に保持
    direction: str = 'LONG',
) -> dict:
    """4段階決済ロジックを 5M バーごとに適用する。

    ADR D-6 準拠:
      初動SL : 5M Swing 未確定 → 15M ダウ崩れで全量損切
      段階1  : 5M Swing 確定後〜4H neck 未到達 → 5M ダウ崩れで全量決済
      段階2  : 4H neck 到達 → 50% 決済 + 残り建値ストップ
      段階3  : 1H Close > neck_4h 確定 → 15M ダウ崩れで残り全量決済

    全決済は「確定足の次足始値」で執行（data_end を除く）。
    """
    phase = 'initial'
    remaining_qty = 1.0
    total_pnl = 0.0

    n = len(df_5m_after)

    for i, (ts, bar) in enumerate(df_5m_after.iterrows()):

        # ── 初動SL: 5M Swing 未確定中は 15M ダウ崩れで全量損切 ──────────────
        if phase == 'initial':
            if check_swing_confirmed_5m(df_5m_after, i):
                phase = 'stage1'
                # fall through to stage1 block this bar
            else:
                if check_15m_dow_break_simple(df_5m_after, i, direction):
                    next_i = min(i + 1, n - 1)
                    exit_price = float(df_5m_after.iloc[next_i]['open'])
                    pnl = (exit_price - entry_price) / PIP_SIZE
                    return {
                        'exit_price': exit_price,
                        'exit_ts':    df_5m_after.index[next_i],
                        'exit_reason': 'initial_SL_15m_dow',
                        'pnl_pips':   pnl,
                        'exit_phase': 'initial',
                    }
                continue  # 変化なし → 次の足へ

        # ── 段階1: 5M Swing 確定後〜neck_4h 未到達 ───────────────────────────
        if phase == 'stage1':
            # neck_4h 到達 → 50% 決済 + stage2 移行
            if bar['high'] >= neck_4h:
                half_pnl = (neck_4h - entry_price) / PIP_SIZE
                total_pnl += half_pnl * 0.5
                remaining_qty = 0.5
                phase = 'stage2'
                continue  # 遷移足は stage2 判定しない

            # 5M ダウ崩れ → 全量決済
            if check_5m_dow_break_simple(df_5m_after, i, direction):
                next_i = min(i + 1, n - 1)
                exit_price = float(df_5m_after.iloc[next_i]['open'])
                pnl = (exit_price - entry_price) / PIP_SIZE
                return {
                    'exit_price':  exit_price,
                    'exit_ts':     df_5m_after.index[next_i],
                    'exit_reason': 'stage1_5m_dow',
                    'pnl_pips':    pnl,
                    'exit_phase':  'stage1',
                }
            continue

        # ── 段階2: 4H neck 到達後（50% 決済済み）────────────────────────────
        if phase == 'stage2':
            # 建値ストップ（残り 50%）
            if bar['low'] <= entry_price:
                return {
                    'exit_price':  entry_price,
                    'exit_ts':     ts,
                    'exit_reason': 'stage2_breakeven_stop',
                    'pnl_pips':    total_pnl,  # 残り50%は建値 → 追加損益0
                    'exit_phase':  'stage2',
                }

            # 1H Close が neck_4h 上抜け確定 → stage3 移行
            if check_1h_close_above_neck(df_5m_after, i, neck_4h):
                phase = 'stage3'
                continue  # 遷移足は stage3 判定しない

            continue

        # ── 段階3: 1H 確定後 → 15M ダウ崩れで残り全量決済 ─────────────────
        if phase == 'stage3':
            # 建値ストップ（継続）
            if bar['low'] <= entry_price:
                return {
                    'exit_price':  entry_price,
                    'exit_ts':     ts,
                    'exit_reason': 'stage3_breakeven_stop',
                    'pnl_pips':    total_pnl,
                    'exit_phase':  'stage3',
                }

            # 15M ダウ崩れ → 残り全量決済
            if check_15m_dow_break_simple(df_5m_after, i, direction):
                next_i = min(i + 1, n - 1)
                exit_price = float(df_5m_after.iloc[next_i]['open'])
                remaining_pnl = (exit_price - entry_price) / PIP_SIZE
                total_pnl += remaining_pnl * remaining_qty
                return {
                    'exit_price':  exit_price,
                    'exit_ts':     df_5m_after.index[next_i],
                    'exit_reason': 'stage3_15m_dow',
                    'pnl_pips':    total_pnl,
                    'exit_phase':  'stage3',
                }
            continue

    # データ末尾に到達（未決済）
    last_price = float(df_5m_after.iloc[-1]['close'])
    remaining_pnl = (last_price - entry_price) / PIP_SIZE
    total_pnl += remaining_pnl * remaining_qty
    return {
        'exit_price':  last_price,
        'exit_ts':     df_5m_after.index[-1],
        'exit_reason': 'data_end',
        'pnl_pips':    total_pnl,
        'exit_phase':  phase,
    }


# ── 統計指標の計算 ────────────────────────────────────────────────────────────

def calc_stats(results: list[dict]) -> dict:
    """P&L リストから勝率 / PF / MaxDD / 総損益を算出する。"""
    pnls = [r['pnl_pips'] for r in results]
    wins   = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]

    total_pnl    = sum(pnls)
    win_rate     = len(wins) / len(pnls) * 100 if pnls else 0.0
    gross_profit = sum(wins) if wins else 0.0
    gross_loss   = abs(sum(losses)) if losses else 0.001  # ゼロ除算回避
    pf           = gross_profit / gross_loss

    # MaxDD（累積損益の最大ドローダウン）
    cumulative = []
    cum = 0.0
    for p in pnls:
        cum += p
        cumulative.append(cum)

    peak   = cumulative[0]
    max_dd = 0.0
    for c in cumulative:
        if c > peak:
            peak = c
        dd = peak - c
        if dd > max_dd:
            max_dd = dd

    return {
        'total_trades': len(pnls),
        'win_rate':     win_rate,
        'pf':           pf,
        'max_dd':       max_dd,
        'total_pnl':    total_pnl,
        'gross_profit': gross_profit,
        'gross_loss':   gross_loss,
    }


# ── メイン処理 ────────────────────────────────────────────────────────────────

def main():
    results = []

    for _, row in entries.iterrows():
        pattern     = str(row['pattern'])
        entry_ts    = pd.Timestamp(row['entry_ts'])
        entry_price = float(row['entry_price'])
        neck_15m    = float(row['neck_15m'])
        neck_1h     = float(row['neck_1h'])
        neck_4h     = float(row['neck_4h'])
        sl_4h       = float(row['sl_4h'])

        # entry_ts 以降の 5M データを切り出す
        df_after = df_5m.loc[entry_ts:]
        if len(df_after) == 0:
            print(f"  SKIP (no data after entry): {entry_ts}")
            continue

        res = simulate_exit(
            df_5m_after=df_after,
            entry_price=entry_price,
            neck_4h=neck_4h,
            sl_4h=sl_4h,
            direction=DIRECTION,
        )

        results.append({
            'pattern':     pattern,
            'entry_ts':    entry_ts,
            'entry_price': entry_price,
            'neck_15m':    neck_15m,
            'neck_1h':     neck_1h,
            'neck_4h':     neck_4h,
            'sl_4h':       sl_4h,
            'exit_ts':     res['exit_ts'],
            'exit_price':  res['exit_price'],
            'exit_reason': res['exit_reason'],
            'exit_phase':  res['exit_phase'],
            'pnl_pips':    round(res['pnl_pips'], 2),
        })

    # ── CSV 出力 ──────────────────────────────────────────────────────────────
    df_out = pd.DataFrame(results)
    df_out.to_csv(OUT_CSV, index=False)
    print(f"\nSaved: {OUT_CSV}  ({len(df_out)} rows)")

    # ── 統計算出 ──────────────────────────────────────────────────────────────
    stats = calc_stats(results)

    # ── コンソールレポート ────────────────────────────────────────────────────
    # 旧版 #018 比較値（固定）
    OLD = {
        'total_trades': 20,
        'win_rate':     55.0,
        'pf':           5.32,
        'max_dd':       14.9,
        'total_pnl':    91.6,
    }

    print("\n=== #026b 決済シミュレーション結果 ===\n")

    print("■ 統計指標")
    print(f"{'指標':<14}| {'#026b（新版）':>12} | {'#018（旧版）':>12} | {'差分':>10}")
    print("-" * 56)

    def diff_str(new, old):
        d = new - old
        sign = '+' if d >= 0 else ''
        return f"{sign}{d:.1f}"

    rows_stat = [
        ('総トレード', f"{stats['total_trades']}件",    f"{OLD['total_trades']}件",
         f"{stats['total_trades'] - OLD['total_trades']:+d}件"),
        ('勝率',       f"{stats['win_rate']:.1f}%",    f"{OLD['win_rate']:.1f}%",
         diff_str(stats['win_rate'], OLD['win_rate']) + '%'),
        ('PF',         f"{stats['pf']:.2f}",           f"{OLD['pf']:.2f}",
         diff_str(stats['pf'], OLD['pf'])),
        ('MaxDD',      f"{stats['max_dd']:.1f} pips",  f"{OLD['max_dd']:.1f} pips",
         diff_str(stats['max_dd'], OLD['max_dd']) + ' pips'),
        ('総損益',     f"{stats['total_pnl']:+.1f} pips", f"+{OLD['total_pnl']:.1f} pips",
         diff_str(stats['total_pnl'], OLD['total_pnl']) + ' pips'),
    ]
    for label, new_v, old_v, d_v in rows_stat:
        print(f"{label:<14}| {new_v:>12} | {old_v:>12} | {d_v:>10}")

    # パターン別
    print("\n■ パターン別")
    print(f"{'pattern':<10}| {'件数':>4} | {'勝率':>7} | {'平均損益(pips)':>14}")
    print("-" * 44)
    for pat in sorted(set(r['pattern'] for r in results)):
        pat_res = [r for r in results if r['pattern'] == pat]
        pat_pnls = [r['pnl_pips'] for r in pat_res]
        pat_wr = len([p for p in pat_pnls if p > 0]) / len(pat_pnls) * 100
        pat_avg = sum(pat_pnls) / len(pat_pnls)
        print(f"{pat:<10}| {len(pat_res):>4} | {pat_wr:>6.1f}% | {pat_avg:>+14.2f}")

    # 決済段階別
    print("\n■ 決済段階別")
    print(f"{'exit_phase':<12}| {'件数':>4} | {'平均損益(pips)':>14}")
    print("-" * 34)
    phase_order = ['initial', 'stage1', 'stage2', 'stage3', 'data_end']
    for ph in phase_order:
        ph_res = [r for r in results if r['exit_phase'] == ph]
        if not ph_res:
            continue
        ph_pnls = [r['pnl_pips'] for r in ph_res]
        ph_avg = sum(ph_pnls) / len(ph_pnls)
        print(f"{ph:<12}| {len(ph_res):>4} | {ph_avg:>+14.2f}")

    # 全エントリー詳細
    print("\n■ 全エントリー詳細")
    print(f"{'#':>2} | {'pat':<9} | {'entry':>7} | {'exit':>7} | {'reason':<26} | {'phase':<8} | {'pnl':>7}")
    print("-" * 80)
    for j, r in enumerate(results, 1):
        print(
            f"{j:>2} | {r['pattern']:<9} | {r['entry_price']:>7.3f} | "
            f"{r['exit_price']:>7.3f} | {r['exit_reason']:<26} | "
            f"{r['exit_phase']:<8} | {r['pnl_pips']:>+7.2f}"
        )

    print(f"\n{'=' * 40}")
    print(f"Output: {OUT_CSV}")


if __name__ == '__main__':
    main()
