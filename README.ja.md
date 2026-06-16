# Nemo Tab Restore

[English](README.md)

Nemo Tab Restore は、Nemo ファイルマネージャに Web ブラウザ風の「閉じたタブを復元」を追加する `nemo-python` extension です。

`Ctrl+W` で閉じたタブの URI を履歴に保存し、`Ctrl+Shift+T` で最後に閉じたタブを既存の Nemo ウィンドウに復元します。

## Features

- `Ctrl+W` または Nemo の close shortcut で、現在タブの URI を履歴に保存
- Nemo 標準の close 処理はそのまま維持
- `Ctrl+Shift+T` で最後に閉じたタブを復元
- 履歴は JSON Lines 形式で永続化
- `file://` URI は復元前にパス存在確認を行い、存在しない場合は古い履歴を試行
- 非 `file://` URI は Nemo にそのまま渡す
- ログ出力と履歴上限を環境変数で設定可能

## Requirements

Linux Mint / Ubuntu 系:

以下のパッケージ名は Linux Mint 22 および Ubuntu 24.04 / 26.04 系で確認しています。

```bash
sudo apt install nemo-python gir1.2-nemo-3.0 python3-gi python3-gi-cairo
```

Linux Mint では通常 Nemo 本体は標準で入っていますが、Python extension binding や GI パッケージは別途必要になる場合があります。

その他の Ubuntu 系リリースでも同系統のパッケージ名である可能性があります。インストールできない場合は、`apt search nemo-python` や `apt search gir1.2-nemo` で確認してください。

openSUSE Tumbleweed:

```bash
sudo zypper install python3-nemo typelib-1_0-Nemo-3_0
```

Tumbleweed では現在、`python3-nemo` が `python313-gobject`、`python313-gobject-Gdk`、`python313-gobject-cairo` などの対応する Python GObject パッケージを依存として引きます。

Arch Linux:

```bash
sudo pacman -S nemo nemo-python
```

Arch Linux では現在、`nemo` が `python-gobject` と `python-cairo` を依存として引きます。

## Install

helper script でインストール:

```bash
./scripts/install.sh
```

または手動でインストール:

```bash
mkdir -p ~/.local/share/nemo-python/extensions
cp nemo_tab_restore.py ~/.local/share/nemo-python/extensions/nemo_tab_restore.py
```

Nemo を再起動します。

```bash
nemo -q
NEMO_TAB_RESTORE_LOG=1 nemo &
```

通常利用でログが不要な場合は、環境変数なしで起動してください。

## Uninstall

helper script でアンインストール:

```bash
./scripts/uninstall.sh
```

uninstall script はインストール済みの extension ファイルだけを削除します。履歴とログは残します。

または手動で削除:

```bash
rm ~/.local/share/nemo-python/extensions/nemo_tab_restore.py
```

## Usage

### Close tab

```text
Ctrl+W
```

現在タブの URI を履歴に保存し、Nemo 標準の close-tab 処理に渡します。

### Restore last closed tab

```text
Ctrl+Shift+T
```

最後に閉じた URI を履歴から取り出し、次のコマンドで既存ウィンドウに復元します。

```bash
nemo --existing-window --tabs URI
```

背景メニューにも `Restore Last Closed Tab` が追加されます。

## Files

Extension install path:

```text
~/.local/share/nemo-python/extensions/nemo_tab_restore.py
```

History file:

```text
~/.local/share/nemo-tab-restore/closed-tabs.jsonl
```

Log file:

```text
~/.cache/nemo-tab-restore/nemo-tab-restore.log
```

## Configuration

### Logging

```bash
NEMO_TAB_RESTORE_LOG=1 nemo
NEMO_TAB_RESTORE_LOG=0 nemo
```

有効値:

```text
1
true
yes
on
debug
```

無効値:

```text
0
false
no
off
空文字
```

未指定時はログ無効です。

### History size

```bash
NEMO_TAB_RESTORE_MAX_HISTORY=300 nemo
```

既定値と範囲:

```text
default: 100
min: 1
max: 1000
```

無効な値、空文字、最小未満の値は既定値に戻ります。最大超過は `1000` に clamp されます。

## Shortcuts

Nemo / GTK の accel map を読みます。

候補パス:

```text
$XDG_CONFIG_HOME/nemo/accels/nemo
$XDG_CONFIG_HOME/gtk-3.0/accels/nemo
~/.config/nemo/accels/nemo
~/.gnome2/accels/nemo
~/.config/gtk-3.0/accels/nemo
```

`$XDG_CONFIG_HOME` が設定されていて空でない場合は、その配下の候補を先に確認します。

Close action:

```text
<Actions>/ShellActions/Close
```

Default:

```text
<Primary>w
```

Restore action:

```text
<Actions>/NemoTabRestore/RestoreLastClosedTab
```

Default:

```text
<Primary><Shift>t
```

この既定値は、ブラウザ風の「閉じたタブを復元」に合わせて意図的に採用しています。Nemo 側でも `<Actions>/DirViewActions/OpenInNewTab`、つまり選択項目を新しいタブで開く action の既定 accelerator として `<Primary><Shift>t` が定義されています。Nemo 本来の割り当てを使いたい場合は、この extension の restore shortcut を accel file で別のキーに変更してください。

Restore shortcut を明示したい場合は、Nemo accel file に次の行を追加します。

```scheme
(gtk_accel_path "<Actions>/NemoTabRestore/RestoreLastClosedTab" "<Primary><Shift>t")
```

## Check

Syntax check:

```bash
/usr/bin/python3 -m py_compile nemo_tab_restore.py
```

## Debugging

ログ有効で Nemo を起動します。

```bash
nemo -q
sleep 1
rm -f ~/.cache/nemo-tab-restore/nemo-tab-restore.log
NEMO_TAB_RESTORE_LOG=1 nemo &
```

ログを確認します。

```bash
tail -f ~/.cache/nemo-tab-restore/nemo-tab-restore.log
```

期待される window hook:

```text
hooked window wid=0x... uri=file:///... title='Loading...'
```

## Known limitations

- キーボードによる close shortcut のみ履歴に保存します。
- マウスによる close 操作は履歴に保存されません。
- 対象外の操作:
  - tab close button
  - middle-click tab close
  - tab context menu close
- 開いている全タブの列挙は実装していません。
- Nemo extension です。Nautilus / Caja は対象外です。

## Troubleshooting

### `No module named 'gi'`

Nemo Python extension は GI / PyGObject を使います。

Nemo はディストリビューション側の Python 環境で extension を読み込みます。別の Python が PATH の先頭にあると、ディストリ標準 Python では読める `gi` が読めない場合があります。

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

## Design notes

- close shortcut は URI を保存したあと `False` を返し、Nemo の標準 close に処理を渡します。
- restore shortcut は履歴から URI を取り出して復元し、`True` を返します。
- debounce は入れていません。押した回数だけ close / restore されるブラウザ風の挙動を優先します。
- 同じ URI の連続履歴は抑制しません。同じフォルダを複数タブで開いて閉じた場合、閉じた回数だけ復元できる必要があります。

## License

MIT License. See [LICENSE](LICENSE).
