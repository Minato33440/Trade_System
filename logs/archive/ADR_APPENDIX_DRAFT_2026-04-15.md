# ADR 追記ドラフト — #026b〜#026d 実装記録
# 発行: Rex-Evaluator（Opus） / 作成日: 2026-04-15
# 用途: #026d完了後のwrap-upでADR本体（ADR-2026-04-14_2_2.md）に統合する
# ステータス: D-10追加済み・wrap-up待ち

---

## ⚠️ ADR 採番確定メモ（Evaluator 権限・2026-04-15）

このドラフトの番号と ADR 本体統合時の正式採番:

| ドラフト内番号 | 正式採番 | 内容 | 時系列 |
|---|---|---|---|
| D-8（現在）| **D-9**（統合時） | WICKTOL→ENTRY_OFFSET置換（#026c） | #026c |
| D-9（現在）| **D-8**（統合時） | exit_logic.py 方式B迂回（#026b） | #026b ← 時系列先 |
| D-10（新規）| **D-10**（そのまま） | 4H構造優位性フィルター（#026d） | #026d |

**wrap-up 時に ADR 本体へ統合する際は、D-8/D-9 を入れ替えて採番すること。**
Planner は指示書内で「D-10」を参照すること（REX_026d_spec.md 修正済み）。

---

## D-8（ドラフト番号）→ 統合時 D-9: WICKTOL_PIPS の役割変更（#026c）

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

## D-9（ドラフト番号）→ 統合時 D-8: exit_logic.py 方式B迂回（#026b実装時）

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
検証は #026d 完了後に再度実施すべき。

**将来的な対応選択肢**:
```
選択肢A: exit_logic.py を凍結解除して manage_exit() を修正
  → #018 ベースラインへの影響を評価する必要がある
  → backtest.py が manage_exit() を呼んでいる場合、ベースライン崩壊リスク

選択肢B: exit_simulator.py の方式B を正式な決済エンジンとして確定（推奨）
  → exit_logic.py の manage_exit() は旧版として凍結保持
  → 新しい決済ロジックは exit_simulator.py に集約

選択肢C: exit_logic_v2.py を新規作成
  → manage_exit_v2() に正しい段階定義を実装
  → exit_simulator.py から v2 を呼ぶ
```

**Evaluator推奨**: 選択肢B（新規ファイル自己完結性 F-3 + 凍結ファイル保護 F-4）

**教訓**: 凍結ファイルの内部ロジックが ADR の最新定義と乖離する場合、
凍結を解除するのではなく、新しいファイルに正しいロジックを実装する。
凍結の目的は「ベースライン再現性」であり、ロジックの正しさではない。

---

## D-10（新規）: 4H構造優位性フィルター（#026d）

**症状**: #026c の #07 / #11 で stage2_breakeven_stop の PnL が
マイナスまたは過少（#07: -13.10 / #11: +5.00）

**原因**:
stage2_breakeven_stop の PnL = 50% × (neck_4h - entry_price)
`#07` の -13.10 → `neck_4h < entry_price` が確定。

これは「4H neck ブレイク後の下長髭裏確認パターン」が原因:
```
neck_1h (1H SH) ─────  ← ブレイク後に 1H が新高値を形成
neck_4h (旧 4H SH) ──  ← すでにブレイクされた水準
sl ≈ sl_4h ≈ sl_1h ──  ← 下長ヒゲで SL タッチ → 15M DB 形成
entry = neck_15m + 7pips → neck_4h を上回ってしまう
```

この状態では `neck_4h < neck_1h`（MTF 逆転状態）が成立している。

**修正（#026d）**:
```python
# neck_4h < neck_1h の場合はエントリー除外
if neck_4h < neck_1h:
    continue
```

**根拠**: `sl_4h ≈ sl_1h`（#020 検証済み・100% 一致）なので
```
4H-SwgH の値幅 = neck_4h - sl_4h
1H-SwgH の値幅 = neck_1h - sl_1h
↓ sl_4h ≈ sl_1h により
neck_4h >= neck_1h ⟺ 4H値幅 >= 1H値幅
```

**教訓**:
- neck_4h が半値決済として機能するには neck_4h >= neck_1h（4H が 1H を支配）が前提
- これは ADR F-1（トップダウン原則）のエントリー検証への直接応用
- 追加パラメータゼロ・閾値チューニング不要
- 除外対象は「4H neck 裏確認パターン」という特定の市場構造

---

## E-7. エントリー方式の転換（#026c設計判断）

実体越え次足始値 → 指値到達方式（詳細は上記 D-8 参照）

**エントリー判定方式の変遷**:
```
#001〜#024a: sh_vals.max() 基準（レンジ最高値）
#025:        sh_vals.iloc[0] 基準（固定ネック・SL以降初回SH）
#026a:       sh_before_sl.iloc[-1] 基準（統一neck・SL直前の最後のSH）
#026c:       統一neck + 7pips 指値（構造的エントリー位置の固定）
```

**ENTRY_OFFSET_PIPS = 7.0 の根拠**:
旧 WICKTOL_PIPS = 5.0 + マージン 2.0 pips。#026b 正常ケースで entry - neck が 5〜15 pips に分布。

---

## 未解決・経過観察中の問題（追記分・2026-04-15）

| 問題 | 発見時期 | 状態 | 備考 |
|---|---|---|---|
| exit_logic.py 方式B迂回 | #026b実装 | 方式Bを正式採用で検討中 | D-9（統合時D-8）。選択肢B推奨 |
| WICKTOL → ENTRY_OFFSET 置換 | #026c設計 | #026cで対応完了 | D-8（統合時D-9）|
| 4H構造優位性フィルター | #026c結果 | #026dで対応中 | D-10 |
| #07 4H neck ブレイク裏確認 | #026c結果 | **#026dで除外（D-10）** | neck_4h < neck_1h |
| #11 neck_4h 余白不足 | #026c結果 | #026dで部分対応（確認要） | #11 は neck_4h > neck_1h なら残存 |
| IHS 0件化 | #026a | 設計上の既知制約 | Phase 2で検討 |
| ENTRY_OFFSET_PIPS=7.0 妥当性 | #026c設計 | #026d完了後に再検証 | 旧neckベースの分析値 |

---

**発行: Rex-Evaluator（Opus） / 2026-04-15**
**D-10 追記 / 採番メモ追加: 2026-04-15（Planner + Evaluator）**
