# Nemo Tab Restore

[English](README.md)

Nemo Tab Restore は、Nemo ファイルマネージャに Web ブラウザ風の「閉じたタブを復元」を追加する `nemo-python` 拡張機能です。

`Ctrl+W` やマウス操作で閉じたタブを `Ctrl+Shift+T` で復元できるようになります。

## 機能

- `Ctrl+W` で閉じたタブの履歴を保存
- タブの閉じるボタンやミドルクリックで閉じたタブの履歴を保存
- `Ctrl+Shift+T` で最後に閉じたタブを復元
- ショートカットキーは標準的な方法で変更可能
- 履歴上限数を環境変数で設定可能

## 必要パッケージ

Nemo 本体に加えて、この拡張機能を Nemo から読み込むための Python バインディングと GI / PyGObject 関連パッケージが必要です。ディストリビューションによっては Nemo 本体に一部の依存関係が含まれているため、追加で必要なパッケージ数は環境によって変わります。

### Linux Mint / Ubuntu 系

以下のパッケージ名は Linux Mint 22 および Ubuntu 24.04 / 26.04 系で確認しています。

```bash
sudo apt install nemo-python gir1.2-nemo-3.0 python3-gi python3-gi-cairo
```

Linux Mint では通常 Nemo 本体は標準で入っていますが、Python 拡張機能用のバインディングや GI パッケージは別途必要になる場合があります。

その他の Ubuntu 系リリースでも同系統のパッケージ名である可能性があります。インストールできない場合は、`apt search nemo-python` や `apt search gir1.2-nemo` で確認してください。

### openSUSE Tumbleweed

```bash
sudo zypper install python3-nemo typelib-1_0-Nemo-3_0
```

Tumbleweed では現在、`python3-nemo` をインストールすると、対応する Python GObject パッケージも一緒にインストールされます。

### Arch Linux

```bash
sudo pacman -S nemo nemo-python
```

Arch Linux では現在、`nemo` をインストールすると、`python-gobject` と `python-cairo` も一緒にインストールされます。

## インストール

手動でインストール:

```bash
mkdir -p ~/.local/share/nemo-python/extensions
cp nemo_tab_restore.py ~/.local/share/nemo-python/extensions/nemo_tab_restore.py
```

上記を自動化したヘルパースクリプトもあります。

```bash
./scripts/install.sh
```

インストール後は Nemo を一度完全に終了してから起動し直します。終了しないままだと、新しく配置した拡張機能が読み込まれません。

```bash
nemo -q
nemo &
```

`nemo -q` で終了したあと、デスクトップのランチャーから通常どおり起動しても構いません。

## アンインストール

手動で削除:

```bash
rm ~/.local/share/nemo-python/extensions/nemo_tab_restore.py
```

上記を自動化したヘルパースクリプトもあります。

```bash
./scripts/uninstall.sh
```

アンインストール用ヘルパースクリプトは、インストール済みの拡張機能ファイルだけを削除します。履歴とログは残します。

## 使い方

### タブを閉じる

次の操作で閉じたタブの URI を履歴に保存します。

- `Ctrl+W`
- タブの閉じるボタン
- タブのミドルクリック

履歴に保存したあと、通常どおり Nemo がタブを閉じます。

タブのコンテキストメニューから閉じる操作は現在対象外です。詳しくは [既知の制限](#既知の制限) を参照してください。

### 閉じたタブを復元

```text
Ctrl+Shift+T
```

最後に閉じた URI を履歴から取り出し、タブを復元します。

内部的には次の Nemo コマンドで既存ウィンドウにタブを開きます。

```bash
nemo --existing-window --tabs URI
```

Nemo のメニューにも `Restore Last Closed Tab` が追加されます。

## ファイル

拡張機能本体ファイル:

```text
~/.local/share/nemo-python/extensions/nemo_tab_restore.py
```

履歴ファイル:

```text
~/.local/share/nemo-tab-restore/closed-tabs.jsonl
```

ログファイル:

```text
~/.cache/nemo-tab-restore/nemo-tab-restore.log
```

## 設定

設定は環境変数で行います。一時的に試す場合は Nemo の起動時に環境変数を付けて実行できます。常に同じ設定で使いたい場合は、利用しているシェルやデスクトップ環境に合わせて `~/.profile` などに設定してください。

### ログ

```bash
NEMO_TAB_RESTORE_LOG=true nemo
NEMO_TAB_RESTORE_LOG=false nemo
```

通常は `true` / `false` を指定してください。未指定時はログ無効です。

デバッグ用にログ付きで起動する場合は、ターミナルから起動します。

```bash
nemo -q
NEMO_TAB_RESTORE_LOG=true nemo
```

### 履歴上限

```bash
NEMO_TAB_RESTORE_MAX_HISTORY=300 nemo
```

既定値と範囲:

```text
default: 100
min: 1
max: 1000
```

無効な値、空文字、最小未満の値は既定値に戻ります。最大値を超えた場合は `1000` として扱います。

## ショートカット

設定を変更しなくても、既定では `Ctrl+W` で閉じたタブを保存し、`Ctrl+Shift+T` で最後に閉じたタブを復元できます。

ショートカットキーを変更したい場合は、Nemo / GTK のアクセラレータファイルを編集します。

アクセラレータファイルの場所はディストリビューションや Nemo / GTK のバージョンによって異なります。この拡張機能は次の候補を確認します。

```text
$XDG_CONFIG_HOME/nemo/accels/nemo
$XDG_CONFIG_HOME/gtk-3.0/accels/nemo
~/.config/nemo/accels/nemo
~/.gnome2/accels/nemo
~/.config/gtk-3.0/accels/nemo
```

`$XDG_CONFIG_HOME` が設定されていて空でない場合は、その配下の候補を先に確認します。

編集する前に Nemo を終了してください。Nemo が起動したままアクセラレータファイルを編集すると、終了時に内容が上書きされることがあります。

```bash
nemo -q
```

アクセラレータファイルでは、`;` で始まる行はコメントアウトされた行です。

GTK のアクセラレータ表記では、`<Primary>` は通常 `Ctrl` キーを表します。

復元ショートカットを明示する場合は、アクセラレータファイルに次の行を追加または編集します。

```scheme
(gtk_accel_path "<Actions>/NemoTabRestore/RestoreLastClosedTab" "<Primary><Shift>t")
```

この行は、次の action に:

```text
<Actions>/NemoTabRestore/RestoreLastClosedTab
```

次のショートカットを割り当てる、という意味です。

```text
<Primary><Shift>t
```

閉じるショートカットは、Nemo 既存の close action (`<Actions>/ShellActions/Close`) の設定値を使用します。

```scheme
(gtk_accel_path "<Actions>/ShellActions/Close" "<Primary>w")
```

この行は、次の action に:

```text
<Actions>/ShellActions/Close
```

次のショートカットを割り当てる、という意味です。

```text
<Primary>w
```

復元ショートカットの既定値 `<Primary><Shift>t` は、ブラウザ風の「閉じたタブを復元」に合わせて意図的に採用しています。Nemo 側でも `<Actions>/DirViewActions/OpenInNewTab`、つまり選択項目を新しいタブで開く action の既定アクセラレータとして `<Primary><Shift>t` が定義されています。Nemo 本来の割り当てを使いたい場合は、この拡張機能の復元ショートカットをアクセラレータファイルで別のキーに変更してください。

## 構文チェック

構文チェック:

```bash
/usr/bin/python3 -m py_compile nemo_tab_restore.py
```

## デバッグ

ログ有効で Nemo を起動します。

```bash
nemo -q
sleep 1
rm -f ~/.cache/nemo-tab-restore/nemo-tab-restore.log
NEMO_TAB_RESTORE_LOG=true nemo &
```

ログを確認します。

```bash
tail -f ~/.cache/nemo-tab-restore/nemo-tab-restore.log
```

期待されるログ例:

```text
hooked window wid=0x... uri=file:///... title='Loading...'
```

## 既知の制限

- タブのコンテキストメニューから閉じる操作は履歴に保存しません。
- 開いている全タブの列挙は実装していません。
- Nemo の拡張機能です。Nautilus / Caja は対象外です。

## トラブルシューティング

### `No module named 'gi'`

Nemo Python 拡張機能は GI / PyGObject を使います。

Nemo はディストリビューション側の Python 環境で拡張機能を読み込みます。別の Python が PATH の先頭にあると、ディストリ標準 Python では読める `gi` が読めない場合があります。

確認:

```bash
which -a python3
python3 --version
python3 -c 'import gi; print(gi.__file__)'
```

期待例:

```text
/usr/bin/python3
/usr/lib/python3/dist-packages/gi/__init__.py
```

GI import 問題を調べる場合は、ディストリ標準 Python で直接確認してください。

```bash
/usr/bin/python3 -c 'import gi; print(gi.__file__)'
```

## 挙動の詳細

- 閉じるショートカットは現在の URI を保存したあと、Nemo の通常のタブを閉じる処理に任せます。
- 復元ショートカットは履歴から URI を取り出し、既存の Nemo ウィンドウに開きます。
- キー入力は押した回数ごとに処理します。ブラウザ風の挙動を優先しています。
- 同じ URI の連続履歴は抑制しません。同じフォルダを複数タブで開いて閉じた場合、閉じた回数だけ復元できる必要があります。
- タブの閉じるボタンやミドルクリックで URI をまだ把握していない非アクティブタブを閉じる場合、一時的にそのタブへ切り替えて URI を取得し、閉じた後に元のアクティブタブへ戻します。
- 現在の仕様では、閉じたタブの履歴はウィンドウ別ではなく共通で管理します。複数の Nemo ウィンドウを開いている場合でも、最後に保存された履歴から復元します。

## ライセンス

MIT License です。詳細は [LICENSE](LICENSE) を参照してください。
