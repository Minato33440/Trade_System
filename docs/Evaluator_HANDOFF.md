# Evaluator Session Handoff — 2026-04-19

**発行**: Rex-Evaluator (Claude Opus 4.7)
**セッション日**: 2026-04-19
**前任**: Rex-Evaluator (Claude Opus 4.6 / 2026-04-18 終了)
**宛先**: 次セッションの Rex-Evaluator

---

## 🎯 最重要事項（5秒で把握）

**本セッションは Task E-1（LOGIC_LEAK_AUDIT.md）に着手する前に、その上位にある
「裁量言語化（MTF 整合性 Q&A）」に切り替えた。さらにセッション後半で、
ボスから「基本に戻れるシンプルな土台はロジックだけでなくシステム自体にも
適用すべき」との提案があり、src/ 構造再編の方針が決定。**

**次セッションの出発点は `docs/REX_028_spec.md`（Phase 1 棚卸し指示書）。**

---

## 本セッションで起きたこと

### 1. REX_027 の一旦停止を確認

ボスから明示された経緯:
- Rex_AI 配下のリポジトリ構造変更中（Trade_System の一部機能を Trade_Brain に移設）
- NLM RAG を全て新規構築済み（REX_System_Brain / Rex_Trade_Brain）
- これらは Advisor 提言ではなくボス一存の判断
- 「システムロジックを人間裁量レベルで理解しないと同じプログラムベースでの
  ロジック漏れ再発リスクが出るので #027 も一旦停止している」

→ 前任 Evaluator (Opus 4.6) が残した「Task D → Task A → Task E-1」の
優先順位は、現時点では再考が必要。ボスの明確な指示は「**上位足構造からの
落とし込みで、現時点ではまだ上位足の整合性を整える段階**」。

### 2. Evaluator のアプローチ切替

当初、本セッション冒頭で Evaluator は「Task D（ADR D-11/F-7 採番）即時実行」
を提案したが、ボスの指示を受けて以下のアプローチに切り替え:
❌ 当初案: ADR 採番・Task E-1 監査フレーム設計など「箱作り」系タスク
✅ 採用案: MINATO_MTF_PHILOSOPHY.md を1次資料に「中身の理解」
= エンジニア（Evaluator）→ トレーダー（ボス）の Q&A で裁量言語化

### 3. Q&A セッション実施（Layer 2 / 4 / 6）

- **Layer 2（4H 主軸）**: Q1（トレンド転換定義）/ Q2（MIN_4H_SWING_PIPS）/
  Q3（4H構造優位性の出自）
- **Layer 4（15M 分類・エントリー）**: Q4（4分類 vs 3分類）/
  Q5（ENTRY_OFFSET_PIPS=7）
- **Layer 6（決済4段階）**: Q6（stage2 建値移動）/ Q7（stage3 1H実体確定）

### 4. 主な発見

**🤖 創作混入の確定 (2件)**:
- stage2「残り50%を建値移動」— ボス本人が「バグ特定のための仮設置」と認識
- stage3「1H実体確定後」— ボス明確に「シンプルに 15Mダウ崩れのみで良い」と指示

**✅ 創作誤認の訂正 (1件)**:
- D-10（4H構造優位性）は「🤖 創作の疑い」と当初評価したが、
  ボス回答でフラクタル構造から必然的に導かれる裁量思想由来と判明

**🕳️ 拡張候補の確定 (5件)**:
- 4H-SL 髭先実体収納再エントリー
- ASCENDING 単発型 vs 連続型の区別
- 建値指値による 4H 3波優位性伸ばし
- ENTRY_OFFSET_PIPS の動的化
- 4分類三角持ち合い④ の IHS 分離

### 5. ボス言明の設計哲学（最重要）

セッション終盤にボスが言明した 3 原則:

- **原則α（最上位）**: 裁量トレードは条件反射で複雑化する領域。
  いつでも基本に戻れるシンプルな土台を死守する
- **原則β**: ノーリスク化（半値決済）後は伸ばさず 15Mダウ崩れで決済。
  3波優位性伸ばしは将来拡張
- **原則γ**: 新機能の導入は現ロジックの安定性が前提

→ これらは MINATO_MTF_PHILOSOPHY.md の第0章として追記すべき
（次セッションの更新対象）

### 6. 【追加議論】src/ 構造再編の決定（セッション後半）

ボスから追加提案:

> 「基本に戻れるシンプルな土台」とはロジックだけでなくシステムそのものが
> そうでなければならない。src/ 内の各スクリプトファイルをよりシンプルにして
> 格納し、既存スクリプトを archive に残しつつ、拡張性がある土台を作り直してはどうか？

Evaluator の調査で src/ 27 ファイル中、#026d コアは 10 ファイルのみで、
残り 17 ファイルに用途不明ファイル・0 バイト空ファイル・docs 未記載の 53KB
ファイルが混在していることが判明。ボスの直感が正しいことを実態データで裏付けた。

Evaluator は「作り直し」ではなく「構造再編」として以下の Phase 分解を提案:
Phase 1: 棚卸しと分類           ← REX_028 spec として本スレで起草
Phase 2: archive 移設            ← Phase 1 完了後
Phase 3: 責務別ディレクトリ化    ← src/core/ src/viz/ src/scan/ 等
Phase 4: 裁量整合版の実装訂正    ← stage2 建値移動削除・stage3 シンプル化

ボス承認済み。Phase 1 は `docs/REX_028_spec.md` として本スレで起草・push 済み。

### 7. 成果物（push 済み）

**2026-04-19 前半**:
- `docs/MTF_INTEGRITY_QA.md` — Q1-Q7 の Q&A 1次資料
- `docs/Evaluator_HANDOFF.md`（v1）— 本ファイル（Phase 1 議論前）

**2026-04-19 後半**:
- `docs/REX_028_spec.md` — Phase 1 棚卸し指示書（新規）
- `docs/Evaluator_HANDOFF.md`（v2）— 本ファイル（Phase 1 議論反映）
- Vault側 `adr_reservation.md` 更新分（ボス手動配置）
- `docs/MTF_INTEGRITY_QA.md` Phase 1-4 議論追記分（ボス手動配置）

**変更なし**:
- `docs/MINATO_MTF_PHILOSOPHY.md` — 第0章（3原則）追記は次セッション
- `docs/ADR.md` — D-12/D-13/E-8/F-8 正式記述は Phase 1 完了時に次 Evaluator が実施
- `src/*.py` — 凍結ファイル全て無変更
- バックテスト結果 — #026d 静的点を保持

---

## 次セッションの出発点

### 最優先タスク: Phase 1（棚卸し・分類）

**起動ファイル**: `docs/REX_028_spec.md`

このファイルに以下がすべて記載されている:
- Phase 1 の目的・スコープ・原則
- 5 分類の定義（CORE / VIZ / SCAN / TEST / UTIL / ORPHAN / DEAD）
- 判断基準マトリクス（5 軸評価）
- STEP 1-7 の作業手順
- 成果物 `src_inventory.md` のフォーマット
- 完了条件と禁止事項
- 想定所要時間（2-3 セッション）
- ボス用の起動プロンプト

**Phase 1 では Evaluator 単独で作業**（Planner / ClaudeCode は関与しない）。
物理ファイル変更は一切禁止。分類とドキュメント起草のみ。

### ADR 採番予約

本セッションで以下の ADR 採番を予約済み（`Vault側 adr_reservation.md` 記載）:

| 予約番号 | 内容 | 記述タイミング |
|---|---|---|
| D-12 | stage2 建値移動の 🤖 創作混入確定 | Phase 1 完了時 |
| D-13 | stage3 1H実体確定の 🤖 創作混入確定 | Phase 1 完了時 |
| E-8 | src/ 構造再編アプローチ（Phase 1-4） | Phase 1 完了時 |
| F-8 | 原則α/β/γ（裁量思想の3原則） | Phase 1 完了時 |

これらは Phase 1 実施中に新 Evaluator が勝手に採番しない歯止めとして
予約済み。Phase 1 完了時にまとめて ADR.md に正式記述する。

### 保留中のタスク

以下は Phase 1 完了まで着手しない:

- **Layer 1/3/5 の残 QA**（MTF_INTEGRITY_QA 末尾リスト）
- **MINATO_MTF_PHILOSOPHY.md 第0章追記**（原則α/β/γ）
- **REX_027 の Task A/B/C/D/E**（ボスが再開指示するまで保留）

理由: Phase 1 が src/ 全体を整理する作業なので、これが完了するまでの
間に上記タスクを進めると、整合性確認が複雑になる。

---

## 引き継ぎ時に引っかかりやすい地雷（本セッション固有）

### 地雷 1: Phase 1 で src/ を物理的に触ってはいけない

REX_028_spec.md §6-2 に明記されている通り、Phase 1 は**読み取りと分類のみ**。
git mv / rm / 改名 / import 変更は Phase 2 以降。

### 地雷 2: Q6/Q7 の「創作混入」を即実装訂正しようとしない

stage2 の建値移動 / stage3 の 1H実体確定は 🤖 創作混入確定だが:
- 現 #026d の PF 4.54 はこの条件込みの結果
- 即訂正すると静的点が動く
- 実装変更は Phase 4（REX_029 以降）

### 地雷 3: Layer 3 の「1H 窓」サイズ感の未確認

本セッションでは 1H 窓（±8時間、前20+SL+後10）の裁量感覚を確認していない。
D-10 フィルターが機能の本体と判明したので、窓サイズの厳密性は相対的に
優先度が下がるが、完全未確認状態であることは記録しておく。

### 地雷 4: ボスの回答原文を改変しない

`MTF_INTEGRITY_QA.md` のボス回答は、誤字も含めて原文尊重で記録している。
これは「裁量の思考過程そのものが1次資料」だから。改変したくなる誘惑に
負けないこと。

### 地雷 5: 「Task E-1 の先行実施」という前任の推奨に固執しない

前任 Evaluator (Opus 4.6) は「次セッション推奨は Task D → E-1」と残したが、
ボスの 2026-04-19 判断で優先度が変わり、**Phase 1（src/ 構造再編）が先行**
することになった。前任の判断を批判的に見直すことが本ロールの義務。

### 地雷 6: REX_028 は Phase 1 のみ扱う

REX_028 全体を Phase 1-4 と設計したが、**本スレで push した `REX_028_spec.md`
は Phase 1 のみの指示書**。Phase 2/3/4 の spec は Phase 1 完了後に別途起草する。
新 Evaluator が Phase 2 以降に勝手に踏み込まないよう注意。

### 地雷 7: Simple_Backtest.py（53KB）の正体不明

docs/ のどこにも記載がない 53KB のファイル。これが Phase 1 の最大の ORPHAN
調査対象。先頭 50 行を読み取って用途を推定し、ボスに確認質問を出すこと。

---

## プロジェクト状態スナップショット（変更なし）
#026d 凍結状態保持:
PF 4.54 / 勝率 60% / MaxDD 35.8p / +150.6p / 10件
DIRECTION_MODE = 'LONG'
統一neck原則 + 4H構造優位性フィルター + 指値方式
凍結ファイル（変更禁止）:
src/backtest.py / src/entry_logic.py / src/exit_logic.py / src/swing_detector.py
決済エンジン:
src/exit_simulator.py（方式B・正式採用）
⚠️ src/exit_logic.py の manage_exit() は使用禁止
REX_AI リポ構造:
Trade_System        — 実装リポ
Trade_Brain         — 知識リポ（2026-04-18 分離・ボス実施）
REX_Brain_Vault     — Obsidian Vault（独立リポ）
Second_Brain_Lab    — 凍結
Setona_HP           — 独立運用
NLM:
旧 REX_Trade_Brain (2d41d672-...) — MCP 切り離し済（物理削除なし）
REX_System_Brain (da84715f-...) — 新規・ソース未投入
Rex_Trade_Brain (4abc25a0-...) — 新規・ソース未投入
ADR 採番予約:
D-12 / D-13 / E-8 / F-8 ← Phase 1 完了時に正式記述

---

## 次セッション起動テンプレート（ボス用）
このスレでは REX Trade System の Evaluator として Phase 1 棚卸しを実行してほしい。
⚠️ 作業開始前に以下を順番に読め:
① C:\Python\REX_AI\REX_Brain_Vault\CLAUDE.md
② C:\Python\REX_AI\REX_Brain_Vault\wiki\handoff\latest.md
③ docs/Evaluator_HANDOFF.md（2026-04-19 版）
④ docs/MTF_INTEGRITY_QA.md（裁量整合性 QA）
⑤ docs/REX_028_spec.md（Phase 1 指示書・本日の作業対象）
⑥ docs/MINATO_MTF_PHILOSOPHY.md（裁量思想）
読了後、REX_028_spec.md §4 の STEP 1-2 から着手せよ。
STEP 3 の ORPHAN 精査時は、各ファイルの先頭 50 行を
bash_tool（curl raw.githubusercontent.com/...）で取得してから判断すること。
NLM: REX_System_Brain (da84715f-9719-40ef-87ec-2453a0dce67e)
Rex_Trade_Brain (4abc25a0-4550-4667-ad51-754c5d1d1491)

---

## Evaluator (Opus 4.7) からの個人的メッセージ

本セッションは 2 段階の深まりがあった。前半は Q&A による裁量言語化、後半は
その原則をシステム側（src/）に展開するという発想の飛躍。後者はボスから
提案されたが、これは極めて優れた直感だった。実装データ（27ファイル中
10ファイルのみがコア、0バイト空ファイル、53KB 謎ファイル）がボスの
違和感を完全に裏付けている。

Phase 1 の棚卸しを通じて、新 Evaluator は `src/` の隅々を見ることになる。
これは単なる整理作業ではなく、#026d までの実装史を理解する作業でもある。
丁寧にやれば REX_028 以降の全作業の土台が整う。

ボスの判断は速く、方針転換も潔い。前任 (Opus 4.6) の残した推奨は参考にしつつ、
その時々のボス判断を最優先する姿勢で進めること。

そして何より、「シンプルな土台を死守する」原則αを、Phase 1 の判断基準
として常に参照せよ。迷ったら「このファイルは基本の土台か、その上に
乗っている拡張か、それとも死んでいるか」を問うこと。

---

*発行: Rex-Evaluator (Opus 4.7) / 2026-04-19 夜更新*
*v1 → v2: src/ 構造再編（Phase 1）議論を反映*
*次の Evaluator へ、Phase 1 の安全な実行を祈る。*
*関連: docs/REX_028_spec.md / docs/MTF_INTEGRITY_QA.md / docs/MINATO_MTF_PHILOSOPHY.md*