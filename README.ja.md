# Nemo Tab Restore

[English](README.md)

Nemo Tab Restore は、Nemo ファイルマネージャに Web ブラウザ風の「閉じたタブを復元」を追加する `nemo-python` 拡張機能です。

`Ctrl+W` やマウス操作などで閉じたタブを `Ctrl+Shift+T` で復元できるようになります。

## 機能

- `Ctrl+W` で閉じたタブの履歴を保存
- マウス操作や File メニューで閉じたタブの履歴を保存
- `Ctrl+Shift+T` で最後に閉じたタブを復元
- ショートカットキーは変更可能
- 設定ファイルまたは環境変数で動作を設定可能
- 復元履歴を全ウィンドウ共有またはウィンドウ単位で管理可能
- 履歴をファイル保存またはオンメモリ保存から選択可能

## 必要パッケージ

Nemo 本体に加えて、この拡張機能を Nemo から読み込むための Python バインディングと GI / PyGObject 関連パッケージが必要です。ディストリビューションによっては Nemo 本体に一部の依存関係が含まれているため、追加で必要なパッケージ数は環境によって変わります。

### Linux Mint

Linux Mint 22.3 Cinnamon では、追加パッケージのインストールなしで動作確認しています。標準状態で `python-nemo`、`gir1.2-nemo-3.0`、`python3-gi`、`python3-gi-cairo` が利用可能でした。

まずはインストール手順に進んでください。Nemo の再起動後に拡張機能が読み込まれない場合は、次のように関連パッケージを確認してください。

```bash
dpkg -l python-nemo gir1.2-nemo-3.0 python3-gi python3-gi-cairo
```

### Ubuntu 系

Ubuntu 24.04 系では、次のパッケージ名を確認しています。

```bash
sudo apt install nemo-python gir1.2-nemo-3.0 python3-gi python3-gi-cairo
```

Ubuntu 系リリースではパッケージ名が異なる可能性があります。インストールできない場合は、`apt search nemo-python` や `apt search gir1.2-nemo` で確認してください。

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

この拡張機能本体を Nemo の Python 拡張ディレクトリにインストールします。

手動でインストールする場合:

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

インストール済みの拡張機能本体を削除します。

手動で削除する場合:

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
- タブのコンテキストメニューから閉じる操作
- File メニューの Close

履歴に保存したあと、通常どおり Nemo がタブを閉じます。

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

履歴モードが `memory` の場合、このファイルは使用しません。

ログファイル:

```text
~/.cache/nemo-tab-restore/nemo-tab-restore.log
```

設定ファイル:

```text
~/.config/nemo-tab-restore/config.env
```

## 設定

設定は環境変数または設定ファイルで行います。環境変数は一時的な上書きに向いています。常に同じ設定で使いたい場合は、起動経路に左右されない設定ファイルが使えます。

### 優先順位

上にある設定ほど優先されます。たとえば設定ファイルと環境変数で違う値を指定した場合は、環境変数の値が使われます。

```text
環境変数
設定ファイル
Nemo / GTK のアクセラレータファイル (ショートカットのみ)
既定値
```

### 環境変数

環境変数は、Nemo をターミナルから起動して一時的に設定を試す場合に便利です。

#### `NEMO_TAB_RESTORE_RESTORE_SHORTCUT`

この拡張機能の復元ショートカットを設定します。

```env
NEMO_TAB_RESTORE_RESTORE_SHORTCUT=Ctrl+Shift+T
```

既定値は `Ctrl+Shift+T` です。別のキーに変更する場合は、たとえば `Ctrl+Shift+Y` のように指定できます。

Nemo 本体と同じショートカットを指定すると、本体側の動作が隠れることがあります。Nemo 本体側のショートカットも含めて調整したい場合は、後述の[ショートカット](#ショートカット)セクションを参照してください。

#### `NEMO_TAB_RESTORE_MAX_HISTORY`

閉じたタブの履歴を保持する最大件数を設定します。

```env
NEMO_TAB_RESTORE_MAX_HISTORY=100
```

既定値は `100`、最大値は `1000` です。

#### `NEMO_TAB_RESTORE_HISTORY_MODE`

閉じたタブの履歴を保存する場所を設定します。

```env
NEMO_TAB_RESTORE_HISTORY_MODE=file
NEMO_TAB_RESTORE_HISTORY_MODE=memory
```

既定値は `file` です。閉じたタブの履歴を `~/.local/share/nemo-tab-restore/closed-tabs.jsonl` に保存します。

`memory` を指定すると、履歴は Nemo の実行中だけメモリ上に保存されます。Nemo を完全に終了すると履歴は消え、履歴ファイルへの読み書きは行いません。

#### `NEMO_TAB_RESTORE_HISTORY_SCOPE`

復元履歴を Nemo ウィンドウ間でどう扱うかを設定します。

```env
NEMO_TAB_RESTORE_HISTORY_SCOPE=shared
NEMO_TAB_RESTORE_HISTORY_SCOPE=window
NEMO_TAB_RESTORE_HISTORY_SCOPE=hybrid
```

既定値は `shared` です。

`shared` は、すべての Nemo ウィンドウで履歴を共有します。

`window` は、現在のウィンドウで閉じたタブだけを復元します。

`hybrid` は、現在のウィンドウの履歴を優先し、現在のウィンドウに復元できる履歴がない場合は、閉じられたウィンドウの履歴や旧形式の履歴も復元対象にします。

#### `NEMO_TAB_RESTORE_LOG`

デバッグ用ログの出力を設定します。

```env
NEMO_TAB_RESTORE_LOG=true
NEMO_TAB_RESTORE_LOG=false
```

通常は `true` / `false` を指定してください。未指定時はログ無効です。

#### 起動時に一時指定する例

ターミナルから起動する場合は、コマンドの前に環境変数を付けて一時的に指定できます。

```bash
NEMO_TAB_RESTORE_LOG=true nemo
```

複数の環境変数を同時に指定することもできます。

```bash
NEMO_TAB_RESTORE_LOG=true NEMO_TAB_RESTORE_MAX_HISTORY=300 nemo
```

### 設定ファイル

設定ファイルには、上記の環境変数と同じ名前・同じ値を `KEY=value` 形式で書けます。

設定ファイルは、拡張機能の初回読み込み時に存在しなければ自動作成されます。すべての設定行はコメントアウトされたサンプルとして作成されるため、必要な行だけ `#` を外して編集してください。

```text
~/.config/nemo-tab-restore/config.env
```

新しいバージョンで設定項目が増えた場合、既存の設定ファイルは自動更新されません。最新のサンプルを作り直したい場合は、必要な設定を控えたうえで `~/.config/nemo-tab-restore/config.env` を削除し、Nemo を再起動してください。

例:

```env
NEMO_TAB_RESTORE_MAX_HISTORY=300
NEMO_TAB_RESTORE_HISTORY_MODE=memory
NEMO_TAB_RESTORE_HISTORY_SCOPE=hybrid
NEMO_TAB_RESTORE_LOG=true
NEMO_TAB_RESTORE_RESTORE_SHORTCUT=Ctrl+Shift+Y
```

設定ファイルは `.env` 風の形式です。完全なシェルスクリプトではありません。

対応している形式:

```text
KEY=value
# comment
空行
```

`export`、変数展開、複雑なクォートやエスケープはサポートしません。

## ショートカット

設定を変更しなくても、既定では `Ctrl+W` で閉じたタブを保存し、`Ctrl+Shift+T` で最後に閉じたタブを復元できます。

この拡張機能は、ブラウザ風の「閉じたタブを復元」に合わせて `Ctrl+Shift+T` を使います。一方で Nemo 本体も、選択項目を新しいタブで開く action (`<Actions>/DirViewActions/OpenInNewTab`) の既定ショートカットとして `Ctrl+Shift+T` を使っています。

タブ復元だけを別のショートカットへ変更する場合は、環境変数または設定ファイルでも変更できます。詳しくは [`NEMO_TAB_RESTORE_RESTORE_SHORTCUT`](#nemo_tab_restore_restore_shortcut) を参照してください。

Nemo 本体側の「新しいタブで開く」などの Nemo 既定のショートカットも変更したい場合は、Nemo / GTK のアクセラレータファイルを編集する必要があります。

アクセラレータファイルが存在しない環境では、たとえば次のパスを手動で作成できます。その他の候補は[挙動の詳細](#挙動の詳細)を参照してください。

```text
~/.config/nemo/accels/nemo
```

編集する前に Nemo を終了してください。Nemo が起動したままアクセラレータファイルを編集すると、終了時に内容が上書きされることがあります。

```bash
nemo -q
```

GTK のアクセラレータ表記では、`<Primary>` は通常 `Ctrl` キーを表します。

アクセラレータファイルでタブ復元を `Ctrl+Shift+Y` に変更する例:

```scheme
(gtk_accel_path "<Actions>/NemoTabRestore/RestoreLastClosedTab" "<Primary><Shift>y")
```

Nemo 本体の「新しいタブで開く」を `Ctrl+Shift+Y` に変更する例:

```scheme
(gtk_accel_path "<Actions>/DirViewActions/OpenInNewTab" "<Primary><Shift>y")
```

閉じるショートカットは、Nemo 既存の close action (`<Actions>/ShellActions/Close`) の設定値を使用します。通常は変更不要です。

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

- この拡張機能は、閉じたタブを任意のタイミングで個別に復元するためのものです。Nemo 起動時に前回終了時に開いていたタブを復元するようなセッション管理は行いません。
- マウス操作によるタブ閉じる操作の捕捉は、Nemo のバージョン、テーマ、GTK の内部構造によって動作しない場合があります。その場合でも、キーボードショートカットによる閉じる操作は対象です。
- 非アクティブなタブをマウス操作で閉じる場合や、そのタブのコンテキストメニューを開く場合、URI を取得するために一時的にそのタブへ切り替わることがあります。URI 取得後は元のアクティブタブへ戻します。
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
- マウス操作で URI をまだ把握していない非アクティブタブを閉じる場合、一時的にそのタブへ切り替えて URI を取得し、閉じた後に元のアクティブタブへ戻します。
- `NEMO_TAB_RESTORE_HISTORY_SCOPE=shared` では、閉じたタブの履歴はウィンドウ別ではなく共通で管理します。
- `NEMO_TAB_RESTORE_HISTORY_SCOPE=window` と `NEMO_TAB_RESTORE_HISTORY_MODE=file` を組み合わせた場合、過去のウィンドウの履歴はファイルに残りますが、現在のウィンドウでは復元対象になりません。必要に応じて `shared` または `hybrid` に変更すると、それらの履歴も復元対象になります。
- `NEMO_TAB_RESTORE_HISTORY_SCOPE=hybrid` では、現在開いている他の Nemo ウィンドウの履歴は fallback の復元対象にしません。

アクセラレータファイルの場所はディストリビューションや Nemo / GTK のバージョンによって異なります。この拡張機能は次の候補を確認します。

```text
$XDG_CONFIG_HOME/nemo/accels/nemo
$XDG_CONFIG_HOME/gtk-3.0/accels/nemo
~/.config/nemo/accels/nemo
~/.gnome2/accels/nemo
~/.config/gtk-3.0/accels/nemo
```

`$XDG_CONFIG_HOME` が設定されていて空でない場合は、その配下の候補を先に確認します。

## ライセンス

MIT License です。詳細は [LICENSE](LICENSE) を参照してください。
