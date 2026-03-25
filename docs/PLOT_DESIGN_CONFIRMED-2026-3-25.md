# REX Plot Generation Logic — 設計確定一覧
# 作成: Rex / 承認: Minato / 作成日: 2026-03-20 / 最終更新: 2026-03-25
# 保存先: REX_Trade_System/docs/PLOT_DESIGN_CONFIRMED-2026-3-25.md

---

## 1. プロット生成の目的

| 用途 | 詳細 |
|---|---|
| 第一目的 | Swing High/Low 検出精度の視覚確認 |
| 第二目的 | エントリー・決済の値位置の整合性検証 |
| 第三目的 | ロジック設計の細かな値位置調整 |
| 第四目的 | 1Hウィンドウ内 15M DB/IHS 構造の目視確認（#020追加） |
| 将来用途 | Vision AI によるロジック自動チェック（Phase 3） |

---

## 2. 実装済みプロット関数一覧（2026-03-25時点）

| 関数 | 追加指示書 | 状態 | 出力先 |
|---|---|---|---|
| save_normalized_plot() | 初期 | ✅ 完了 | data/charts/ |
| save_swing_debug_plot() | 初期 | ✅ 完了 | logs/plots/ |
| plot_base_scan() | #015 | ✅ 完了 | logs/base_scan/ |
| plot_swing_check() | #009 | ✅ 完了 | logs/plots/ |
| plot_4h_1h_structure() | #019 | ✅ 完了 | logs/structure_plots/ |
| plot_1h_window_5m() | #020 | ✅ 完了（#020-fix適用済み） | logs/1h_windows/ |
| save_entry_debug_plot() | 初期 | ✅ 完了 | logs/plots/ |

---

## 3. plot_1h_window_5m() 仕様（#020・修正版確定）

### 目的
1H 押し目ウィンドウ（前20本+SL足+後5本=26本≈26時間）内の
5M OHLC + 5M SH/SL マーカー + 参照線を可視化する。

### 表示要素

| 要素 | 色 | 太さ | スタイル | 描画方法 |
|---|---|---|---|---|
| 5M ローソク足（陽線） | 緑 (#26a69a) | - | mplfinance candle | mpf.plot() |
| 5M ローソク足（陰線） | 赤 (#ef5350) | - | mplfinance candle | mpf.plot() |
| 5M Swing High マーカー | サーモン (#FA8072) | size=60 | ▼ scatter | **ax.scatter()** |
| 5M Swing Low マーカー | 水色 (#87CEEB) | size=60 | ▲ scatter | **ax.scatter()** |
| 4H SL 水平線 | 青 (#1E90FF) | 1.5px | 破線 | ax.axhline() |
| 1H SL 垂直線 | 黄緑 (#ADFF2F) | 1.0px | 点線 | ax.axvline() |

### mplfinance 実装パターン（#020-fix で確定）

```python
# 正しいパターン: returnfig=True → axes[0] を使用
fig, axes = mpf.plot(
    df_5m_win,
    type='candle', style=s,
    returnfig=True,       # ← 必須
    figsize=(16, 7),
)
ax = axes[0]

# ⛔ addplot は使わない（axes[1]白帯バグの原因）
# ✅ 代わりに ax.scatter() で整数x軸に直接描画
```

### #020-fix で修正したバグ

| Bug | 症状 | 原因 | 修正 |
|---|---|---|---|
| 白帯バグ | ローソク足が見えない | mpf.make_addplot() が axes[1] を生成し22%占有 | addplot廃止 → ax.scatter() |
| CJK豆腐 | タイトルの日本語が□ | DejaVu Sans にCJK文字なし | 英語タイトルに変更 |
| axvline型問題 | 垂直線が表示されない場合 | mplfinance内部の整数x軸 | try/except フォールバック |

### 保存仕様

```
保存先: logs/1h_windows/YYYYMMDD_HHMM_{LONG|SHORT}_1h_window.png
解像度: 150 dpi
最大枚数: 20枚（__main__ ブロック内の MAX_PLOTS で制御）
```

---

## 4. plot_4h_1h_structure() 仕様（#019確定）

### 目的
4H+1H のマルチTF構造を5Mローソク上にオーバーレイし、
トレンド方向の整合性を視覚的に確認する。

### 表示要素

| 要素 | 色 | 太さ | スタイル |
|---|---|---|---|
| 5M ローソク足（陽線） | 緑 (#26a69a) | - | mplfinance 標準 |
| 5M ローソク足（陰線） | 赤 (#ef5350) | - | mplfinance 標準 |
| 4H Swing High / Neck | 橙 (#FF8C00) | 2.0px | 実線 + 水平帯 |
| 4H Swing Low | 青 (#1E90FF) | 2.0px | 実線 |
| 1H Swing High | サーモン (#FA8072) | 1.5px | 折れ線 |
| 1H Swing Low | 水色 (#87CEEB) | 1.5px | 折れ線 |

### 表示期間

```
左側: ネック越えイベントから 10日分
右側: ネック越えイベントから 2日分
合計: 約12日分の 5M 足
```

### 保存仕様

```
保存先: logs/structure_plots/YYYYMMDD_HHMM_{LONG|SHORT}_4H1H_structure.png
解像度: 150 dpi
パラメータ: N_4H=5, N_1H=3, LOOKBACK_4H=100, LOOKBACK_1H=240
```

### 検証結果

```
初回（2026-03-22）: 16件生成 → 9枚目視で90%合格
追加（2026-03-25）: 7枚追加目視 → 100%合格
累計合格率: 16/17（94%）
```

---

## 5. plot_swing_check() 仕様（#009 Phase 1 確定）

### 目的
5M OHLC + 4H/15M Swing High/Low + NONE区間の視覚化。
Swing 検出精度の基礎確認に使用。

### 表示要素

| 要素 | 色 | 太さ | スタイル |
|---|---|---|---|
| 5M ローソク足 | 緑/赤 | - | mplfinance 標準 |
| 4H Swing High | 橙 (#FF8C00) | 2.0px | 実線 |
| 4H Swing Low | 青 (#1E90FF) | 2.0px | 実線 |
| 15M Swing High | サーモン (#FA8072) | 1.5px | 実線 |
| 15M Swing Low | 水色 (#87CEEB) | 1.5px | 実線 |
| NONE 区間 | グレー | - | 背景塗り alpha=0.15 |

---

## 6. エントリー詳細プロット仕様（Phase 2 — 将来実装）

### トリガー条件

```
① 4H 上昇ダウ確認
② Fib 61.8% 圏内
③ 15M 前回押し目安値を割っていない
④ 15M ダブルボトム形成確認
⑤ 5M DB ネックライン上抜け実体確定
  → ⑤ の瞬間にプロット生成・保存
```

### 追加表示要素

| 要素 | 色 | 太さ | スタイル |
|---|---|---|---|
| Fib 61.8% | 紫 (#9B59B6) | 1.0px | 破線 |
| Fib 50% | 紫 (#9B59B6) | 1.0px | 点線 |
| 4H ネックライン | 橙 (#FF8C00) | 2.5px | 実線（太め） |
| 15M DB ネックライン | 黄緑 (#ADFF2F) | 1.2px | 破線 |
| エントリー ▲ | 緑 (#00FF00) | - | マーカー |
| 決済 × | 赤 (#FF0000) | - | マーカー |
| 4H Swing 水平帯 | 橙 (#FF8C00) | - | 背景塗り alpha=0.08 |

### サブパネル

```
エントリー条件の合否 ○×（5条件）
Fib 値（実数）/ 損益（pips）/ 最大含み損（pips）
Swing 検出パラメータ（n / lookback）
```

---

## 7. 共通仕様

### 依存ライブラリ

```python
mplfinance          # OHLC ローソク足の描画
matplotlib          # パネル構成・水平線・マーカー描画
pandas              # OHLC データ操作
numpy               # Fib 計算
```

### mplfinance 使用ルール（#020-fix で確定）

```
1. returnfig=True パターンのみ使う
   → plt.subplots() + mpf.plot(ax=ax) パターンは禁止
2. make_addplot() に ax= 引数を渡さない
   → TypeError の原因になる
3. addplot の代わりに ax.scatter() で描画する
   → addplot は axes[1] を生成してレイアウトを崩すバグがある
4. axvline は try/except でフォールバック
   → mplfinance の returnfig モードでは x軸が整数になる場合がある
5. タイトルに日本語を使わない
   → DejaVu Sans に CJK 文字がないため豆腐になる
```

### 共通ファイル保存仕様

```
解像度: 150〜200 dpi
背景色: #131722（ダークテーマ）
保存: plt.savefig(fname, dpi=N, bbox_inches='tight', facecolor=fig.get_facecolor())
```

---

## 8. Phase 3（将来）— Vision AI 自動チェック

```
目的: 生成 PNG を Vision AI に送信して Swing 構造の整合性を自動確認

実装内容:
  ・PNG → base64 変換 → Gemini Vision / GPT-4o API 送信
  ・異常ケースのみ抽出してレポート出力
  ・実装コスト: 約 30 行

前提条件:
  Phase 2 でチャート品質が十分に高まってから着手
```
