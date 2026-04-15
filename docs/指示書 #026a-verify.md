# REX 指示書 #026a-verify — 4H/1H 構造整合性検証プロット
# 宛先: ClaudeCode（VS Code）
# 発行: Rex-Planner（Sonnet） / 設計: Rex-Evaluator（Opus）
# 承認: ボス（2026-04-14）
# 思考フラグ: think harder

---

## 0. 作業開始前に必ずやること（ADR B-1/B-2 — 省略禁止）

以下の順番で実ファイルを read してからコードを書くこと。

```
① src/swing_detector.py を read して以下を確認:
   - detect_swing_highs(series, n, lookback=?) のシグネチャ全文
   - detect_swing_lows(series, n, lookback=?) のシグネチャ全文
   - resample_tf(df, tf) のシグネチャ全文

② src/window_scanner.py を read して以下を確認:
   - scan_4h_events() で使っている n / lookback の実際の値
   - df_4h の生成方法（resample_tf の引数）
```

読み終えた後、以下を確認してメモする:
- detect_swing_highs の返り値: bool Series か、価格 Series か
- 4H検出に使っている n= と lookback= の実際の値
- resample_tf の戻り値のカラム名（High/Low/Open/Close か high/low/open/close か）

---

## 1. 今回の作業概要

**新規スクリプト `src/verify_4h1h_structure.py` を作成する。**
既存ファイルは一切変更しない。

**目的**:
コードが検出している 4H SH/SL の位置が、TradingView（裁量チャート）で
目視できる4H構造と一致しているかを目視検証するための1H足チャートを生成する。

**発生した問題（ボス確認済み・2026-04-14）**:
Plot06（20250107 ASCENDING）で `4H SL = 157.350` だが、
TVチャートの実際の4H押し目底は 156.4〜156.6 付近（約80pipsのズレ）。

---

## 2. 実装内容

### 2-1. データ読み込みとリサンプル

```python
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# パス設定（実ファイルを確認してから調整すること）
_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.swing_detector import detect_swing_highs, detect_swing_lows, resample_tf

# 5Mデータ読み込み
DATA_PATH = _repo_root / 'data' / 'raw' / 'usdjpy_multi_tf_2years.parquet'
df_5m = pd.read_parquet(DATA_PATH)

# リサンプル（ADR不変ルール#3: label='right', closed='right' 厳守）
df_1h = resample_tf(df_5m, '1h')
df_4h = resample_tf(df_5m, '4h')
```

### 2-2. Swing High/Low 検出

```python
# window_scanner.py と同じパラメータを使うこと（実ファイルで確認した値）
# 以下は概念コード。実際のn/lookbackは実ファイルを読んで確認すること（ADR B-1）

# 4H Swing
sh_4h_flags = detect_swing_highs(df_4h['High'], n=3)   # nは実ファイルで確認
sl_4h_flags = detect_swing_lows(df_4h['Low'],  n=3)

sh_4h_vals = df_4h['High'][sh_4h_flags]   # 4H SH の価格Series
sl_4h_vals = df_4h['Low'][sl_4h_flags]    # 4H SL の価格Series

# 1H Swing
sh_1h_flags = detect_swing_highs(df_1h['High'], n=2)
sl_1h_flags = detect_swing_lows(df_1h['Low'],  n=2)

sh_1h_vals = df_1h['High'][sh_1h_flags]
sl_1h_vals = df_1h['Low'][sl_1h_flags]
```

**注意**: detect_swing_highs の返り値が bool Series の場合は上記のように使う。
もし返り値が価格 Series の場合はそのまま使う。
実ファイルを確認してから判断すること（ADR B-1）。

### 2-3. プロット生成関数

```python
def plot_verify(start_str: str, end_str: str, save_name: str):
    """
    指定期間の1H足ローソクチャートに4H/1H SH/SLマーカーをオーバーレイして保存。

    Args:
        start_str: 開始日時文字列（例: '2025-01-01'）
        end_str:   終了日時文字列（例: '2025-01-15'）
        save_name: 保存ファイル名（例: '01_20250101_4h1h_verify.png'）
    """
    # 1H足を期間で切り出し
    df_plot = df_1h.loc[start_str:end_str].copy()
    if len(df_plot) == 0:
        print(f"  SKIP: データなし {start_str}〜{end_str}")
        return

    # mplfinance でローソク描画（ADR C系厳守）
    s = mpf.make_mpf_style(base_mpf_style='nightclouds')
    fig, axes = mpf.plot(
        df_plot,
        type='candle',
        style=s,
        returnfig=True,       # ← 必須（ADR C-1）
        figsize=(22, 9),
        title='',             # タイトルは後でax.set_title()で設定
    )
    ax = axes[0]

    # タイトル設定（日本語禁止・ADR C-5）
    ax.set_title(
        f'4H/1H Structure Verify  {start_str} ~ {end_str}\n'
        f'4H SH/SL: n=3  |  1H SH/SL: n=2',
        fontsize=11, color='white', pad=10
    )

    # ── 4H / 1H マーカーを ax.scatter() で描画 ──────────────────────
    # ⛔ addplot は使わない（ADR C-2/C-3）
    # ✅ ax.scatter() に x軸の整数インデックスを渡す

    def get_x_pos(ts, df_plot):
        """タイムスタンプをdf_plotの整数x軸位置に変換する。"""
        if ts in df_plot.index:
            return df_plot.index.get_loc(ts)
        # 存在しない場合は searchsorted で最近傍
        pos = df_plot.index.searchsorted(ts)
        return pos if pos < len(df_plot) else None

    # 4H Swing High（赤・大きめ▼）
    for ts, val in sh_4h_vals.loc[start_str:end_str].items():
        x = get_x_pos(ts, df_plot)
        if x is not None and 0 <= x < len(df_plot):
            ax.scatter(x, val * 1.0003, color='#FF4444', marker='v',
                       s=180, zorder=10, label='_nolegend_')

    # 4H Swing Low（青・大きめ▲）
    for ts, val in sl_4h_vals.loc[start_str:end_str].items():
        x = get_x_pos(ts, df_plot)
        if x is not None and 0 <= x < len(df_plot):
            ax.scatter(x, val * 0.9997, color='#1E90FF', marker='^',
                       s=180, zorder=10, label='_nolegend_')

    # 1H Swing High（オレンジ・小さめ▼）
    for ts, val in sh_1h_vals.loc[start_str:end_str].items():
        x = get_x_pos(ts, df_plot)
        if x is not None and 0 <= x < len(df_plot):
            ax.scatter(x, val * 1.0002, color='#FFA500', marker='v',
                       s=70, zorder=9, label='_nolegend_')

    # 1H Swing Low（シアン・小さめ▲）
    for ts, val in sl_1h_vals.loc[start_str:end_str].items():
        x = get_x_pos(ts, df_plot)
        if x is not None and 0 <= x < len(df_plot):
            ax.scatter(x, val * 0.9998, color='#00CED1', marker='^',
                       s=70, zorder=9, label='_nolegend_')

    # 凡例（ダミープロットで作成）
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0],[0], marker='v', color='w', markerfacecolor='#FF4444',
               markersize=12, label='4H Swing High'),
        Line2D([0],[0], marker='^', color='w', markerfacecolor='#1E90FF',
               markersize=12, label='4H Swing Low'),
        Line2D([0],[0], marker='v', color='w', markerfacecolor='#FFA500',
               markersize=8,  label='1H Swing High'),
        Line2D([0],[0], marker='^', color='w', markerfacecolor='#00CED1',
               markersize=8,  label='1H Swing Low'),
    ]
    ax.legend(handles=legend_elements, loc='upper left',
              fontsize=9, framealpha=0.5)

    # 保存
    out_dir = _repo_root / 'logs' / 'verify_4h1h'
    out_dir.mkdir(parents=True, exist_ok=True)
    save_path = out_dir / save_name
    fig.savefig(save_path, dpi=130, bbox_inches='tight',
                facecolor='#0f0f0f')
    plt.close(fig)
    print(f"  Saved: {save_path}")
```

### 2-4. メイン実行（5期間）

```python
if __name__ == '__main__':
    out_dir = Path(_repo_root) / 'logs' / 'verify_4h1h'
    out_dir.mkdir(parents=True, exist_ok=True)

    cases = [
        # (開始日,       終了日,        ファイル名,                       備考)
        ('2024-12-25', '2025-01-15', '01_20250101_4h1h_verify.png',
         'Plot06対応 — 4H SLズレの疑い'),
        ('2024-03-20', '2024-04-05', '02_20240325_4h1h_verify.png',
         'Plot01 DB — 最初期の検出'),
        ('2024-06-10', '2024-06-25', '03_20240617_4h1h_verify.png',
         'Plot02 ASCENDING'),
        ('2025-06-10', '2025-06-25', '04_20250617_4h1h_verify.png',
         'Plot07 DB'),
        ('2025-09-10', '2025-09-25', '05_20250917_4h1h_verify.png',
         'Plot09/10 ASCENDING — 連続検出期間'),
    ]

    for start, end, fname, note in cases:
        print(f"\n[{note}]  {start} ~ {end}")
        plot_verify(start, end, fname)

    print("\n=== verify_4h1h_structure.py 完了 ===")
    print(f"出力先: logs/verify_4h1h/ ({len(cases)}枚)")
```

---

## 3. 変更してはいけないファイル

```
既存ファイルは一切変更しない。

確認コマンド:
  git diff -- src/window_scanner.py src/swing_detector.py \
              src/entry_logic.py src/exit_logic.py \
              src/backtest.py src/plotter.py
  → 差分ゼロであること
```

---

## 4. エラー発生時の対処

```
エラーが出たら自分で想像で修正しない。Rex に以下を報告して停止:

  ① エラーメッセージ全文
  ② エラーが出た行番号とコード
  ③ その時点での変数の型と値（print で確認）

よくある原因:
  TypeError: ax.scatter の x が float → int(x) で対処（報告後に試す）
  KeyError: カラム名の大文字小文字 → 実ファイルで確認
  ValueError: タイムゾーン不一致 → ts と df.index の tz を print して報告
  IndexError: searchsorted 範囲外 → get_x_pos の戻り値チェックを強化
```

---

## 5. 完了条件（全て満たすこと）

```
✅ python src/verify_4h1h_structure.py がエラーなし実行完了
✅ logs/verify_4h1h/ に5枚のPNGが生成されている
✅ 各PNGに 4H▼▲（大・赤/青）と 1H▼▲（小・オレンジ/シアン）が描画されている
✅ 既存ファイルの差分ゼロ（git diff で確認）
✅ git add src/verify_4h1h_structure.py logs/verify_4h1h/
✅ git commit -m "Verify: #026a-verify 4H/1H structure check plots"
```

---

## 6. 結果報告フォーマット（必須・実行後に必ず出力）

```
=== #026a-verify 結果報告 ===

生成プロット: 5枚
実際に使用したパラメータ:
  4H Swing: n=? lookback=?（実ファイルで確認した値）
  1H Swing: n=? lookback=?

■ 各プロットの4H SH/SL 検出数
01_20250101: 4H SH=?本 / 4H SL=?本  （期間内）
02_20240325: 4H SH=?本 / 4H SL=?本
03_20240617: 4H SH=?本 / 4H SL=?本
04_20250617: 4H SH=?本 / 4H SL=?本
05_20250917: 4H SH=?本 / 4H SL=?本
```

---

**発行: Rex-Planner / 2026-04-14**
**設計根拠: REX_026a_verify_spec.md / ADR-2026-04-13 F-1**
**次ステップ: ボスがTVチャートと比較 → Evaluatorが判定 → #026b or パラメータ調整**