# REX AI Trade System — ロジック整合性マトリクス
# 発行: Rex-Evaluator（Opus） / 作成日: 2026-04-15
# 時点: #026a-v2完了・#026b完了・#026c実装前
# 用途: wrap-up時のNLM更新で「何がどう変わったか」を一覧把握する

---

## 1. ファイル状態マトリクス

### ソースファイル

| ファイル | 最終変更 | 状態 | 変更可否 | 依存先 |
|---|---|---|---|---|
| swing_detector.py | #020 | ✅凍結 | ❌ 変更禁止 | entry_logic / backtest / window_scanner |
| entry_logic.py | #018 | ✅凍結 | ❌ 変更禁止 | backtest |
| exit_logic.py | #009 | ✅凍結 | ❌ 変更禁止 | backtest（manage_exit） |
| backtest.py | #018 | ✅凍結 | ❌ 変更禁止 | ベースライン保持 |
| window_scanner.py | #026a-v2 | 拡張可能 | ⚠️ ロジック変更は要確認 | swing_detector / entry_logic(check_15m_range_low) |
| exit_simulator.py | #026b | 新規 | ✅ 自由 | window_scan_entries.csv |
| plotter.py | #020-fix | 拡張可能 | ✅ 表示追加自由 | なし |
| structure_plotter.py | #019 | 拡張可能 | ✅ 表示追加自由 | swing_detector |
| base_scanner.py | #015 | 完了 | ⚠️ | swing_detector |

### 出力ファイル

| ファイル | 生成元 | 最終更新 | カラム数 |
|---|---|---|---|
| logs/window_scan_entries.csv | window_scanner.py | #026a-v2 | 12 |
| logs/window_scan_exits.csv | exit_simulator.py | #026b | 7+ |
| logs/window_scan_plots/*.png | window_scanner.py | #026a-v2 | 12枚 |

---

## 2. パラメータ整合性マトリクス（#026c実装前の現在値）

### エントリー関連

| パラメータ | 定義場所 | 現在値 | 使用場所 | #026c後の変更 |
|---|---|---|---|---|
| DIRECTION_MODE | window_scanner.py | 'LONG' | スキャン方向 | 変更なし |
| ALLOWED_PATTERNS | window_scanner.py | ['DB','ASCENDING','IHS'] | パターンフィルタ | 変更なし |
| WICKTOL_PIPS | window_scanner.py | 5.0 | エントリー判定（実体越え） | **使用停止**（残置） |
| ENTRY_OFFSET_PIPS | （未定義） | — | — | **新規追加 = 7.0** |
| MIN_4H_SWING_PIPS | window_scanner.py | 20.0 | 4H Swing幅ガード | 変更なし |
| LOOKBACK_15M_RANGE | entry_logic.py | 50 | 15M パターン検出 | 変更なし |
| MAX_REENTRY | window_scanner.py | 1 | 再エントリー上限 | 変更なし |
| PIP_SIZE | 共通 | 0.01 | pip計算 | 変更なし |
| N_1H_SWING | window_scanner.py | 3 | 1H Swing検出粒度 | 変更なし |

### 窓関連

| パラメータ | 定義場所 | 現在値 | 用途 |
|---|---|---|---|
| WINDOW_1H_PRE | window_scanner.py | 20 | 1H SL前の窓幅 |
| WINDOW_1H_POST | window_scanner.py | 10 | 1H SL後の窓幅 |
| PRICE_TOL_PIPS | window_scanner.py | 20.0 | 1H SL選択許容 |
| PLOT_PRE_H | window_scanner.py | 25 | プロット表示（窓と独立） |
| PLOT_POST_H | window_scanner.py | 40 | プロット表示 |

### Swing検出パラメータ

| タイムフレーム | n値 | 定義場所 | 確定指示書 |
|---|---|---|---|
| 4H | n=3 | swing_detector.py | 初期確定 |
| 1H | n=3 | window_scanner.py (N_1H_SWING) | #026a-v2（D-7） |
| 15M | n=3 | entry_logic.py | #014確定 |
| 5M | n=2 | window_scanner.py（プロット用） | 初期確定 |

### neck定義（#026a-v2現在）

| neck | 算出方法 | 用途 | 定義根拠 |
|---|---|---|---|
| neck_15m | 窓内 かつ sl_1h_ts以前 の最後の15M SH | エントリートリガー | 統一neck原則（F-6） |
| neck_1h | 窓内 かつ sl_1h_ts以前 の最後の1H SH | 窓特定アンカー | F-6 / D-6修正 |
| neck_4h | sl_4h_ts以前 の最後の4H SH | 半値決済トリガー（段階2） | F-6 / D-6修正 |

### エントリー判定方式

| 項目 | #026b現在（変更前） | #026c後（変更後） |
|---|---|---|
| 判定条件 | min(open,close) > neck_15m + 5.0pips | bar['high'] >= neck_15m + 7.0pips |
| 判定対象 | 5M実体の下限 | 5M高値（ヒゲ含む） |
| entry_price | 確定足の次の5M始値 | neck_15m + 7.0pips（固定） |
| entry_ts | 次足のタイムスタンプ | 到達足のタイムスタンプ |

### 決済関連

| 段階 | トリガー | 決済内容 | 実装場所 |
|---|---|---|---|
| 初動SL | 15M ダウ崩れ | 全量損切 | exit_simulator.py（方式B） |
| 段階1 | 5M ダウ崩れ | 全量決済 | exit_simulator.py（方式B） |
| 段階2 | High >= neck_4h | 50%決済 + 建値移動 | exit_simulator.py（方式B） |
| 段階3 | 1H Close > 4H SH確定後 | 15Mダウ崩れで残り全量 | exit_simulator.py（方式B） |

---

## 3. 既知の不整合マトリクス

### NLMソース vs 実装の乖離

| NLMソース | 記述内容 | 実態 | 影響度 | 対応 |
|---|---|---|---|---|
| EX_DESIGN-2026-3-31 | 「指値方式は廃止」 | #026cで指値方式復活 | 🔴高 | wrap-upで新EX_DESIGN作成 |
| EX_DESIGN-2026-3-31 | WICKTOL_PIPS=5.0でエントリー | ENTRY_OFFSET_PIPS=7.0に変更予定 | 🔴高 | 同上 |
| EX_DESIGN-2026-3-31 | neck=sh_vals.iloc[0]（SL以降初回） | 統一neck原則（SL直前最後） | 🔴高 | 同上 |
| EX_DESIGN-2026-3-31 | 15件検出（DB:3/IHS:3/ASC:9） | 12件（DB:2/IHS:0/ASC:10） | 🟡中 | 同上 |
| EX_DESIGN-2026-3-31 | manage_exit()で決済 | 方式B（独自実装） | 🟡中 | 同上 |
| SYSTEM_OVERVIEW | exit_simulator.py 未記載 | #026bで新規作成済み | 🟡中 | wrap-upで新SYSTEM_OVERVIEW作成 |

### 凍結ファイル内部 vs ADR最新定義の乖離

| ファイル | 内部動作 | ADR最新定義 | 影響 |
|---|---|---|---|
| exit_logic.py manage_exit() | neck_1hで段階2判定 | neck_4hで段階2判定（D-6） | #026bで方式B迂回により回避済み |
| entry_logic.py | WICKTOL_PIPS=5.0 実体越え | ENTRY_OFFSET_PIPS=7.0 指値（#026c） | window_scanner.pyで独立実装のため影響なし |
| backtest.py | 旧版ロジック一式 | 現行は別系統（window_scanner + exit_simulator） | ベースライン比較専用。乖離は設計上意図的 |

### プロジェクトナレッジ（Claude.ai添付）vs NLM

| ファイル | プロジェクトナレッジ版 | NLM版 | 差異 |
|---|---|---|---|
| ADR | 2026-04-13（D:5件/F:5件） | 2026-04-14_2_2（D:7件/F:6件） | **ボスがPull済み（2026-04-15）** |
| EX_DESIGN | 2026-3-31 | 2026-3-31（同一） | 両方とも旧版。wrap-upで更新 |
| HANDOFF | 2026-04-13 | （NLM未投入） | HANDOFFはNLM対象外 |

---

## 4. CSVカラム定義（#026a-v2現在 / 12カラム）

```
window_scan_entries.csv:
  idx           # 窓番号
  sl_1h_ts      # 1H SLのタイムスタンプ
  sl_4h_ts      # 4H SLのタイムスタンプ
  sl_4h_val     # 4H SL価格
  pattern       # DB / IHS / ASCENDING
  neck_15m      # 15Mネック（統一neck原則）
  entry_price   # エントリー価格 ← #026cで計算方式変更
  entry_ts      # エントリー時刻 ← #026cで「到達足」に変更
  confirm_ts    # 確定足時刻
  neck_1h       # 1Hネック（窓アンカー）
  neck_4h       # 4Hネック（半値決済トリガー）
  sh_4h         # 4H SH（= neck_4h と同値）
```

**#026c による変更**:
- entry_price: 次足始値 → neck_15m + ENTRY_OFFSET_PIPS * PIP_SIZE
- entry_ts: 次足ts → 到達足ts
- カラム構成自体は変更なし（12カラム維持）

---

## 5. 依存関係ダイアグラム（テキスト版）

```
[凍結層 — ベースライン保持]
  swing_detector.py ──→ entry_logic.py ──→ backtest.py (#018: PF 5.32)
                    └──→ exit_logic.py  ──┘

[拡張層 — アクティブ開発]
  swing_detector.py ──→ window_scanner.py ──→ CSV ──→ exit_simulator.py
  entry_logic.py   ──┘  (check_15m_range_low)        (方式B: 独自決済)

[出力層]
  window_scanner.py ──→ logs/window_scan_entries.csv
                    ──→ logs/window_scan_plots/*.png
  exit_simulator.py ──→ logs/window_scan_exits.csv
                    ──→ コンソール比較レポート
```

---

## 6. #026c完了後に更新すべき箇所（チェックリスト）

### ドキュメント更新
- [ ] EX_DESIGN_CONFIRMED-2026-04-xx.md 新規作成
  - [ ] エントリー方式: 指値（neck+7pips）に更新
  - [ ] ENTRY_OFFSET_PIPS=7.0 追記
  - [ ] 検出数・パターン分布を更新
  - [ ] 方式B決済ロジックを正式記載
  - [ ] P&L結果（#026c版）を記載
- [ ] ADR-2026-04-xx.md 新規作成
  - [ ] D-8 / D-9 / E-7 を本ドラフトから統合
  - [ ] 未解決テーブル更新
- [ ] SYSTEM_OVERVIEW-2026-04-xx.md 新規作成
  - [ ] exit_simulator.py の追加を反映
  - [ ] ENTRY_OFFSET_PIPS パラメータ追加

### NLM更新
- [ ] 新 EX_DESIGN を NLM に source_add
- [ ] 新 ADR を NLM に source_add
- [ ] 新 SYSTEM_OVERVIEW を NLM に source_add
- [ ] SYSTEM_GUIDE の参照先マップ更新 → NLM に source_add

### プロジェクトナレッジ（Claude.ai）更新
- [ ] 新 ADR を添付ファイルとして差し替え
- [ ] 新 EX_DESIGN を添付ファイルとして追加

### Vault 更新
- [ ] wiki/trade_system/doc_map.md 更新
- [ ] wiki/log.md にwrap-up記録追記

---

**発行: Rex-Evaluator（Opus） / 2026-04-15**
