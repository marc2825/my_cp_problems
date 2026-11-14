# ツール

yukicoder の問題をこのリポジトリに取り込み、問題一覧を管理するスクリプトです。

| スクリプト | 用途 | 通信 |
| --- | --- | --- |
| [`import_yukicoder.py`](import_yukicoder.py) | 問題を取得して保存する | あり |
| [`update_problem_index.py`](update_problem_index.py) | 保存済みデータから問題一覧と各問題の README を作り直す | なし |
| [`check_problem_assets.py`](check_problem_assets.py) | 足りない資料（解説・テストなど）を確認する | なし |
| [`convert_editorials.py`](convert_editorials.py) | 解説 HTML から Markdown 版を作る | なし |
| [`clean_gitkeep.py`](clean_gitkeep.py) | 不要になった `.gitkeep` を削除する | なし |

## セットアップ

Python 3.10 以上が必要です。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

コマンドはリポジトリのルートで実行します。保存先はスクリプトの場所から決まるので、
別のディレクトリから実行しても保存先は変わりません。

## 問題の取り込み

```bash
# 1 問だけ取り込む（Problem ID ではなく問題番号を指定）
python tools/import_yukicoder.py 3584

# ユーザーが作問した公開問題をまとめて取り込む
python tools/import_yukicoder.py --user 17084

# 何が変わるかだけ確認する（ファイルは書き込まない）
python tools/import_yukicoder.py --user 17084 --dry-run
```

| オプション | 説明 |
| --- | --- |
| `problem_no` | 問題番号。`--user` とどちらか一方を指定 |
| `--user ID` | 作問者のユーザー ID。作者として公開した問題が対象で、テスターとして参加した問題は含まない |
| `--dry-run` | 取得と解析だけ行い、変更計画を表示する |
| `--output DIR` | 保存先を変更する（既定: `problems/yukicoder`） |
| `--with-assets` | 解説・想定解・バリデータ・全テストも取得する（[追加資料の取得](#追加資料の取得)） |

通常の取り込みは認証なしで公開ページと公開 API だけを読みます。保存されるのは問題文（`statement.md` / `statement.html`）、
`metadata.yml`、問題ごとの `README.md` と、手動で記入する `editorial.md`・`solution/`・`validator/` の雛形です。
保存構成は[ルートの README](../README.md#各問題の保存構成) を参照してください。
作問中・公開前・非公開の問題はスキップします。

### 実行結果の見方

| 表示 | 意味 |
| --- | --- |
| `NEW` | 問題ディレクトリを新規作成 |
| `CREATE` / `UPDATE` | ファイルを新規作成／更新 |
| `UNCHANGED` / `SKIP (変更なし)` | 変更なし（書き込まない） |
| `PRESERVE` | 手編集されたファイルを保護して更新しない |
| `SKIP No.…` | 非公開などで取得対象外 |
| `PARTIAL` | 問題文や追加資料の一部を取得できなかった |
| `WARNING` / `ERROR` | 確認が必要な事項／取得・保存の失敗 |

1 問が失敗しても残りの処理は続けます。
終了コードは、すべて成功で `0`、失敗・スキップ・部分取得のいずれかがあれば `1`、引数の誤りで `2` です。

## 追加資料の取得

`--with-assets` を付けると、ログインして閲覧できる資料も取得します。
認証には、ブラウザから書き出したログイン済み Cookie か、API キー／問題の編集トークンを使います。

```bash
# Cookie を使う（Netscape 形式。リポジトリの外に置く）
python tools/import_yukicoder.py 3584 --with-assets --cookie-file ~/yukicoder-cookies.txt

# 想定解を特定ユーザーの提出に絞る
python tools/import_yukicoder.py --user 17084 --with-assets --cookie-file ~/yukicoder-cookies.txt --solution-user 17084

# トークンを使う（値ではなく環境変数名を渡す）
python tools/import_yukicoder.py 3584 --with-assets --token-env YUKICODER_API_TOKEN
```

| 取得する資料 | 保存先 | 必要な権限 |
| --- | --- | --- |
| 解説 | `editorial.html`（トークンのみの場合は `editorial.source.md` のこともある） | 閲覧できること |
| 想定解 | `solution/<提出ID>.<拡張子>` | Cookie |
| バリデータ | `validator/main.<拡張子>` | 作者・テスター・管理者 |
| 全テストケース | `tests/test_in/`, `tests/test_out/` | 閲覧できること |

- 想定解は、解説ページで「想定解」として登録された提出だけを保存します。一般の AC 提出は取得しません。
- 権限がない資料や Cookie の期限切れは `PARTIAL` として報告し、取得できた資料だけ保存します。
  テストケースは全件そろった場合だけ保存し、途中で失敗したときは既存のテストをそのまま残します。
- `--cookie-file` と `--token-env` は併用できます。
- Cookie・トークンはファイルやログに出力しません。認証付きのリクエストが別ホストへリダイレクトされた場合は送信しません。
- 使うのは読み取り専用の GET だけです。ジャッジコードやジェネレータは取得しません。

## 再実行と手動編集

既存フォルダを再利用し、差分のあるファイルだけ更新します。（変更がなければ書き込みません。）

- **生成ファイルの手編集は保護されます。** `README.md`・`statement.*`・追加資料は、前回生成時のハッシュを
  `.import-state.json` に記録しています。手編集されたファイルは `PRESERVE` と表示して上書きしません。
  自動更新に戻したいときは、ファイルを削除して再実行してください。
- **`metadata.yml` で手動編集できる項目**は `difficulty`・`tags`・`judge_type` と独自に追加したキーです。
  いずれも再実行で保持されます。`difficulty` が空欄なら、サイトの★の数を自動で記入します。
- `judge_type` が `special`（特殊ジャッジ）の問題には `checker/` を作成します。空欄ならサイトの表示から判定します。
- ファイルやディレクトリの削除・移動・改名はしません。タイトルが変わってもディレクトリ名はそのままです。
- `.import-state.json` と `problems/.index-state.json` はコミットしてください。手編集はしないでください。

## 問題一覧と不足資料の確認

取り込みのたびに、各問題の `metadata.yml` から [problems/README.md](../problems/README.md) の一覧と、
ルート README の問題数・最終更新日時を更新します。
書き換えるのは README 内の `<!-- BEGIN AUTO:... -->` と `<!-- END AUTO:... -->` で囲まれた範囲だけです。

各問題の `README.md` には、中身のあるファイルだけをリンク付きで並べます（空の雛形は載せません）。
手動でファイルを追加・編集したあとは、通信なしで問題ごとの README と一覧を作り直せます。

```bash
python tools/update_problem_index.py
```

取り込みや一覧更新のあとには、問題ごとに足りない資料（未取得の解説、空の想定解・バリデータ、
テストの欠け、特殊ジャッジのチェッカーなど）を表示します。これだけを確認したい場合は次のとおりです。

```bash
# 足りない資料を表示する
python tools/check_problem_assets.py

# 手動で資料を置くフォルダを作成する（空フォルダには .gitkeep を置く）
python tools/check_problem_assets.py --prepare-dirs
```

どちらのスクリプトも `--dry-run` と `--output` に対応しています。

## 解説の Markdown 化

`editorials/yukicoder/<問題フォルダ>/editorial.html` に解説を置き、次のコマンドを実行すると、
GitHub 上でそのまま読める `editorial.md` を同じフォルダに作ります。HTML はそのまま残ります。

```bash
python tools/convert_editorials.py
```

- 数式は GitHub が表示できる `$…$` / `$$…$$` に直し、単純な表は Markdown の表にします。
- 画像と同名のファイルがフォルダ内にあれば、外部 URL の代わりにそちらを参照します。
- `problems/` 側の `editorial.md` が取り込み時の TODO 雛形のままなら、作った Markdown 版と HTML 版へのリンクに書き換えます。
  手で書き換えた `editorial.md` はそのまま残します。問題の取り込み後に実行してください。
- 生成した `editorial.md` は HTML の変更に合わせて作り直します。修正は `editorial.html` 側で行ってください。
  先頭の自動生成コメントがない（手書きの）`editorial.md` は上書きしません。

## 不要な `.gitkeep` の削除

Git は空のフォルダを記録できないため、空のフォルダには `.gitkeep` を置いています。
フォルダに他のファイルを入れたあとは、次のコマンドで不要になった `.gitkeep` をまとめて削除できます。

```bash
python tools/clean_gitkeep.py --dry-run   # 削除対象を確認する
python tools/clean_gitkeep.py
```

- 同じフォルダ（またはその下のフォルダ）に他のファイルがある `.gitkeep` だけを削除します。
- `.git`・`.venv` などの隠しフォルダと `__pycache__` は対象外です。

## 注意点

- 画像はダウンロードせず、元サイトの URL を参照します。オフラインで使う場合は手動で保存してください。
- 数式は GitHub で表示できるよう `$…$` / `$$…$$` で保存します。
- 単純な表は Markdown の表にします。結合セルを含む表・SVG・MathML は HTML のまま残します（警告を表示）。
- `statement.html` はブラウザで開くための単独の HTML です。数式表示（MathJax）にはインターネット接続が必要です。
- サンプルは `statement.md` に含まれます。`--with-assets` なしでは `tests/` にファイル化しません。

## テスト

```bash
python -m unittest discover -s tests -v
```

ネットワーク接続なしで実行できます。

## ライセンス

`tools/` と `tests/` のコードは [MIT License](LICENSE) です。
