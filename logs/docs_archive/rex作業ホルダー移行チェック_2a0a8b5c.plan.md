---
name: REX作業ホルダー移行チェック
overview: 作業ディレクトリ移行後に、REX_Trade_System の構成・仮想環境・依存・.env・起動・出力先・Git変更を一通り検証して、相対パス事故と環境取り違えを潰します。
todos:
  - id: inspect-system-structure
    content: rex_chat.py / data_fetch.py / docs から前提を整理し、移行後チェック項目に落とし込む
    status: completed
  - id: verify-venv-python-binding
    content: cwd・python実体・.venv存在・上位.venv不在をコマンドで検証する手順を用意
    status: completed
  - id: verify-deps-and-env
    content: 依存importと.env必須/任意キーの存在確認手順を用意（値は非表示）
    status: completed
  - id: verify-minimal-run-and-outputs
    content: "--help/--trade/--news の最小起動と出力ファイル生成確認手順を用意"
    status: completed
  - id: verify-git-cleanliness
    content: git statusで意図した変更のみ残っているか確認する手順を用意
    status: completed
isProject: false
---

## 目的

- `C:\Python\UCAR_Dialy\Trade_Record\REX_Trade_System` を基準に、Python実体が `.venv` を掴んでいること、依存/環境変数/最小起動/出力先が期待どおりであることを確認する。
- 併せて、現在のコード前提（`.env` 読み込み場所、必須/任意ENV、ログ出力先、Gitに残る変更）を把握して、移行後の事故ポイントを潰す。

## 現状把握（コード/ドキュメントから読み取れた前提）

- **エントリ**: `[configs/rex_chat.py](c:/Python/UCAR_Dialy/Trade_Record/REX_Trade_System/configs/rex_chat.py)`
  - `repo_root = Path(__file__).resolve().parents[1]` で `**REX_Trade_System** 直下を基準**にし、`.env` は `load_dotenv(repo_root / ".env")` で読む。
  - `XAI_API_KEY` が **必須**（無いと exit code 2）。`XAI_MODEL` は `os.getenv("XAI_MODEL", "grok-4")` が **デフォルト**。
  - `--trade` は `logs/png_data/multi_pairs_plot_8.png` と `logs/png_data/YYYY_MM_DD_snapshot.yaml` を相対パスで保存。
- **データ取得**: `[src/data_fetch.py](c:/Python/UCAR_Dialy/Trade_Record/REX_Trade_System/src/data_fetch.py)`
  - `yfinance` 優先、空/失敗時に `POLYGON_API_KEY` があれば Polygon フォールバック。
- **依存**: `[requirements.txt](c:/Python/UCAR_Dialy/Trade_Record/REX_Trade_System/requirements.txt)` に `yfinance/pandas/matplotlib/python-dotenv/requests/feedparser/beautifulsoup4` は入っている。
- **Git無視**: `[.gitignore](c:/Python/UCAR_Dialy/Trade_Record/REX_Trade_System/.gitignore)` で `.env` と `logs/png_data/` は ignore（= 出力PNG/YAMLは基本コミットされない運用）。

## 重要な注意（読み取り時点で見つかった差分/リスク）

- **XAI_MODELデフォルトの不一致**: `docs/SYSTEM_OVERVIEW.md` にはデフォルト `grok-4-fast` とある一方、実装は `grok-4`。
- **.venv の存在はリポジトリからは確定できない**: `.venv` は通常Git管理外なので、ローカル実体はコマンドで検証する必要がある。

## 検証手順（Minatoがローカルで実行）

- **作業ホルダー確認**
  - PowerShellで `cd C:\Python\UCAR_Dialy\Trade_Record\REX_Trade_System`
- **Python実体が `.venv` か**
  - `python -c "import sys; print(sys.executable)"`
  - 期待: `...\REX_Trade_System\.venv\Scripts\python.exe`
- **仮想環境フォルダの存在**
  - `Test-Path .\.venv` → `True`
  - `Test-Path ..\.venv`（= `Trade_Record\.venv`）→ `False`
- **主要依存のimport確認（最低限）**
  - `python -c "import yfinance, pandas, matplotlib, dotenv, requests, feedparser, bs4; print('ok')"`
  - 失敗したら: `.venv` に対して `python -m pip install -r requirements.txt`
- **.env の必須/任意キー確認（値は表示しない）**
  - `python -c "import os; from dotenv import load_dotenv; load_dotenv('.env'); print('XAI_API_KEY', bool(os.getenv('XAI_API_KEY'))); print('XAI_MODEL', os.getenv('XAI_MODEL')); print('POLYGON_API_KEY', bool(os.getenv('POLYGON_API_KEY')))"`
- **起動（最小）**
  - `python .\configs\rex_chat.py --help`
  - 必要なら: `python .\configs\rex_chat.py --news` / `python .\configs\rex_chat.py --trade`
- **出力先（--trade）**
  - `Test-Path .\logs\png_data\multi_pairs_plot_8.png`
  - `Get-ChildItem .\logs\png_data\*_snapshot.yaml | Select-Object -First 5`
- **Git状態の確認（意図した変更だけ残す）**
  - リポジトリルート（`C:\Python\UCAR_Dialy`）で `git status`。
  - `node_modules/` や `logs/` など不要物が追跡対象になっていないか、意図しない docs/requirements 変更が混ざってないかを見る。

## 見直し候補（必要なら次の作業として）

- `XAI_MODEL` デフォルトを **ドキュメントか実装どちらかに寄せる**（`grok-4` vs `grok-4-fast`）。
- `.gitignore` が `logs/png_data/` を無視しているので、週次でPNG/YAMLをGitに残したい運用なら例外ルールを設計する（現状ドキュメントにはコピー運用もある）。
