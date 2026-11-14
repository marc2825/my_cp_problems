[![AtCoder Algorithm Rating](https://badgen.org/img/atcoder/marc2825/rating/algorithm)](https://atcoder.jp/users/marc2825)
[![AtCoder Heuristic Rating](https://badgen.org/img/atcoder/marc2825/rating/heuristic)](https://atcoder.jp/users/marc2825?contestType=heuristic)
[![Codeforces Rating](https://codeforces-readme-stats.vercel.app/api/badge?username=marc2825)](https://codeforces.com/profile/marc2825)
[![yukicoder](https://img.shields.io/badge/yukicoder-Profile-4CAF50)](https://yukicoder.me/users/17084)
<br>
[![問題一覧](https://img.shields.io/badge/Problems-問題一覧-2563EB)](problems/README.md)
[![解説](https://img.shields.io/badge/Editorials-解説-9333EA)](editorials/README.md)
[![取得スクリプト](https://img.shields.io/badge/Tools-取得スクリプト-475569)](tools/README.md)

# 競技プログラミング自作問題アーカイブ

[marc2825](https://yukicoder.me/users/17084) が [yukicoder で作問した問題](https://yukicoder.me/users/17084/problems)を、
問題文・解説・想定解法・テストケースごとに整理して保存しています。

<!-- BEGIN AUTO:ARCHIVE_STATUS -->
最終自動更新: **2026-11-14 11:32:08 JST**

保存済み問題: **13 問** · [問題一覧](problems/README.md)
<!-- END AUTO:ARCHIVE_STATUS -->

## ディレクトリ構成

| ディレクトリ | 内容 |
| --- | --- |
| [`problems/`](problems/README.md) | 問題ごとの問題文・メタデータ・想定解・バリデータ・テストケース一覧 |
| [`editorials/`](editorials/README.md) | 解説原稿（自作問題の解説と、他の問題へのユーザー解説） |
| [`tools/`](tools/README.md) | yukicoder から自動で問題を取り込むスクリプト |
| [`tests/`](tests/) | スクリプトの単体動作テスト |

## 各問題の保存構成

各問題は `problems/yukicoder/<問題番号>_<slug>/` に保存しています。

```text
problems/yukicoder/3584_camouflage_mole/
├── README.md            # 問題ページ（各ファイルへのリンク）
├── statement.md         # 問題文（Markdown）
├── statement.html       # 問題文（ブラウザで開ける HTML）
├── editorial.md         # 解説、または解説原稿へのリンク
├── metadata.yml         # 難易度・コンテスト・実行制限など
├── solution/            # 想定解
├── validator/           # 入力の検証コード
├── checker/             # 特殊ジャッジのチェッカー（該当する問題のみ）
└── tests/               # テストケース一覧
    ├── test_in/         # テスト入力
    └── test_out/        # 期待出力
```

※ `statement.html` の数式表示にはインターネット接続が必要です。GitHub 上ではソースとして表示されるので、ローカルでブラウザから開いてください。

## 問題の取り込み

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

python tools/import_yukicoder.py --user 17084 --dry-run   # 変更内容を確認
python tools/import_yukicoder.py --user 17084             # 取り込む
```

`--user xxxxx` は、yukicoder のユーザー ID が `xxxxx` の人の作問した公開済み問題をまとめて取り込む指定です。

ログインが必要な資料（解説・想定解・バリデータ・全テストケース）の取得、再実行時の動作、
一覧の更新方法などは [tools/README.md](tools/README.md) を参照してください。

## その他のコマンド

いずれも通信なしで動き、`--dry-run` を付けると変更内容の確認だけを行います。

```bash
python tools/convert_editorials.py    # 解説 HTML を Markdown に変換
python tools/update_problem_index.py  # README・問題一覧を更新
python tools/clean_gitkeep.py         # 不要な .gitkeep を削除
```

## 今後の実装予定

- ログイン済み Cookie などの認証情報を使った完全自動の取り込み。
  解説・想定解・バリデータ・全テストケースの取得から、解説の Markdown 化、README・一覧の更新までを 1 コマンドで行う。
  （現在は `--with-assets` で一部の資料を取得できますが、ログイン状態での一括取得は実サイトで未検証です）

## ライセンス

- `tools/` と `tests/` のコード: [MIT License](tools/LICENSE)
- それ以外（問題文・解説・想定解・テストケースなど）: [CC BY 4.0](LICENSE)
