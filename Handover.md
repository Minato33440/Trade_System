# REX Trade System - セッション引き継ぎドキュメント

**作成日**: 2026-03-13  
**プロジェクト**: REX_Trade_System  
**ディレクトリ**: `c:\Python\UCAR_Dialy\Trade_Record\REX_Trade_System`

---

## 📋 プロジェクト概要

USDJPYのマルチタイムフレーム（MTF）トレード戦略のバックテストシステム。  
Polygon無料版APIで直近2年分の5分足/15分足/1時間足/4時間足/日足データを取得し、  
ミナト流MTF短期ルールv2でバックテストを実行。

---

## ✅ 完了した作業

### 1. **データ取得システム（`src/data_fetch.py`）**
- ✅ Polygon無料版APIから2年分のマルチタイムフレームデータ取得
- ✅ yfinanceフォールバック機能
- ✅ 列名を`signals.py`互換に統一（`5M_`, `15M_`, `1H_`, `4H_`, `D_`プレフィックス）
- ✅ 4H足フォールバック（1H足からresample）
- ✅ レート制限対策（5 req/min → 12秒間隔）
- ✅ NaN対策（各時間枠を分離してffill）

**取得済みデータ**:
- ファイル: `data/raw/usdjpy_multi_tf_2years.parquet`
- 期間: 2024-03-13 ~ 2026-03-12（約2年）
- 形状: 83,112行 × 25列
- 時間枠: 5M (82,608本), 15M (27,655本), 1H (6,943本), 4H (1,795本), D (631本)

### 2. **シグナル生成ロジック（`src/signals.py`）**
- ✅ `mtf_minato_short_v2()` 関数実装
- ✅ 4H優位性（2番底+ネックライン越え）
- ✅ 日足トレンド一致（EMA20/50 GC or ADX>25）
- ✅ フィボナッチ50%以内押し目
- ✅ 1H/15M/5Mネックライン確認
- ✅ 先行エントリー検知（ストップ狩り逆利用）
- ✅ セッション時間帯フィルタ（tokyo, london, ny, all）

### 3. **バックテストシステム（`src/backtest.py`）**
- ✅ `run_usdjpy_mtf_v2()` - 基本バックテスト関数
- ✅ `run_usdjpy_mtf_v2_advanced()` - Advanced版（テンプレート準拠）
  - NaN対策（各TF分離+ffill）
  - JST変換（UTC → Asia/Tokyo）
  - セッション別集計
  - VectorBT対応
  - MaxDD 10%超で警告
  - Markdownテーブル出力
  - パス自動解決（親ディレクトリから実行可能）

---

## 📊 現在の状態

### **シグナル数（2年間）**
- TOKYO: 10件
- LONDON: 0件
- NY: 1件
- ALL: 15件

### **制限事項**
⚠️ **VectorBT未インストール**のため以下が計算不可:
- 平均利確/損切Pips
- 2年損益合計
- 期待値
- Profit Factor
- 最大DD
- 勝率

---

## 🗂️ ファイル構成

```
REX_Trade_System/
├── .env                          # APIキー（XAI, Polygon）
├── data/
│   └── raw/
│       └── usdjpy_multi_tf_2years.parquet  # 2年分MTFデータ
├── src/
│   ├── data_fetch.py             # Polygon/yfinanceデータ取得
│   ├── signals.py                # MTFシグナル生成
│   ├── backtest.py               # バックテスト実行
│   ├── utils.py                  # ユーティリティ
│   └── plotter.py                # プロット機能
├── configs/
│   ├── rex_chat.py               # Rex AI対話システム
│   └── node.mjs                  # xAI APIラッパー
├── docs/
│   ├── Minato_rule.md            # ミナト流ルール説明
│   └── Backtest_template_v2.md   # バックテストテンプレート
└── HANDOFF.md                    # このファイル
```

---

## 🚀 次にやるべきこと（優先順）

### **1. VectorBTインストール（最優先）**
```powershell
cd c:\Python\UCAR_Dialy\Trade_Record\REX_Trade_System
.venv\Scripts\activate
pip install vectorbt
pip install tabulate  # Markdownテーブル出力用（オプション）
```

### **2. バックテスト実行**
```powershell
python src/backtest.py
```

これで実際の損益・期待値・PF・MaxDDが計算されます。

### **3. signals.py 改善（推奨）**

#### **A. use_daily 引数を追加**
```python
def mtf_minato_short_v2(
    df_multi: pd.DataFrame,
    session: str = "all",
    use_daily: bool = True,  # ← 追加
) -> pd.Series:
    # use_daily=False の場合は日足トレンド条件をスキップ
    if use_daily:
        cond_trend = golden_cross | (adx_val > 25)
    else:
        cond_trend = pd.Series(True, index=df_multi.index)
```

**目的**: 4H優位性のみ vs 日足ルール追加の比較テスト

#### **B. exit_pips 計算を追加**
実際の利確/損切Pipsを計算して返す機能を追加。

#### **C. ロング/ショート別エントリー**
現在はショートのみ。ロングシグナルも生成できるように拡張。

---

## 💻 実行方法

### **基本実行**
```powershell
cd c:\Python\UCAR_Dialy\Trade_Record\REX_Trade_System
python src/backtest.py
```

### **データ再取得（必要時のみ）**
```powershell
python src/data_fetch.py
# 約6〜8分かかります（Polygonレート制限対策）
```

### **Rex AI対話**
```powershell
python configs/rex_chat.py
# または
python configs/rex_chat.py --trade  # 8ペア30日データ+プロット
```

---

## 📌 重要な注意点

### **1. Polygon API制限**
- **無料版**: 5 req/min
- **15分足**: 最大2年まで遡れる
- **取得間隔**: 12秒（レート制限対策）

### **2. データのNaN構造**
- 5分足がベースなので、粗い時間枠ほどNaNが多い
- **対策**: `backtest.py`で各TFを分離してffill済み

### **3. タイムゾーン**
- Polygon: UTC
- セッション判定: JST（Asia/Tokyo）
- **自動変換**: `backtest.py`内で実装済み

### **4. セッション時間帯（JST）**
- TOKYO: 9:00-11:00
- LONDON: 17:00-19:00
- NY: 22:30-翌1:00

---

## 🔧 トラブルシューティング

### **エラー: ファイルが見つからない**
```
FileNotFoundError: 'data/raw/usdjpy_multi_tf_2years.parquet'
```
**解決**: REX_Trade_Systemディレクトリで実行してください
```powershell
cd c:\Python\UCAR_Dialy\Trade_Record\REX_Trade_System
python src/backtest.py
```

### **VectorBT未インストール**
```
[WARNING] vectorbt未インストール
```
**解決**:
```powershell
pip install vectorbt
```

### **Markdownテーブル出力エラー**
```
ImportError: Missing optional dependency 'tabulate'
```
**解決** (オプション):
```powershell
pip install tabulate
```

---

## 📈 期待される出力（VectorBT インストール後）

```
======================================================================
  バックテスト結果サマリ
======================================================================

セッション  総トレード数  期待値(pips)  Profit Factor  最大DD(%)  勝率(%)
TOKYO       10           +X.XX          X.XX           X.XX      XX.XX
LONDON      0            0.00           0.00           0.00      0.00
NY          1            +X.XX          X.XX           X.XX      XX.XX
ALL         15           +X.XX          X.XX           X.XX      XX.XX

総合評価:
  期待値: +X.XX pips
  -> [OK/NG] 期待値+5pips以上！裁量で狙う価値あり
  
  Profit Factor: X.XX
  -> [OK/NG] PF 1.5以上！長期的にプラス期待
  
  最大DD: X.XX%
  -> [OK/警告] MaxDD 10%以内。リスク管理良好
```

---

## 📚 参考ドキュメント

- `docs/Minato_rule.md` - ミナト流MTFルール詳細
- `docs/Backtest_template_v2.md` - バックテスト要件定義
- `.env` - APIキー設定（XAI_API_KEY, Polygon_API_KEY）

---

## 🎯 最終目標

1. **期待値 +5pips以上**: 裁量で狙う価値あり
2. **Profit Factor 1.5以上**: 長期的にプラス
3. **MaxDD 10%以内**: リスク管理良好
4. ロング/ショート別の勝率・損益内訳を把握

---

## 💬 次のセッションで確認すること

1. VectorBTインストール後のバックテスト結果
2. 期待値・PF・MaxDDの実数値
3. TOKYO/LONDON/NY/ALL各セッションの比較
4. use_daily ON/OFF比較の必要性

---

**ボス、VectorBTをインストールしてバックテスト再実行したら、結果を教えてね！**  
**期待値・PF・MaxDDの数値次第で、次の改善方針が決まるよ！**
