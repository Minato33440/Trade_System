Trade_System — Astra 引き継ぎ確認

確認日: 2026-09-07 / 対象: `C:\Python\REX_AI\Trade_System` / 統括: Astra

指定ハンドオフ、Astra/Hermes導入計画、現行設計、実コード、Git状態、保存済みCSVを照合した。さらに必要なコードと入力をタスク内の作業領域へコピーし、現行 #026d のスキャナと決済シミュレーターを再実行した。

**#026d は現在の環境でも再現できる。Phase 1/2 は完了、Phase 3/4 は未着手。ただしハンドオフの未解消一覧には、すでに訂正された項目が含まれる。** リアルタイムに同じシグナルを出せることや、裁量思想との完全な整合性までは、この再現成功によって保証されない。

## 確認した実装と再現結果

正式な現行経路は `window_scanner.py → window_scan_entries.csv → exit_simulator.py → window_scan_exits.csv`。旧 `backtest.py` は #018 の比較用基準で、今回の #026d 再現には使っていない。

| 項目 | 保存された #026d | 今回の再実行 |
|---|---:|---:|
| トレード数 | 10 | 10 |
| 勝ち数 / 勝率 | 6 / 60.0% | 6 / 60.0% |
| PF | 4.54 | 4.5352112676（小数2桁で4.54） |
| 総損益 | +150.6 pips | +150.6 pips |
| MaxDD | 35.8 pips | 35.8 pips |
| DB / ASCENDING / IHS | 2 / 8 / 0 | 2 / 8 / 0 |
| stage1 / stage2 / stage3 | 7 / 1 / 2 | 7 / 1 / 2 |
| 4H優位性フィルター除外 | 3 | 3 |

- エントリーCSVと決済CSVは、列順・全セル値に加えて **SHA-256が一致し、バイト単位で同一**。
- PNG 10枚を作業用コピー内に生成。画像内容の目視評価は今回の対象外。
- 4H優位性条件 `neck_4h >= neck_1h` とエントリーオフセット7pipsは全10件で成立。
- 元データは83,112行。5M OHLCの欠損除去後に実際のスキャンが使ったのは82,626本。UTCの元データ範囲は2024-03-13 00:00〜2026-03-12 23:55。
- スキャナは33窓を処理し、10件を生成。窓の実時間幅が35時間を超える警告が13件出る。バー本数による窓幅と休場をまたぐ実時間差の扱いは、追加の確認対象。
- Python 3.13.3 / pandas 2.3.3 / numpy 2.4.2 / pyarrow 23.0.1 / matplotlib 3.10.8 / mplfinance 0.12.10b0。
- スキャナ6.743秒、決済シミュレーター0.713秒。これは今回の1実行の所要時間で、性能比較ではない。
- 元の凍結4ファイル、実行対象、入力データ、既存CSV、INDEX、ハンドオフの計11ファイルは、前後のSHA-256が一致。

数値・ファイルハッシュ・実行結果は [検証記録](./026d-verification-2026-09-07.json) に保存した。#018のPF 5.32などは過去文書の参照値であり、今回は再実行していない。

根拠: [過去の026d結果](C:/Python/REX_AI/Trade_System/logs/coordination/execution_results/026d_result.md:40)、[現行設計](C:/Python/REX_AI/Trade_System/docs/EX_DESIGN_CONFIRMED.md:111)、[スキャナ入口](C:/Python/REX_AI/Trade_System/src/window_scanner.py:380)、[決済入口](C:/Python/REX_AI/Trade_System/src/exit_simulator.py:282)。

## Gitと到達点

ローカルHEADは `26df950`（2026-07-10、AGENTS更新）。`src/` を対象にした最終コミットは `ed9bc00`（2026-04-20、Phase 2整理）。現役12ファイルは引き続き `src/` 直下にあり、予定された `src/core/`、`src/viz/`、`src/scan/`、`src/tests/` は未作成。

確認開始時から次の未コミット項目が存在した。

```text
 M logs/coordination/INDEX.md   # 41行の既存追記
?? docs/hannd_off/
```

凍結4ファイルの `git diff HEAD` は差分ゼロ。今回リポ本体に編集は加えていない。Git表示ではローカルに保存された `origin/main` と同じ位置だが、fetchは実施しておらず、最新リモートとの一致までは確認していない。

ハンドオフ冒頭の「約2ヶ月のブランク」は、実装停止の2026-04-20から数えると整合しない。2026-09-07までは140日、約4か月半。governanceの更新も7月2日以後に記録がある。

根拠: [Phase 1/2の到達点](C:/Python/REX_AI/Trade_System/docs/SYSTEM_OVERVIEW.md:331)、[既存の028指示書](C:/Python/REX_AI/Trade_System/logs/coordination/instructions/REX_028_spec.md:1)。

## ハンドオフのドリフト一覧を現在の実物で読み直した結果

| ハンドオフ項目 | 今回確認した状態 |
|---|---|
| D-A: INDEXの026d未完表記 | **訂正済み**。旧表は履歴として残り、2026-09-07の追記が完了と次のPhase 3を明記。今回開始時点ですでに存在した未コミット追記。 |
| D-B: ADR冒頭の旧role | **指定箇所は訂正済み**。7月3日のM-4に記録。 |
| D-C: maintenanceのD-x番号衝突 | **訂正済み**。M-xへ切り替え、旧記録の読み替え注記あり。 |
| D-D: 構造図と実体 | **一部残存**。logs/scratch等はすでに反映。main.py、configs/settings.py、docs旧地層の説明は実体と不一致。README、Rex_Trade_Wiki、Web_Tracker、tests等の図への反映も残る。後2ディレクトリは空。 |
| D-E: ADR末尾の宛先 | **指定見出しは訂正済み**。「不変ルール（全engine共通）」。 |
| D-F: 週次系除去の完了記録 | rootのREDIUM.mdとlogs/gmは不在。ただし7月3日の記録にはarchive側のREDIUM未処理が残る。archive内容は参照していないため、整理全体の完了は未確認。 |
| D-G: コードフェンス剥離 | 現行SYSTEM_OVERVIEWのツリー・依存マップでは指摘を再現しない。文書全体の表示完全性は未検証。 |
| D-H: AGENTSヘッダ日付 | **訂正済み**。現行は2026-07-09 / 2026-07-02の履歴を記載。 |
| D-I: KPS仕様v4 | **古い前提が残る**。scratch位置・claudecode経路・未着手表記を現在の操作指示として使わない。 |
| D-J: rootの旧Handover.md | **残存**。存在のみ確認。 |

根拠: [INDEXの追記](C:/Python/REX_AI/Trade_System/logs/coordination/INDEX.md:69)、[7月3日のM-4](C:/Python/REX_AI/Trade_System/logs/coordination/maintenance_log.md:92)、[構造図](C:/Python/REX_AI/Trade_System/docs/SYSTEM_OVERVIEW.md:55)、[AGENTS](C:/Python/REX_AI/Trade_System/AGENTS.md:1)。

指定箇所が訂正されたことと、全資料から旧roleがなくなったことは別。例えばADRの原則γの図には、将来動作をPlannerへ割り当てる表記がなお残る（680行）。

## 再開前に扱う実質的な課題

### 1. Phase 3の移設案と凍結条件の整合

ハンドオフは凍結4ファイルも `src/core/` へ移す。一方、AGENTSは現在の4つのパスに対するdiffゼロを要求する。ファイル移動だけでも旧パスには削除差分が生じる。

さらに `Path(__file__).resolve().parents[1]` でリポルートを求めるコードが多いため、1階層深く移動するとdata/logsの参照先が変わる。`from src.*` と一部の直接importも追従が必要。したがって、単純なgit mvでは「ロジック・動作影響ゼロ」を満たせない。

Astraの着手案は、まず凍結4ファイルを現位置に保持する段階移行を検討し、非凍結ファイルの責務整理、旧入口互換、パス解決、CSV全件一致を作業仕様に落とすこと。全12ファイルの移設を採用する場合は、凍結の保証対象を旧パスdiffゼロからどの同一性条件へ変更するかを明示する。この文書は移設案の整理であり、canon変更や移設方式の採用記録ではない。

根拠: [凍結条件](C:/Python/REX_AI/Trade_System/AGENTS.md:44)、[移設案](C:/Python/REX_AI/Trade_System/docs/hannd_off/2026-09-07_handoff.md:120)、[ルート算出](C:/Python/REX_AI/Trade_System/src/window_scanner.py:28)、[決済側のルート算出](C:/Python/REX_AI/Trade_System/src/exit_simulator.py:19)。

### 2. 裁量思想文書と訂正方針の不一致

現行実装にstage2の建値ストップとstage3の1H確定待ちがあることはコードで確認できる。ADR D-12/D-13はこれらを裁量にない追加条件として記録し、Phase 4で訂正する方針。

ところが「最上位辞書」と案内される `MINATO_MTF_PHILOSOPHY.md` の203〜205行には、建値移動と残りを走らせる説明が今もある。ADR D-12の「思想文書は半値決済とだけ記述」という説明とは実物が一致しない。次のAgentが思想文書だけから仕様を起こすと、訂正対象を再導入する恐れがある。

設計時には、思想文書、4月19日のボス回答、ADRの採用方針を対応表にし、原文・解釈・現在採用する条件を分ける。到達、上抜け、半値決済後という段階の境界もその表で固定する。PFの再現成功を、裁量整合性の合格と扱わない。

根拠: [思想文書の現記載](C:/Python/REX_AI/Trade_System/docs/Base_Logic/MINATO_MTF_PHILOSOPHY.md:203)、[ADR D-12](C:/Python/REX_AI/Trade_System/docs/ADR.md:242)、[ADR D-13](C:/Python/REX_AI/Trade_System/docs/ADR.md:279)、[ボス回答を含むQ6/Q7](C:/Python/REX_AI/Trade_System/docs/Base_Logic/MTF_INTEGRITY_QA.md:310)、[現コード](C:/Python/REX_AI/Trade_System/src/exit_simulator.py:180)。

### 3. エントリー時点で利用できる情報の確認

現在の10件はすべて `entry_ts < ts_4h`。例えば1件目のエントリーは2024-03-26 12:35 UTC、記録された4Hスキャンイベントは2024-03-27 20:00 UTC。

`scan_4h_events()` はある4H時点で方向と確定済みSLを調べ、そのSLを基準とした過去の窓をスキャンする。15Mパターンの判定にも窓全体を渡す。Swing検出は左右n本を必要とする。この構成の再現性は確認できたが、エントリー時点までに利用可能な情報だけで同じシグナルが得られるかは未検証。

これは将来データ参照を詳しく調べるべき具体的な観測であり、10件すべての売買が不可能だったという断定ではない。動的アルゴとして進める際には、各価格時刻・Swing確認時刻・判断時刻を分け、時点を打ち切った入力によるリプレイを検証対象にする。コスト、滑り、運用成績、未知期間への有効性も今回の検証範囲外。

根拠: [4Hイベント](C:/Python/REX_AI/Trade_System/src/window_scanner.py:72)、[窓全体でのパターン判定](C:/Python/REX_AI/Trade_System/src/window_scanner.py:171)、[過去窓のスキャン](C:/Python/REX_AI/Trade_System/src/window_scanner.py:412)、[左右の足によるSwing確認](C:/Python/REX_AI/Trade_System/src/swing_detector.py:19)、[保存CSV](C:/Python/REX_AI/Trade_System/logs/window_scan_entries.csv:2)。

### 4. 検証の土台

rootの `tests/` は空。`src/test_1h_coincidence.py` と `src/verify_4h1h_structure.py` は、データとCSV/プロットを使う検証スクリプトであり、Phase 3後のimportと旧入口互換を保証する自動テスト群は確認できない。

今回確立したスキャナ→シミュレーターの再実行とCSV全件一致を回帰確認の最初の基準にできる。次の段階では入口互換と時点整合性を狙った検証を追加し、構造変更と売買条件の訂正を別の差分として評価する。

## このスレの担当とAgent運用

| 担当 | 作業範囲 |
|---|---|
| Astra | Bossとの設計対話、PlannerとEvaluatorの判断機能、作業分割、矛盾の裁定、根拠確認、受入判定 |
| GPT-5.6 Terra | 対象を限定した実装、依存関係調査、テスト修正、別コンテキストでのレビュー |
| GPT-5.6 Luna | ファイル・ログ・数値の抽出、索引の突合、証拠表の作成 |
| Boss | 裁量思想と設計上の採用判断、必要なcanon昇格の最終判断 |

今回もLunaをドリフト一覧、TerraをPhase 3着手可能性の調査へ実際に委任し、Astraがコードと再実行結果を確認した。Lunaのディレクトリ存在判定に1件の誤りがあり、Astraの実物照合で発見して再確認・訂正した。Agent間の一致だけを根拠とせず、重要な判断はファイル・コマンド結果へ戻す。

この配分は公式のモデル用途説明とも整合するが、品質・費用の優越は今回の1監査からは主張しない。[公式モデルガイド](https://learn.chatgpt.com/docs/models#choosing-sol-terra-and-luna)

現段階はCodex内のAstra＋GPT下位モデルで運用できる。9月5日の計画書は設計提案であり、提案配置の `C:\Python\REX_AI\MCP_Servers\Hermes-Runtime` と `C:\Users\Setona\AppData\Local\hermes-broker` は今回の確認では存在しない。このセッションにもhermes-runtimeツールは公開されていない。他の場所に実装が存在するかの全域探索はしていない。

既存Claude brokerを維持し、将来必要になった段階でHermesの実行管理・Provider切替・状態保存・使用量記録へ接続する。AstraによるTrade_System統括と、Vaultの `bridges/` への書込所有は区別する。今回の統括引継ぎだけで、その所有権を移転したとは扱わない。

根拠: [Astra/Hermes計画](C:/Python/REX_AI/REX_Brain_Vault/raw/system_build/astra-hermes-broker-plan-2026-09-05.md:3)、[Vaultの共有記録と所有](C:/Python/REX_AI/REX_Brain_Vault/AGENTS.md:15)。

## 3リポジトリの役割と次の作業

| リポジトリ | 担当 |
|---|---|
| Trade_Brain | 市況履歴、週次更新、レジーム判断などの静的な分析・知識層。別スレが継続担当。 |
| Trade_System | MTF構造、シグナル、エントリー・決済、バックテストなどの動的ロジック。本スレの担当。 |
| REX_Brain_Vault | 共有仕様、判断履歴、記憶、リポ間の接続を支える司令塔の情報基盤。実行状態管理は将来のRuntime側と接続。 |

将来の合流点として、市況レジームから戦略の有効条件やロットへつなぐ方向性は維持する。`plotter.py` の両リポ由来の関数を共存保持する既存方針も引き継ぐ。

次の作業単位は、**現在の再現結果と残る矛盾を基に、Phase 3専用の実行仕様を具体化すること**。

1. 解消済みドリフトと残件を区別し、今回の監査を現状確認の参照にする。
2. 凍結4ファイルの扱い、importとパス解決、旧入口互換、CSV一致の受入条件をPhase 3仕様へ落とす。
3. 構造変更をその仕様に沿って限定的に実装・検証する。
4. Phase 4では原文・ADR・仕様の対応を確定し、裁量整合版の決済へ訂正。現行 #026d と別の基準結果を保存する。
5. 動的運用へ進む前に、時点ごとの情報可用性を確認するリプレイを通す。リポ間統合はその土台の上で進める。

今回の成果は進捗確認と再現検証。設計採用、ソース移設、取引ロジック変更、コミット、push、Provider設定変更は含めていない。
