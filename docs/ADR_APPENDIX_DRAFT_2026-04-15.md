# ADR 追記ドラフト — #026c 実装前の事前記録
# 発行: Rex-Evaluator（Opus） / 作成日: 2026-04-15
# 用途: #026c完了後のwrap-upでADR本体に統合する
# ステータス: ドラフト（#026c結果で最終化）

---

## D-8. WICKTOL_PIPS の役割変更 — 実体判定バッファ → 指値オフセットへ転換（#026c）

**症状**: #026b結果で stage2 breakeven_stop の4件全てがマイナスP&L。
原因を辿ると、entry_price が neck_4h を超過しており、
これは「5M実体越え確定足の次足始値」方式が急騰局面で
entry を neck から 80pips以上引き離してしまうことに起因する。

**具体例（#04 ASCENDING 2024-12-11）**:
```
neck_15m  = 151.790
entry     = 152.651  ← neck + 86.1 pips（急騰で次足始値が跳ね上がり）
neck_4h   = 152.180  ← entry が既に neck_4h の上
→ stage2 で 50% 決済 = 50% × (152.180 - 152.651) = -23.55 pips
```

**旧パラメータ（#026bまで）**:
```
WICKTOL_PIPS = 5.0   # 5M実体越え判定のバッファ
判定: min(open, close) > neck_15m + WICKTOL_PIPS * PIP_SIZE
執行: 確定足の次の5M始値で成行エントリー
```

**新パラメータ（#026c）**:
```
ENTRY_OFFSET_PIPS = 7.0   # neck_15m からの固定オフセット
判定: bar['high'] >= neck_15m + ENTRY_OFFSET_PIPS * PIP_SIZE
執行: entry_price = neck_15m + ENTRY_OFFSET_PIPS * PIP_SIZE（固定値）
```

**WICKTOL_PIPS の扱い**:
- コード内に残置（他の参照箇所がある可能性）
- エントリー判定では ENTRY_OFFSET_PIPS に完全置換
- 将来的に他の参照がなければ削除候補

**教訓**: エントリー価格が構造的な利確ライン（neck_4h）を超えうる方式は、
どんなに正確なパターン検出をしても決済段階で破綻する。
エントリー位置を構造に対して固定する（指値方式）ことで、
エントリーと決済の関係が常に設計通りになる。

---

## D-9. exit_logic.py 方式B迂回 — manage_exit() の仕様不一致（#026b実装時）

**症状**: #026b の ClaudeCode が manage_exit() の呼び出しを回避し、
独自の決済シミュレーションロジック（方式B）を実装した。

**原因**:
exit_logic.py（凍結ファイル）内の manage_exit() は、
position dict の `neck_1h` を半値決済トリガーとして参照する設計。
しかし ADR D-6（2026-04-14確定）では `neck_4h` が正しい半値決済トリガー。

```
exit_logic.py 内部（推定）:
  段階2判定: bar['high'] >= position['neck_1h']  ← 旧定義（誤）

ADR D-6 確定定義:
  段階2判定: bar['high'] >= position['neck_4h']  ← 正定義
```

exit_logic.py は凍結ファイル（F-4）のため変更不可。
ClaudeCode は矛盾を検出し、manage_exit() を使わず独自実装を選択した。

**ClaudeCode の判断評価**: 正しい。凍結ファイルを変更せずに迂回した。
ただし方式Bの決済ロジックが ADR の段階定義と完全一致しているかの
検証は #026c 完了後に再度実施すべき。

**将来的な対応選択肢**:
```
選択肢A: exit_logic.py を凍結解除して manage_exit() を修正
  → #018 ベースラインへの影響を評価する必要がある
  → backtest.py が manage_exit() を呼んでいる場合、ベースライン崩壊リスク

選択肢B: exit_simulator.py の方式B を正式な決済エンジンとして確定
  → exit_logic.py の manage_exit() は旧版として凍結保持
  → 新しい決済ロジックは exit_simulator.py に集約
  → 推奨: こちらが安全

選択肢C: exit_logic_v2.py を新規作成
  → manage_exit_v2() に正しい段階定義を実装
  → exit_simulator.py から v2 を呼ぶ
```

**Evaluator推奨**: 選択肢B。理由: 新規ファイルの自己完結性（F-3）と
凍結ファイル保護（F-4）の両方を満たす。

**教訓**: 凍結ファイルの内部ロジックが ADR の最新定義と乖離する場合、
凍結を解除するのではなく、新しいファイルに正しいロジックを実装する。
凍結の目的は「ベースライン再現性」であり、ロジックの正しさではない。

---

## E-7. エントリー方式の転換 — 実体越え次足始値 → 指値到達方式（#026c設計判断）

**問題**:
#026b の P&L 結果（PF 0.61 / 勝率 25% / -61.3 pips）が
#018 ベースライン（PF 5.32 / 55% / +91.6 pips）と大幅に乖離。
原因分析の結果、stage2 breakeven_stop の4件全てで
entry_price > neck_4h が成立しており、構造的に利益が出ない
トレードが含まれていた。

根本原因: 「5M実体越え確定足の次足始値」方式では、
急騰・ギャップ・大陽線の局面でエントリー価格が制御不能になる。

**選択肢A（却下）**: entry_price に上限を設ける（MAX_ENTRY_SPREAD_PIPS）
```
if entry_price - neck_15m > MAX_ENTRY_SPREAD_PIPS * PIP_SIZE:
    skip  # エントリー見送り
```
→ 既存ロジック構造を維持。ただし「見送り」は機会損失であり、
  適切な entry_price で入れた可能性を捨てている。

**選択肢B（却下）**: neck_1h 手前をエントリー条件に追加
```
if entry_price >= neck_1h:
    skip  # レイトエントリー除外
```
→ テクニカル的に正しいが、neck_1h の精度が未検証。
  Phase 2 で検討すべき。

**選択肢C（採用）**: 指値方式（neck_15m + ENTRY_OFFSET_PIPS）
```
entry_level = neck_15m + ENTRY_OFFSET_PIPS * PIP_SIZE  # 7.0 pips
if bar['high'] >= entry_level:
    entry_price = entry_level  # 固定値
```

**Cを採用した理由（ボス判断・2026-04-15）**:

1. **損切幅の安定化**: 初動SLが15Mダウ崩れなら、
   エントリー位置が固定されることで損切幅が安定する
2. **指値注文との等価性**: 実トレードでも neck_15m + 7pips に
   指値を置けば同じ結果が再現できる
3. **バックテスト再現性**: 「次足始値」はスリッページに依存するが、
   指値は一意に決まる
4. **構造的レイトエントリー防止**: entry が常に neck 近傍に
   固定されるため、entry > neck_4h が発生しにくくなる
5. **シンプルさ**: ボラティリティ指数（案3）やneck_1hフィルター（案2）
   より実装・検証が容易

**エントリー判定方式の変遷**:
```
#001〜#024a: sh_vals.max() 基準（レンジ最高値）
#025:        sh_vals.iloc[0] 基準（固定ネック・SL以降初回SH）
#026a:       sh_before_sl.iloc[-1] 基準（統一neck・SL直前の最後のSH）
#026c:       統一neck + 7pips 指値（構造的エントリー位置の固定）
```

**ENTRY_OFFSET_PIPS = 7.0 の根拠**:
- 旧 WICKTOL_PIPS = 5.0（ヒゲ許容バッファ）+ マージン 2.0 pips
- #026b 結果の正常ケースで entry - neck_15m が 5〜15 pips に分布
- ⚠️ この値は旧 neck（SL以降 iloc[0]）ベースの分析に基づく
- #026c 完了後に新 neck ベースで妥当性を再検証する

**window_scanner.py 変更の正当性（再確認）**:
- F-4: window_scanner.py は拡張可能ファイル
- エントリー「価格の計算方式」変更であり、「パターン検出ロジック」は不変
- neck_15m の算出ロジック / check_15m_range_low() の呼び出しは変更しない

---

## 未解決・経過観察中の問題（追記分）

| 問題 | 発見時期 | 状態 | 備考 |
|---|---|---|---|
| WICKTOL → ENTRY_OFFSET 置換 | #026c設計 | #026cで対応予定 | D-8参照 |
| exit_logic.py 方式B迂回 | #026b実装 | 方式Bを正式採用で検討中 | D-9参照。選択肢B推奨 |
| #06 15M neck検出バグ | #026b目視 | #027で対応 | ボス指摘。根本はパターン検出側 |
| #07 4H SL検出の誤り | #026b目視 | #027で対応 | 安値切り上げ中のSL認定 |
| #11 15M DB検出失敗 | #026b目視 | #027で対応 | 1H-DB構造は見えるが15M未検出 |
| IHS 0件化 | #026a | 設計上の既知制約 | Phase 2で検討 |
| ENTRY_OFFSET_PIPS=7.0 妥当性 | #026c設計 | #026c完了後に再検証 | 旧neckベースの分析値 |

---

**発行: Rex-Evaluator（Opus） / 2026-04-15 / ドラフト**
