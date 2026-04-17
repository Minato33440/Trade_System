# REX 指示書 #026b — 決済シミュレーション（exit_simulator.py 新規作成）
# 発行: Rex-Evaluator（Opus）→ ClaudeCode 直接
# 承認: ボス（2026-04-15）
# think harder

---

## ⛔ 最重要ルール — 実装前に必ず実行

```bash
# 1. manage_exit() のシグネチャと内部ロジックを確認
cat src/exit_logic.py

# 2. check_5m_dow_break / check_15m_dow_break のシグネチャ確認
grep -n "def check_" src/exit_logic.py

# 3. check_4h_neck_1h_confirmed のシグネチャ確認
grep -n "def check_4h" src/exit_logic.py

# 4. window_scan_entries.csv の現在のカラム構成を確認
head -2 logs/window_scan_entries.csv

# 5. swing_detector.py の detect_swing_highs/lows シグネチャ確認
grep -n "def detect_swing" src/swing_detector.py

# 6. resample_tf の場所と引数確認
grep -rn "def resample_tf" src/
```

**上記6つを全て read した後でなければ、コードを1行も書いてはならない。**
シグネチャが指示書の想定と異なる場合はボスに報告して停止。

---

## 目的

`logs/window_scan_entries.csv`（12件）の各エントリーに対して
決済シミュレーションを実行し、P&L / PF / 勝率 / MaxDD を算出する。
旧版 backtest.py（#018）との比較レポートを生成する。

---

## 作成ファイル

```
src/exit_simulator.py（新規・1ファイルのみ）
```

**変更禁止ファイル**: backtest.py / entry_logic.py / exit_logic.py / swing_detector.py / window_scanner.py
**確認方法**: 実装完了後に `git diff -- src/backtest.py src/entry_logic.py src/exit_logic.py src/swing_detector.py src/window_scanner.py` で差分ゼロを確認

---

## 処理フロー

```
① データ読み込み
   - df_5m = pd.read_parquet('data/raw/usdjpy_multi_tf_2years.parquet')
   - entries = pd.read_csv('logs/window_scan_entries.csv')
   - カラム名の正規化（実ファイルで確認してから実装）

② 各エントリーに対するループ
   for each entry in entries:
     a. entry_ts / entry_price / neck_4h / sl_4h / neck_15m を取得
     b. entry_ts 以降の 5M データを切り出し
     c. 4段階決済ロジックを 5M バーごとに適用
     d. 決済価格・決済理由・損益を記録

③ 統計指標の算出
   - 勝率 / PF / MaxDD / 総損益

④ CSV出力 + コンソールレポート
```

---

## 決済ロジックの実装（4段階）

**最重要: manage_exit() を直接呼び出せるなら呼び出す。
呼び出せない（引数が複雑すぎる、内部状態に依存している等）場合は、
以下のロジックを exit_simulator.py 内に独自実装する。
どちらの方式を採用したかを結果報告に明記すること。**

### 方式A: manage_exit() を直接呼び出す場合

```python
from src.exit_logic import manage_exit
# シグネチャを read してから呼び出し方を決定
```

### 方式B: 独自実装する場合（推奨 — manage_exit()のAPIが複雑な場合）

以下の4段階を 5M バーごとに判定する:

```python
PIP_SIZE = 0.01

def simulate_exit(df_5m_after, entry_price, neck_4h, sl_4h, direction='LONG'):
    """
    entry_price: エントリー価格
    neck_4h:     半値決済トリガー（4H SH = 段階2移行ライン）
    sl_4h:       4H SL（損切基準）
    df_5m_after: entry_ts 以降の5Mデータ
    
    Returns: dict with exit_price, exit_ts, exit_reason, pnl_pips, exit_phase
    """
    
    phase = 'initial'  # initial → stage1 → stage2 → stage3
    half_exited = False
    swing_confirmed_5m = False
    remaining_qty = 1.0  # 1.0 = 全量
    total_pnl = 0.0
    
    for i, (ts, bar) in enumerate(df_5m_after.iterrows()):
        
        # ----- 初動SL: 15M ダウ崩れで全量損切 -----
        if phase == 'initial':
            # 5M Swing が確定したら stage1 に移行
            # （前後n=2本でSHまたはSLが確定 = swing_confirmed）
            if check_swing_confirmed_5m(df_5m_after, i):
                phase = 'stage1'
            else:
                # 15M ダウ崩れ判定
                if check_15m_dow_break_simple(df_5m_after, i, direction):
                    exit_price = df_5m_after.iloc[min(i+1, len(df_5m_after)-1)]['open']
                    pnl = (exit_price - entry_price) / PIP_SIZE
                    return {
                        'exit_price': exit_price,
                        'exit_ts': df_5m_after.index[min(i+1, len(df_5m_after)-1)],
                        'exit_reason': 'initial_SL_15m_dow',
                        'pnl_pips': pnl,
                        'exit_phase': 'initial'
                    }
        
        # ----- 段階1: 5M ダウ崩れで全量決済 -----
        if phase == 'stage1':
            # 4H neck（= neck_4h）到達チェック → stage2
            if bar['high'] >= neck_4h:
                # 50%決済を記録
                half_pnl = (neck_4h - entry_price) / PIP_SIZE
                total_pnl += half_pnl * 0.5
                half_exited = True
                remaining_qty = 0.5
                phase = 'stage2'
                continue
            
            # 5M ダウ崩れ判定
            if check_5m_dow_break_simple(df_5m_after, i, direction):
                exit_price = df_5m_after.iloc[min(i+1, len(df_5m_after)-1)]['open']
                pnl = (exit_price - entry_price) / PIP_SIZE
                return {
                    'exit_price': exit_price,
                    'exit_ts': df_5m_after.index[min(i+1, len(df_5m_after)-1)],
                    'exit_reason': 'stage1_5m_dow',
                    'pnl_pips': pnl,
                    'exit_phase': 'stage1'
                }
        
        # ----- 段階2: 4H neck到達後（50%決済済み）-----
        if phase == 'stage2':
            # 建値ストップ判定（残り50%）
            if bar['low'] <= entry_price:
                # 残り50%を建値で決済 → 利益はhalf分のみ
                return {
                    'exit_price': entry_price,
                    'exit_ts': ts,
                    'exit_reason': 'stage2_breakeven_stop',
                    'pnl_pips': total_pnl,
                    'exit_phase': 'stage2'
                }
            
            # 1H Close が 4H SH（neck_4h）上抜け確定チェック → stage3
            if check_1h_close_above_4h_sh(df_5m_after, i, neck_4h):
                phase = 'stage3'
                continue
        
        # ----- 段階3: 15M ダウ崩れで残り全量決済 -----
        if phase == 'stage3':
            # 建値ストップ（stage2から継続）
            if bar['low'] <= entry_price:
                return {
                    'exit_price': entry_price,
                    'exit_ts': ts,
                    'exit_reason': 'stage3_breakeven_stop',
                    'pnl_pips': total_pnl,
                    'exit_phase': 'stage3'
                }
            
            # 15M ダウ崩れ判定
            if check_15m_dow_break_simple(df_5m_after, i, direction):
                exit_price = df_5m_after.iloc[min(i+1, len(df_5m_after)-1)]['open']
                remaining_pnl = (exit_price - entry_price) / PIP_SIZE
                total_pnl += remaining_pnl * remaining_qty
                return {
                    'exit_price': exit_price,
                    'exit_ts': df_5m_after.index[min(i+1, len(df_5m_after)-1)],
                    'exit_reason': 'stage3_15m_dow',
                    'pnl_pips': total_pnl,
                    'exit_phase': 'stage3'
                }
    
    # データ末尾に到達（決済されなかった）
    last_price = df_5m_after.iloc[-1]['close']
    remaining_pnl = (last_price - entry_price) / PIP_SIZE
    total_pnl += remaining_pnl * remaining_qty
    return {
        'exit_price': last_price,
        'exit_ts': df_5m_after.index[-1],
        'exit_reason': 'data_end',
        'pnl_pips': total_pnl,
        'exit_phase': phase
    }
```

### ダウ崩れ判定のシンプル実装

**まず exit_logic.py の check_5m_dow_break / check_15m_dow_break を read する。**
これらが使える場合はそのまま使う。使えない場合（引数にdf全体が必要など）は
以下のシンプル版を実装:

```python
def check_5m_dow_break_simple(df_5m, current_idx, direction='LONG'):
    """
    直近の5M SHを下回る5M Closeが出たらダウ崩れ
    """
    if current_idx < 10:
        return False
    window = df_5m.iloc[max(0, current_idx-20):current_idx+1]
    # 直近のSH（高値の局所最大値）
    highs = window['high']
    sh_flags = detect_swing_highs(highs, n=2)
    sh_vals = highs[sh_flags]
    if len(sh_vals) == 0:
        return False
    last_sh = sh_vals.iloc[-1]
    # 現在の5M Close（実体下端）が直近SHの安値を下回った
    current_close = min(df_5m.iloc[current_idx]['open'], df_5m.iloc[current_idx]['close'])
    if direction == 'LONG':
        # SLが前回SLを割った = ダウ崩れ
        lows = window['low']
        sl_flags = detect_swing_lows(lows, n=2)
        sl_vals = lows[sl_flags]
        if len(sl_vals) >= 2:
            if sl_vals.iloc[-1] < sl_vals.iloc[-2]:
                return True
    return False

def check_15m_dow_break_simple(df_5m, current_idx, direction='LONG'):
    """
    5Mデータを15Mにリサンプルしてダウ崩れ判定
    """
    if current_idx < 30:
        return False
    window_5m = df_5m.iloc[max(0, current_idx-60):current_idx+1]
    df_15m = resample_tf(window_5m, '15min')
    if len(df_15m) < 10:
        return False
    lows = df_15m['low']
    sl_flags = detect_swing_lows(lows, n=3)
    sl_vals = lows[sl_flags]
    if len(sl_vals) >= 2:
        if sl_vals.iloc[-1] < sl_vals.iloc[-2]:
            return True
    return False

def check_swing_confirmed_5m(df_5m, current_idx):
    """
    5M SH または SL が確定したかチェック
    """
    if current_idx < 5:
        return False
    window = df_5m.iloc[max(0, current_idx-10):current_idx+1]
    sh = detect_swing_highs(window['high'], n=2)
    sl = detect_swing_lows(window['low'], n=2)
    return sh.any() or sl.any()

def check_1h_close_above_4h_sh(df_5m, current_idx, neck_4h):
    """
    1H足のClose（= 5M足12本目のClose）が neck_4h を上抜けたか
    """
    current_ts = df_5m.index[current_idx]
    # 毎時00分の5M足（= 1H足の最終足）かどうか
    if current_ts.minute == 55:  # 5M足の55分 = 次の00分で1H確定
        close_1h = df_5m.iloc[current_idx]['close']
        if close_1h > neck_4h:
            return True
    return False
```

**⚠️ 上記はシンプル版の参考実装。exit_logic.py の実関数を read した上で、
使えるものはそのまま使い、使えないものだけ独自実装すること。**

---

## 統計指標の計算

```python
def calc_stats(results):
    """
    results: list of dict（各エントリーの決済結果）
    """
    pnls = [r['pnl_pips'] for r in results]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    
    total_pnl = sum(pnls)
    win_rate = len(wins) / len(pnls) * 100 if pnls else 0
    
    gross_profit = sum(wins) if wins else 0
    gross_loss = abs(sum(losses)) if losses else 0.001  # ゼロ除算回避
    pf = gross_profit / gross_loss
    
    # MaxDD（累積損益の最大ドローダウン）
    cumulative = []
    cum = 0
    for p in pnls:
        cum += p
        cumulative.append(cum)
    peak = cumulative[0]
    max_dd = 0
    for c in cumulative:
        if c > peak:
            peak = c
        dd = peak - c
        if dd > max_dd:
            max_dd = dd
    
    return {
        'total_trades': len(pnls),
        'win_rate': win_rate,
        'pf': pf,
        'max_dd': max_dd,
        'total_pnl': total_pnl,
        'gross_profit': gross_profit,
        'gross_loss': gross_loss,
    }
```

---

## 出力

### CSV: `logs/window_scan_exits.csv`

```
カラム:
  pattern, entry_ts, entry_price, neck_15m, neck_1h, neck_4h, sl_4h,
  exit_ts, exit_price, exit_reason, exit_phase, pnl_pips
```

### コンソール出力（比較レポート）

```
=== #026b 決済シミュレーション結果 ===

■ 統計指標
指標          | #026b（新版）| #018（旧版）| 差分
総トレード    |              | 20件         |
勝率          |              | 55.0%        |
PF            |              | 5.32         |
MaxDD         |              | 14.9 pips    |
総損益        |              | +91.6 pips   |

■ パターン別
pattern   | 件数 | 勝率 | 平均損益(pips)
DB        |      |      |
ASCENDING |      |      |

■ 決済段階別
exit_phase | 件数 | 平均損益(pips)
initial    |      |
stage1     |      |
stage2     |      |
stage3     |      |
data_end   |      |

■ 全エントリー詳細
#  | pattern | entry     | exit      | reason    | phase  | pnl
01 | DB      | 151.909   | ...       | ...       | ...    | ...
...
```

---

## 完了条件

```
✅ python src/exit_simulator.py がエラーなし実行
✅ logs/window_scan_exits.csv が生成（12件分）
✅ コンソールに比較レポートが出力
✅ git diff -- src/backtest.py src/entry_logic.py src/exit_logic.py
   src/swing_detector.py src/window_scanner.py 差分ゼロ
✅ git commit -m "Feat: #026b exit simulator with P&L calculation"
```

---

## 結果報告フォーマット

```
=== #026b 結果報告 ===

■ 実装方式
manage_exit() 直接呼出 / 独自実装（どちらを採用したか明記）
理由:

■ 統計指標
指標          | #026b   | #018    | 差分
総トレード    |         | 20件    |
勝率          |         | 55.0%   |
PF            |         | 5.32    |
MaxDD         |         | 14.9p   |
総損益        |         | +91.6p  |

■ パターン別
pattern   | 件数 | 勝率   | 平均pnl
DB        |      |        |
ASCENDING |      |        |

■ 決済段階別
exit_phase | 件数 | 平均pnl
initial    |      |
stage1     |      |
stage2     |      |
stage3     |      |
data_end   |      |

■ 全12件の詳細（1行ずつ）
#  | pat  | entry_price | exit_price | reason | phase | pnl_pips
01 | ...  | ...         | ...        | ...    | ...   | ...
```

---

## ⚠️ 決済ロジックの正しい定義（ADR D-6 準拠・ボス確認済み）

```
■ 半値決済トリガー = neck_4h（4H SH）
  段階2: High >= neck_4h → 50%決済 + 残りストップを建値に移動

■ neck_4h は CSV カラムから読み取る（再計算しない）

■ 4段階の流れ
  初動SL: 15M ダウ崩れ → 全量損切（5M Swing未確定時）
  段階1:  5M ダウ崩れ → 全量決済（5M Swing確定後〜4H neck未到達）
  段階2:  4H neck到達 → 50%決済 + 建値移動
  段階3:  1H Close > 4H SH 確定 → 15M ダウ崩れで残り決済

■ 全ての決済は「確定足の次足始値」で執行
```

---

## ClaudeCode 不変ルール（全指示書共通）

```
1. 既存関数を呼ぶ前に必ず実ファイルの def 行を read する
2. 凍結ファイルは変更しない（backtest / entry_logic / exit_logic / swing_detector）
3. window_scanner.py も今回は変更しない
4. resample_tf は label='right', closed='right' で統一
5. 全てのトレランスは pip ベース（PIP_SIZE = 0.01）
6. 指示書のコードをそのままコピペせず、実APIに合わせる
7. git diff で禁止ファイルの差分ゼロを完了条件に含める
8. エラーが出たら自分で「想像で」修正しない。ボスに報告して停止
```

---

**発行: Rex-Evaluator / 2026-04-15**
