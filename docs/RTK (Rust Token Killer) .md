RTK (Rust Token Killer) 導入
令和8年4月10日


実装方法：

Windows環境での注意点
HomebrewはWindowsで使えないので、以下のいずれかを選択します。

● Step 1: インストール

方法A: インストールスクリプト（Git Bash / WSL使用時）
curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh

方法B: Cargoでインストール（Rustが入っている場合）
cargo install --git https://github.com/rtk-ai/rtk

方法C: バイナリを直接ダウンロード
https://github.com/rtk-ai/rtk/releases からWindows用バイナリ（.exe）を取得し、PATHが通ったディレクトリに配置。

● Step 2: Claude Code用フック設定

rtk init -g
これで以下が自動設定されます：

Bashフックが.bashrc / .zshrcに追記される
RTK.md（Claude Codeへの指示ファイル）が生成される
以降、git statusなどのコマンドが自動的にrtk git statusとして実行される

非インタラクティブで即座に設定したい場合：
rtk init -g --auto-patch

設定確認：
rtk init --show

● Step 3: 動作確認

rtk gain          # トークン削減の統計確認
rtk gain --graph  # 30日間のグラフ表示
重要な制限事項
RTKのフックはBashツール経由のコマンドのみに効きます。Claude CodeのネイティブツールであるRead・Grep・Globはバイパスされるため、それらの出力は圧縮されません。

期待できる削減効果
コマンド	削減率
git status	~80%（2000→400トークン）
テスト出力	~90%
一般的な開発コマンド	60〜90%

Windowsでの具体的な環境（Git Bash / PowerShell / WSLなど）によって手順が変わる可能性があるので、詰まった箇所があれば教えてください。

----------------------------------------------------------------------------
インストール指示：
方法C: cargo install --git https://github.com/rtk-ai/rtk
バイナリを直接ダウンロード
https://github.com/rtk-ai/rtk/releases からWindows用バイナリ（.exe）を取得し、PATHが通ったディレクトリを作ってに配置
自動的にrtk git statusとして実行できるようにClaude Code用フック設定してもらえます？
----------------------------------------------------------------------------

実装結果：

● 設定完了 + RTKインストール手順

フック設定内容
~/.claude/settings.json に PreToolUse フックを追加しました。
Bashツールが実行されるたびに：
	1. RTKが存在するかチェック
	2. 対象コマンド（git, ls, grep, find, diff, pytest, cargo, npm, docker, kubectl, aws）なら自動的に rtk <コマンド> に書き換え
	3. RTKがなければ無害にスルー

-------------------------------------------------------------------------------

● 次のステップ：RTKバイナリのインストール
Cargoがないので、バイナリを直接ダウンロードする方法を使います。

1. リリースページからダウンロード
https://github.com/rtk-ai/rtk/releases にアクセスして rtk-x86_64-pc-windows-msvc.exe（または類似名）を取得

2. PATHが通ったディレクトリに配置
C:\Users\Setona\bin\ がすでにPATHに入っているのでここに置くだけ：
# PowerShellで
Move-Item ダウンロード先\rtk*.exe C:\Users\Setona\bin\rtk.exe

3. 動作確認
rtk --version
結果：(.venv) PS C:\Python\REX_AI\Setona_HP> C:\Users\Setona\bin\rtk --version                                                    
rtk 0.35.0

rtk git status   # 出力がコンパクトになればOK
結果：(.venv) PS C:\Python\REX_AI\Setona_HP> C:\Users\Setona\bin\rtk git status    
[rtk] /!\ No hook installed — run `rtk init -g` for automatic token savings
* main...origin/main
clean — nothing to commit

4. Claude Codeを再起動（フック読み込みのため）
またはVSCode内で /hooks を一度開く

注意: jq コマンドも必要です。Git for Windowsに同梱されていることが多いですが、なければ https://jqlang.github.io/jq/download/ から jq-windows-amd64.exe を jq.exe にリネームして同じ C:\Users\Setona\bin\ に配置してください。

---------------------------------------------------------------------------

Claudecode再起動→セットアップ完了

RTKリポジトリを実装してますが、3.まで実行したので4.以降の対応を

4. Claude Codeを再起動（フック読み込みのため）
またはVSCode内で /hooks を一度開く

注意: jq コマンドも必要です。Git for Windowsに同梱されていることが多いですが、なければ https://jqlang.github.io/jq/download/ から jq-windows-amd64.exe を jq.exe にリネームして同じ C:\Users\Setona\bin\ に配置

rtk は bash PATHでも認識されています。セットアップ状況をまとめます：
完了した内容：
	1. rtk バイナリ → C:\Users\Setona\bin\rtk.exe ✅
	2. bash PATH から rtk アクセス可能 ✅
	3. ~/.claude/CLAUDE.md に RTK 使用指示を生成済み ✅
	4. ~/.claude/settings.json に既存フック設定あり ✅
Windowsでの動作モード：
RTKはWindowsでは hook-based（自動プレフィックス）が使えないため、CLAUDE.md モードにフォールバックしました。これはClaude Code（私）が rtk git status のようにコマンドを手動でプレフィックスする方式です。
次のステップ：
settings.json の既存フックとCLAUDE.mdの指示が重複している可能性があります。settings.jsonのフックは command -v rtk で存在確認しているので機能はしますが、RTKが期待するフォーマットと異なります。現状のまま使うか、RTKのCLAUDE.mdモードに統一するか選べます。
動作確認として試してみましょう：

RTKが正常に動作しています。セットアップ完了です。
動作確認結果：
	• rtk git status → コンパクト出力 ✅
	• rtk git log → 圧縮ログ ✅
現在の構成：
	• ~/.claude/CLAUDE.md → RTK使用指示（私が rtk プレフィックスを使うよう指示）
	• ~/.claude/settings.json → 既存の手動フック（併存）
今後のセッションでは git、ls、grep、find、diff などのコマンドを自動的に rtk 経由で実行してトークンを節約します。VSCodeを再起動すると ~/.claude/CLAUDE.md が確実に読み込まれます。

----------------------------------------------------------------------------------

REX_AI以下の各リポジトリでも使可能

rtk init -g（グローバルフラグ）で設定したため、~/.claude/CLAUDE.md に指示が書かれています。Claude Codeはすべてのプロジェクトで起動時にこのグローバルCLAUDE.mdを読み込むため、以下すべてのリポジトリで自動的にRTKが有効になります：
リポジトリ	対象
C:\Python\REX_AI\Setona_HP	✅ 現在のプロジェクト
C:\Python\REX_AI\BL_Project	✅ 自動適用
C:\Python\REX_AI\Daily_Log	✅ 自動適用
C:\Python\REX_AI\Trade_System	✅ 自動適用
C:\Python\REX_AI\python	✅ 自動適用
仕組み： ~/.claude/CLAUDE.md はユーザーレベルのグローバル設定なので、どのディレクトリで Claude Code を起動しても読み込まれます。プロジェクトごとに追加設定は不要です。


Claudecode使用時に自動的に実行という理解で良いか？

状況が明確になりました。現状は自動ではありません。

現在の構成と問題：
仕組み	状態	説明
settings.json フック	機能しない	jq が未インストールのため動作不可
~/.claude/CLAUDE.md	機能している	私（Claude）が手動で rtk を付けて実行
つまり今は「CLAUDE.mdを読んだ私が意識して rtk git status のように実行する」という動作で、ユーザー側の操作は不要ですが、厳密には自動フックではなくClaudeの判断によります。

完全自動化するには jq のインストールが必要です。
jq をインストールすれば settings.json の PreToolUse フックが有効になり、git/ls/grep などのコマンドが自動的に rtk 経由になります。
インストール方法：
# Chocolateyがある場合
choco install jq
# または手動で
# https://jqlang.github.io/jq/download/ から jq-windows-amd64.exe をダウンロード
# → jq.exe にリネームして C:\Users\Setona\bin\ に配置
インストールしますか？

インストール完了
結果：
	• jq 1.7.1 → C:\Users\Setona\bin\jq.exe に配置 ✅
これで settings.json の PreToolUse フックが正常に機能するようになりました。
VSCode / Claude Code を再起動すると、git・ls・grep・find・diff などのコマンドが自動的に rtk 経由で実行されます。

----------------------------------------------------------------------------------
　
コーディング時以外の会話等でもrtkを実行させる

RTKはコマンド出力を圧縮するツールなので、ツール（Bash）を使わない純粋な会話ではRTKが介入できるものがありません。
ただし、「コーディング時以外でもBashコマンドを実行した際に自動適用したい」という意味であれば、現在のフックは特定コマンドしか対象にしていないので拡張できます。
現在の対象：git, ls, grep, find, diff, pytest, cargo, npm, go test, docker, kubectl, aws
全Bashコマンドをrtk経由にする場合：
Read settings.json

現在のフックのパターンを全コマンド対象に変更することは可能ですが、rtk が対応していないコマンド（例：python script.py）はそのまま素通しされるので安全です。
変更しますか？それとも現状（対応コマンドのみ自動）で十分でしょうか？

整理すると：
状況	RTKの動作
git/ls/grep 等のコマンド実行	フックで自動適用 ✅
その他のBashコマンド	現状は素通し（拡張可能）
純粋なテキスト会話	RTKが介入できるものがない（圧縮対象なし）

Bashコマンド拡張設定済完了

変更内容：
変更前	変更後
git/ls/grep 等の特定コマンドのみ	rtk で始まるコマンド以外すべて
rtk が対応していないコマンド（python 等）はそのまま素通しされるので機能上の問題はありません。二重プレフィックス（rtk rtk ...）も防いでいます。VSCode再起動後に有効になります。

----------------------------------------------------------------------------------