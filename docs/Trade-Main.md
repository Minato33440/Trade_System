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
- 2026-03: Trade_Record/versions/distilled/2026/distilled-gm-2026-3.md
- 2026-04: Trade_Record/versions/distilled/2026/distilled-gm-2026-4.md

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

### 2026-3-20_wk04（2026-03-16 → 2026-03-20）
- Regime: Geopolitical Risk-Off + Energy Shock（FOMC_hold_hawkish + US_China_postponed + IEA_oil_6months + WTI_extreme_volatile + USDJPY_v_recovery + JP225_below_fib236）
- 1行：FOMC据え置き＋タカ派・米中延期・イスラエル湾岸爆撃でリスクオフ再加速。US100月足Fibo23.6ネック割り込みFibo38.2（22,200$）視野。WTI極端乱高下（119.50→76→100）、XAU4,500$急落。USDJPY V字（159.90→157.50→157.92）。完全凍結・弾薬最大温存。
- Key gates:
  - Add risk: 米中首脳会談再設定確認後 US100 22,200$維持かつ反発確認（追撃禁止）
  - Reduce risk: US100 daily close <22,200 OR VIX>30定着 OR WTI再高騰（ホルムズ再封鎖）
- Links:
  - [note](./logs/gm/weekly/2026/2026-3-20_wk04/note.md)
  - [meta](./logs/gm/weekly/2026/2026-3-20_wk04/meta.yaml)
  - [review](./logs/gm/weekly/2026/2026-3-20_wk04/review.md)
  - [charts](./logs/gm/weekly/2026/2026-3-20_wk04/charts.md)

### 2026-3-27_wk05（2026-03-23 → 2026-03-27）
- Regime: Geopolitical Risk-Off + Energy Shock（VIX_30_breach + US100_fib382_approaching + USDJPY_toward_161 + WTI_near_100 + stagflation_week_ahead + iran_4_6_deadline）
- 1行：VIX 31.05でwk04 Reduce gate発動水準到達。US100 23,132でFib38.2（22,222）まで約900pt。USDJPY 159.7で161円射程。4/6イラン期限・4/3雇用統計が最大の節目。2シナリオ（一段安→急反発 / 金融危機連鎖）踏まえ完全凍結継続。
- Key gates:
  - Add risk: US100 22,000〜22,222底打ち確認＋VIX鎮静（<27）＋イラン緊張緩和（追撃禁止）
  - Reduce risk: US100 daily close <22,000 OR VIX>35定着 OR WTI急騰（120$）OR イラン本格軍事衝突
- Links:
  - [note](./logs/gm/weekly/2026/2026-3-27_wk05/note.md)
  - [meta](./logs/gm/weekly/2026/2026-3-27_wk05/meta.yaml)
  - [review](./logs/gm/weekly/2026/2026-3-27_wk05/review.md)
  - [charts](./logs/gm/weekly/2026/2026-3-27_wk05/charts.md)


## Weekly Brief | 2026-4-3_wk01（2026-03-30 → 2026-04-03）
created: 2026-04-05 (JST)

### Macro / Regime
- Regime（system）: Equities Down / Oil Surge（equities=down / volatility=normal / oil=surge / gold=off / crypto=range / yields=rising）
- **VIX 23.87** でwk05（31.05）から低下。ただし地政学エスカレーション最高水準で週明け再上昇警戒。
- **US100 24,045$** → 23,900$週足ネックを若干上回って終了。48h期限後の確認が最重要。
- **WTI 112$（土曜）** → 金曜103.5比+8.5$。トランプ48h最後通牒＋JASSM-ER全在庫中東投入で急騰。
- **XAUUSD 4,702$** → 安全資産買い本格化。wk05比+178$。
- **US10Y 4.313 / US2Y 3.948** → 債券フライト。US2Y 4%割れ。
- **トランプ48h最後通牒（4/4）**: 軍事行動の直前シグナル。イランは反発。4/6-7が最大分岐点。
- **NATO脱退検討**: 欧米同盟への波及リスク。

### Position / Orders
- Core：Gold（4,702$・安全資産移行確認）/ エネルギー（WTI保有継続）/ 防衛継続保有。
- Mode：完全凍結継続。4/6-7 48h期限通過まで絶対NO-GO。
- 弾薬温存：期限通過後の停戦合意確認 + US100維持 + VIX<20全条件確認後のみ初動。

### Key Levels (close-based)
- US100: 24,045 / R=24,643 / S=23,900（週足ネック）/ 22,222（Fib38.2）/ 22,000
- JP225: TBD / S=36,000〜35,000（サポート帯）
- USDJPY: 159.632 / R=160.0（レートチェック）/ 161.0（NOBUターゲット）
- WTI: 112.060（土曜）/ 103.5（金曜）/ R=120.0（介入水準）/ S=100.0
- XAUUSD: 4,702.7 / S=4,574（wk05終値）/ 4,100
- VIX: 23.87 / US10Y: 4.313 / US2Y: 3.948

### Gates（最重要：終値で判定）
- Add risk ONLY if: 4/6-7 48h期限通過後に停戦合意確認 + US100 24,045$週足維持 + VIX<20（追撃禁止）
- Reduce / pause if: US100 D1 close <23,400 OR VIX>30再到達 OR WTI>120$ OR JASSM-ER実際に使用
- Hedge gate: Gold 4,702$維持 / エネルギー / 防衛継続

### This Week Focus（行動: 4/6-4/10）
- 完全凍結継続。4/6-7 トランプ48h最後通牒期限通過まで絶対NO-GO。
- 4/6-7（月-火）: 48h期限の停戦合意 or 軍事拡大の確認。最大の地政学分岐点。
- 4/10（木）米国CPI: WTI急騰背景の物価指標。スタグフレーション確認度に注目。
- US100 24,045$の偽ブレイク or 本物上抜けの週足確認。

### Signals (weekly, fixed keys)
- us10y_accel: easing（4.313。債券フライトで低下中）
- hy_oas_widening: alert（地政学エスカレーション最高水準）
- vix_spike: easing（23.87。低下も週明け再上昇警戒）
- wti_shock: on（112$土曜 / 金曜103.5$ / エスカレーション・プレミアム）
- eps_revision_chain: watch（4/10 CPI・WTI急騰背景のインフレ確認）

## Previous (archived briefs)
- Weekly Brief | 2026-3-27_wk05（2026-03-23 → 2026-03-27）
  - see: logs/gm/weekly/2026/2026-3-27_wk05/

## Weekly Brief | 2026-3-27_wk05（2026-03-23 → 2026-03-27）
created: 2026-03-29 (JST)

### Macro / Regime
- Regime: Geopolitical Risk-Off + Energy Shock（第5週継続）
- VIX 31.05でwk04設定のReduce risk gate（VIX>30定着）が発動水準に到達。
- US100 23,132.77 → Fib38.2（22,222）まで約900pt。NOBUターゲット22,000が視野。
- USDJPY 159.704で円安継続。NOBUターゲット161円が射程。
- WTI 99.64で100$近辺高止まり。エネルギーショック構造継続。
- XAUUSD 4,524.3で短期調整継続。4,500サポート注視。
- イラン/ガザ: 戦闘停止に向けた動き。4/6前後に米・イラン攻撃延期期限（最大節目）。

### Position / Orders
- Core：Gold / エネルギー（WTI 100$近辺）/ 防衛（ゴールデンドーム関連）継続保有。
- Mode：完全凍結継続。VIX>30到達・4/6イラン期限まではNO-GO。
- 弾薬温存：US100 22,000〜22,222底打ち確認待ち。
- 長期ポートフォリオ：売り不要。安値での積立加速を検討。

### Key Levels (close-based)
- US100: 23,132.77 / S=22,222（Fib38.2）/ 次=21,264 / テールリスク=20,000
- JP225: S=36,000〜35,000 / 3/30権利落ち注意
- USDJPY: 159.704 / R=161.0（NOBUターゲット）/ S=149〜150（急落シナリオ）
- WTI: 99.640 / R=106（NOBUターゲット）/ S=68〜70
- XAUUSD: 4,524.3 / S=4,500 / VIX: 31.050 / US10Y: 4.440

### Gates（最重要：終値で判定）
- Add risk ONLY if: US100 22,000〜22,222底打ち確認＋VIX<27＋イラン緊張緩和（追撃禁止）
- Reduce / pause if: US100 D1 close <22,000 OR VIX>35定着 OR WTI急騰（120$）OR イラン本格衝突
- Hedge gate: Gold 4,500サポート / エネルギー / 防衛継続

### This Week Focus（行動: 3/30-4/4）
- 完全凍結継続。4/6イラン期限通過まではNO-GO徹底。
- 4/3（金）雇用統計 + ISMサービス業PMI：スタグフレーション確認の最重要指標。
- 3/30（月）権利落ち：ギャップダウン想定。成行で動かない。
- US100 22,000〜22,222接近時の底打ちサイン（TACO仮説）を日足終値で確認。

### Signals (weekly, fixed keys)
- us10y_accel: on（4.440%）
- hy_oas_widening: alert（プライベートクレジット デフォルト懸念）
- vix_spike: on（31.05 / 30超え確定）
- wti_shock: on（99.64 / 100$高止まり）
- eps_revision_chain: watch（4/3雇用統計待ち）

## Previous (archived briefs)
- Weekly Brief | 2026-3-20_wk04（2026-03-16 → 2026-03-20）
  - see: logs/gm/weekly/2026/2026-3-20_wk04/


## Weekly Brief | 2026-3-20_wk04（2026-03-16 → 2026-03-20）
created: 2026-03-21 (JST)

### Macro / Regime
- Regime: Geopolitical Risk-Off + Energy Shock
- FOMC（3/19）政策金利据え置き＋タカ派発言。イラク侵攻インフレ加速懸念継続。米中首脳会談延期でリスクオフ再加速。
- IEA声明：湾岸諸国エネルギー輸出の復旧に半年見通し→原油高長期化シナリオ（180$予測アナリストも）。
- イスラエルによる湾岸諸国空爆・エネルギー施設破壊継続。米軍中東に海兵隊数千人追加派遣。
- WTI極端乱高下（119.50→76→100）。XAU週足Fibo23.6→日足押し安値4,500$まで急落。
- US100 月足Fibo23.6の週足ネックライン割り込み終値→Fibo38.2（22,200$）視野。
- JP225 週足ワントップから急落、Fibo23.6実体割り込み終値（日米首脳会談・防衛セクターで相対堅調）。
- USDJPY：159.90（週高値）→157.50（日銀牽制急落）→157.924（金曜終値）V字。VIX 26.78高止まり。

### Position / Orders
- Core：Gold / エネルギー（WTI 100$回復確認）/ 防衛（日米共同開発・ゴールデンドーム関連）継続保有。
- Mode：完全凍結継続。米中首脳会談再設定確認まではNO-GO。
- 弾薬温存：US100 Fibo38.2（22,200$）/ JP225 深押し待機継続。
- USDJPY：V字回復確認済み。介入急落（～3円）は一過性対処方針継続。

### Key Levels (close-based)
- US100: 23,898.154（週終値）/ S=22,200（Fibo38.2）/ 次=21,264
- JP225: Fibo23.6実体割り込み終値 / S=54,814
- USDJPY: 157.924（金曜NY終値）/ 週高159.90 / 週安157.50
- WTI: 98.230 / S=95.0 / R=100.0（施設復旧半年で高止まり）
- XAUUSD: 4,574.9（日足押し安値4,500$付近）
- US2Y: 4.012 / US10Y: 4.391 / VIX: 26.780

### Gates（最重要：終値で判定）
- Add risk ONLY if: 米中再設定確認後 US100 22,200$維持かつ反発（追撃禁止）
- Reduce / pause if: US100 D1 close <22,200 OR VIX>30定着 OR WTI再急騰
- Hedge gate: Gold 4,500$押し目・エネルギー・防衛継続

### This Week Focus（行動: 3/23-27）
- 完全凍結継続。米中首脳会談再設定の有無を最重視。
- WTI 100$定着 or 調整を確認（エネルギー保有判断）。
- 日銀4月タカ派発言内容に注意（円高加速リスク）。
- VIX 26.78の30超え定着 or 鎮静を日足終値で確認。

### Signals (weekly, fixed keys)
- us10y_accel: on（FOMC据え置き・タカ派でUS10Y 4.391%）
- hy_oas_widening: alert（プライベートクレジット リスクオフ型新商品波及）
- vix_spike: on（26.78 高止まり）
- wti_shock: on（極端乱高下・100$回復・施設復旧半年）
- eps_revision_chain: watch（米中延期の影響・日銀4月タカ派）

## Previous (archived briefs)
- Weekly Brief | 2026-3-13_wk03（2026-03-09 → 2026-03-13）
  - see: logs/gm/weekly/2026/2026-3-13_wk03/
