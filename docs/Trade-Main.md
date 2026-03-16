# Trade-Main

## GM 2025-11_to_12 (Archive)
- Archive: Trade_Record/_archive/source_threads_v1/acv-gm-2025-11_to_12.md
- Raw: Trade_Record/_archive/source_threads_v1/raw/
- Note: day-to-day ops are tracked via STATUS.md and weekly logs.

## Purpose (Σ:UCAR-Trade / GM)
- 週次の相場環境・判断更新点を distilled として時系列ストックし、
  将来UCARが経年データから必要要素を抽出してGM分析の材料にする（トレード効率化）。

## How to Navigate (3-layer map)
- Current location: Trade_Record/STATUS.md
- Weekly index (yearly): Trade_Record/logs/gm/weekly/YYYY/_index.md
- Weekly folder (yearly): Trade_Record/logs/gm/weekly/YYYY/YYYY-MM-DD_wkNN/
  - note.md: background / narrative (long OK)
  - meta.yaml: tags / events (machine-readable)
  - review.md: Weekly Review (result + next plan)
- distilled: Trade_Record/versions/distilled/YYYY/

## Workflow (weekly loop)
- Week start / midweek:
  - Append "Weekly Brief" to STATUS.md (short)
- Week end (Fri close):
  - Write "Weekly Review" into weekly folder (review.md)
  - Add 1-line link to yearly _index.md
  - (Optional) extract distilled items for versions/distilled/

## Monday AM（12/22）ラベル付け（※行動トリガー禁止）
- 月曜朝は薄商いで“狩り”混入率が高いので、**A/B/Cの寄り推定**だけ行う（売買判断はしない）。
- 実際の行動は **終値ゲート**で決定（Tokyo close / NY close）。
- テンプレは note.md 冒頭「Monday AM Check」欄を使用（コピペ運用）。
- logging:
  - 月曜朝ラベル → note.md
  - 終値結果（Tokyo/NY）→ note.md Facts欄
  - 週末まとめ → review.md


  # Trade-Main.md | GM Playbook (Week Start)
updated: 2025-12-22 09:40 JST

目的：
- BOJ後のリスクオン回帰局面で「押し目買い先着」を狙う。
- ただし薄商い×ヘッドライン×オプション要因での“行って来い/急落”を想定し、
  終値ゲートで事故を避ける。

運用原則（固定）：
1) 判定は終値優先（暫定＝東京引け / 最終＝NY引け）
2) 追いかけ買い禁止（指値先着）
3) リスクオフ判定は「3点灯（同日）」を最重視
4) 2243/2638はベータが高いので、分割＋弾（現金）を常に確保

今週の主テーマ：
- クリスマスラリー継続の“本物/偽物”を見分ける週。
- USDJPYが高値圏のため、急伸→急落（介入警戒の形）にも備える。

ゲート（最重要）：
- NY引け：
  - USDJPY: 156.59（割れ＝円高再点火） / 157.703（上抜け維持＝上伸び余地）
  - SPX: 6,667（終値割れ＝リスクオフ濃厚）
  - BTC: 84k（終値割れ＝リスクオフ加速の合図になりやすい）
- 東京引け：
  - JP225: 48,657 → 47,377（終値割れ＝リスクオフ点灯）
  - 2243: 2,514 / 2,387
  - 2638: 2,320 / 2,268

3シナリオ即応：
A) 円高急落（リスクオフ連鎖）
- 条件：USDJPY NY終値で156.59割れ（ヒゲではなく終値）
- 行動：追加買い停止、弾温存。サポ割れ終値連続なら拾い直しモードへ。

B) 行って来い（狩り→終値レンジ回帰）
- 条件：重要ライン割れがヒゲで終わり、終値で回帰
- 行動：指値のみ。成行禁止。買い戻しは終値確認後に限定。

C) 事実買い上抜け（リスクオン継続）
- 条件：USDJPY 157.703上抜け維持＋米株の引け確認＋ETF終値確認（2243=2692/2638=2458）
- 行動：追いかけず、浅押し（4H21MA）or 深押し（サポ帯）で再構築。

ヘッジ利確（小さく・ルール化）：
- 目的：押し目弾を増やす（コアは崩さない）
- 目安：2243/2638 各10〜20口
- トリガー：確認ライン近辺で失速 / 米株が確認してこない / USDJPYが加速し過ぎて形が崩れる


# Trade-Main.md — GM Playbook / Operating Manual
updated: 2026-01-03 (JST)

> NOTE: Key gates/levels are “snapshot”. Source of truth is STATUS.md.

## GM 2025-11_to_12 (Archive)
- Archive: Trade_Record/_archive/source_threads_v1/acv-gm-2025-11_to_12.md
- Raw: Trade_Record/_archive/source_threads_v1/raw/
- Note: day-to-day ops are tracked via STATUS.md and weekly logs.

## Purpose (Σ:UCAR-Trade / GM)
- 週次の相場環境・判断更新点を distilled として時系列ストックし、
  将来UCARが経年データから必要要素を抽出してGM分析の材料にする（トレード効率化）。

## How to Navigate (3-layer map)
- Current location: Trade_Record/STATUS.md
- Weekly index (yearly): Trade_Record/logs/gm/weekly/YYYY/_index.md
- Weekly folder: Trade_Record/logs/gm/weekly/YYYY/<week_id>/
  - note.md: rolling note（facts-first）
  - meta.yaml: tags / regime / levels（machine-readable）
  - review.md: week summary + next plan
  - charts.md + charts/: chart snapshots + level-change reasons
- distilled (monthly): Trade_Record/versions/distilled/YYYY/distilled-gm-YYYY-M.md

## Workflow (weekly loop)
- Week start: note.md に macro/regime をドラフト（Monday AM label を冒頭に）
- Mid-week: meta.yaml に signals / bias を追加（event-driven）
- Week end: review.md に result / next をまとめ、distilled/YYYY.md に判断変更点を抽出
- Monthly: distilled/YYYY-MM.md を集約（検索用）

## Weekly Conventions
- Regime: risk-on / risk-off / cautious / etc.（+sub notes）
- Key gates: Add/Reduce risk conditions
- Links: intra-folder relative

## 2026 Weekly Index
### 2026-1-3_wk52（2025-12-29 → 2026-01-03）
- Regime: risk-on (cautious) / thin liquidity
- 1行：年末年始の薄商いで“上げるが踏み切らない”モード。次週イベント待ち。
- Key gates:
  - Add risk: US100 daily close > 25,670 and 21MA holds（押し目のみ／追わない）
  - Reduce risk: US100 daily close < 23,692 OR USDJPY < 154.7
- Links:
  - [note](./2026-1-3_wk52/note.md)
  - [meta](./2026-1-3_wk52/meta.yaml)
  - [review](./2026-1-3_wk52/review.md)
  - [charts](./2026-1-3_wk52/charts/charts.md)

### 2026-1-10_wk01（2026-01-05 → 2026-01-10）
- Regime: risk-on_cautious（rotation accelerating / low vol）
- 1行：回転加速＋低ボラで株が崩れにくいが、金利粘りで追撃を控えめに。
- Key gates:
  - Add risk: 押し目のみ
  - Reduce risk: VIX上抜け or 金利再上昇
- Links:
  - [note](./2026-1-10_wk01/note.md)
  - [meta](./2026-1-10_wk01/meta.yaml)
  - [review](./2026-1-10_wk01/review.md)
  - [charts](./2026-1-10_wk01/charts/charts.md)

### 2026-1-17_wk02（2026-01-13 → 2026-01-17）
- Regime: risk-on_cautious（rotation + low vol, but yields sticky & gold bid）
- 1行：金利が落ちにくい＋金が崩れにくい＝“ヘッジと追撃”の難易度が上がる週。
- Key signals: yields_sticky / gold_bid / breadth_weakening / jan_flow_support / earnings_risk_Feb
- Links:
  - [note](./2026-1-17_wk02/note.md)
  - [meta](./2026-1-17_wk02/meta.yaml)
  - [review](./2026-1-17_wk02/review.md)
  - [charts](./2026-1-17_wk02/charts/charts.md)

### 2026-1-24_wk03（2026-01-19 → 2026-01-24）
- Regime: risk-on_cautious（risk-on継続だがJPYショック＋Goldブレイクでヘッジ需要が可視化）
- 1行：薄い板×イベント週。終値ゲートと分割以外はやらない週（追撃禁止）。
- Key gates:
  - Add risk: US100 > 25,670 を終値で確認 → 押しで21MAが支える
  - Reduce risk: US100 D1 close < 23,692 または USDJPY < 154.7
- Links:
  - [note](./2026-1-24_wk03/note.md)
  - [meta](./2026-1-24_wk03/meta.yaml)
  - [review](./2026-1-24_wk03/review.md)
  - [charts](./2026-1-24_wk03/charts/charts.md)

### 2026-2-6_wk01（2026-02-02 → 2026-02-06）
- Regime: US risk_off（tech-led） / JP risk_on（election） / USDJPY_breakout / intervention_tailrisk / oil_bid
- 1行：DC過剰投資懸念でMSFT等が崩れ、米株は損切り連鎖。日本は選挙期待で強いが、米株失速と円安の“介入リスク”が次の揺れ。
- Key gates:
  - Add risk: US100 25,011（=直近終値）を維持しつつ 21MAを回復、かつ VIX < 20（押し目のみ／追撃禁止）
  - Reduce risk: US100 daily close < 23,913（下げ加速：22,223〜21,264視野）／JP225 < 51,141／USDJPY < 154.747（調整） or 159.348上抜け後の急反落（介入）／US10Y > 4.30 or US2Y > 3.67（テック逆風）
- Links:
  - [note](./2026-2-6_wk01/note.md)
  - [meta](./2026-2-6_wk01/meta.yaml)
  - [review](./2026-2-6_wk01/review.md)
  - [charts](./2026-2-6_wk01/charts/charts.md)

### 2026-2-13_wk02（2026-02-09 → 2026-02-13）
- Regime: US risk_off_cautious（tech稲穂 + employment_upside → rate_cut_delay） / JP risk_on_overheat（election_afterglow） / USDJPY_sticky_high / geopolitics_watch (Iran) / VIX_rise
- 1行：雇用上方修正＋MSFT好決算なのにSaaS売られ米国株リスクオフ兆候、日本株オン継続だが連動下落警戒。トランプFRBタカ派指名＋イラン悪化でボラ増。
- Key gates:
  - Add risk: US100 24,000維持しつつ25,000回復＆VIX<18（押し目限定／追撃禁止）
  - Reduce risk: US100 daily close < 24,000（損切り連鎖加速：23,000視野）／JP225 < 55,000／USDJPY < 155.0（介入/巻き戻し） or 160.0上抜け後急落／US10Y > 4.30 or VIX>22定着
- Links:
  - [note](./2026-2-13_wk02/note.md)
  - [meta](./2026-2-13_wk02/meta.yaml)
  - [review](./2026-2-13_wk02/review.md)
  - [charts](./2026-2-13_wk02/charts/charts.md)

## Distilled Logs (monthly)
- 2026-01: Trade_Record/versions/distilled/2026/distilled-gm-2026-1.md
- 2026-02: Trade_Record/versions/distilled/2026/distilled-gm-2026-2.md

## 3-scenario response（週の骨格）
A) Risk-on confirmation（上抜け“本物”）
- 条件：US100 > 25,670 を終値で確認 → 押しで21MAが支える
- 行動：追わずに押し待ちで分割追加（AIベータも同様）

B) Whipsaw / itte-koi（狩り→回帰）
- 条件：重要ライン割れがヒゲで終わり、終値で回帰
- 行動：指値のみ。投げない。買い戻し/追加は終値確認後

C) Risk-off re-ignition（失速）
- 条件：US100 D1 close < 23,692 または USDJPY < 154.7
- 行動：追加停止。現金+ゴールド寄りへ。日本ベータから先に軽くする選択を検討

## Monday AM label（行動トリガー禁止）
- 月曜朝は薄商いで“狩り”が混入しやすい。
- A/B/C の寄り推定だけを note.md 冒頭に記録し、行動は終値ゲートで決める。

### 2026-3-7_wk02（2026-03-02 → 2026-03-07）
- Regime: risk_off_acceleration（employment_weak + geopol_explosion + financial_shock / gold_strong_bid / btc_resilient）
- 1行：雇用下方修正でドル円下落/US100サポート死守、イラン本格化でWTI+43.62%/Gold+5.86%ヘッジ爆発、SaaSファンド解約停止で激震警戒。
- Key gates:
  - Add risk: US100 24643維持＋24700回復＆VIX<25（深押し限定／追撃禁止）
  - Reduce risk: US100 daily close <23913 OR VIX>30定着 OR WTI>100 OR Gold<4900
- Links:
  - [note](./logs/gm/weekly/2026/2026-3-7_wk01/note.md)
  - [meta](./logs/gm/weekly/2026/2026-3-7_wk01/meta.yaml)
  - [review](./logs/gm/weekly/2026/2026-3-7_wk01/review.md)
  - [charts](./logs/gm/weekly/2026/2026-3-7_wk01/charts/charts.md)
