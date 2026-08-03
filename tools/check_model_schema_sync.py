"""SQLAlchemyモデルと schema.sql の整合を検証する静的チェック。

DB接続を必要とせず、CIで実行できます。以下の2点を検証します。

1. モデルのカラム集合と schema.sql の CREATE TABLE のカラム集合が一致すること
2. schema.sql 内の INSERT が、同ファイルの CREATE TABLE に存在しないカラムを
   参照していないこと（MySQL の ERROR 1054 を事前に検出する）

使い方:
    python tools/check_model_schema_sync.py            # 作業ツリーの schema.sql を検証
    python tools/check_model_schema_sync.py --git HEAD # 指定リビジョンの schema.sql を検証

終了コード 0 で成功、1 で不整合ありです。

モデルは import せず ast で解析します。app パッケージを import すると app/__init__.py が
ブループリント経由で rag_manager を読み込み、LLMクライアントの構築とAPIキーの存在確認まで
走ってしまうため、CIで動かせなくなるからです。
"""

import argparse
import ast
import os
import re
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SCHEMA_PATH = os.path.join(ROOT, "schema.sql")
MODELS_DIR = os.path.join(ROOT, "app", "models")

# CREATE TABLE 本体からカラム名を拾うための型キーワード
_TYPE_KEYWORDS = r"BOOLEAN|INT\b|TEXT|VARCHAR|DATE\b|DECIMAL|TIMESTAMP|JSON"


def load_schema_sql(git_rev=None):
    """schema.sql の中身を返す。git_rev 指定時はそのリビジョンから取得する。"""
    if git_rev:
        result = subprocess.run(
            ["git", "show", f"{git_rev}:schema.sql"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
        )
        if result.returncode != 0:
            raise SystemExit(f"git show に失敗しました: {result.stderr}")
        return result.stdout
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return f.read()


def parse_models():
    """app/models/*.py を ast で解析し {テーブル名: set(カラム名)} を返す。"""
    tables = {}
    for filename in sorted(os.listdir(MODELS_DIR)):
        if not filename.endswith(".py") or filename == "__init__.py":
            continue
        with open(os.path.join(MODELS_DIR, filename), encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename)

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            table_name = None
            columns = set()
            for stmt in node.body:
                if not isinstance(stmt, ast.Assign) or not isinstance(stmt.targets[0], ast.Name):
                    continue
                target = stmt.targets[0].id

                if target == "__tablename__" and isinstance(stmt.value, ast.Constant):
                    table_name = stmt.value.value
                elif (
                    isinstance(stmt.value, ast.Call)
                    and isinstance(stmt.value.func, ast.Name)
                    and stmt.value.func.id == "Column"
                ):
                    columns.add(target)

            if table_name:
                tables[table_name] = columns

        # Table(...) で定義される中間テーブル（例: staff_patients_association）
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "Table"
                and node.args
                and isinstance(node.args[0], ast.Constant)
            ):
                columns = {
                    arg.args[0].value
                    for arg in node.args[1:]
                    if isinstance(arg, ast.Call)
                    and isinstance(arg.func, ast.Name)
                    and arg.func.id == "Column"
                    and arg.args
                    and isinstance(arg.args[0], ast.Constant)
                }
                if columns:
                    tables[node.args[0].value] = columns

    return tables


def strip_line_comments(sql):
    """`-- ...` 形式の行コメントを除去する。

    schema.sql はカラム列挙の途中に `-- ADL (FIM/BI)` のようなコメントを挟んでおり、
    そこに含まれる括弧が構文解析を打ち切ってしまうため、解析前に落とします。
    """
    return re.sub(r"--[^\n]*", "", sql)


def parse_create_tables(sql):
    """{テーブル名: set(カラム名)} を返す。"""
    tables = {}
    for match in re.finditer(
        r"CREATE TABLE(?:\s+IF NOT EXISTS)?\s+`?(\w+)`?\s*\((.*?)\n\)\s*ENGINE",
        sql,
        re.S | re.I,
    ):
        table_name, body = match.group(1), match.group(2)
        # 行頭アンカーは使わない: schema.sql は1行に複数カラムを宣言している箇所がある
        tables[table_name] = set(re.findall(rf"`(\w+)`\s+(?:{_TYPE_KEYWORDS})", body, re.I))
    return tables


def parse_inserts(sql):
    """[(テーブル名, [カラム名, ...]), ...] を返す。"""
    inserts = []
    for match in re.finditer(r"INSERT INTO\s+`?(\w+)`?\s*\(([^)]*)\)", sql, re.I):
        table_name = match.group(1)
        columns = re.findall(r"`(\w+)`", match.group(2))
        inserts.append((table_name, columns))
    return inserts


def check(git_rev=None):
    sql = strip_line_comments(load_schema_sql(git_rev))
    schema_tables = parse_create_tables(sql)
    model_tables = parse_models()
    errors = []

    if not model_tables:
        errors.append("app/models/ からテーブル定義を1件も抽出できませんでした（解析ロジックの破損を疑ってください）")

    # --- 1. モデル vs schema.sql ---
    for table_name, model_columns in sorted(model_tables.items()):
        if table_name not in schema_tables:
            errors.append(f"[{table_name}] モデルに定義があるが schema.sql に CREATE TABLE がありません")
            continue

        sql_columns = schema_tables[table_name]

        for name in sorted(model_columns - sql_columns):
            errors.append(f"[{table_name}] モデルのみ: {name} (SELECT時に ERROR 1054 になります)")
        for name in sorted(sql_columns - model_columns):
            errors.append(f"[{table_name}] schema.sqlのみ: {name} (この列には保存されません)")

        if model_columns == sql_columns:
            print(f"  OK  {table_name}: {len(model_columns)} カラム一致")

    # --- 2. CREATE されるテーブルは全て DROP されているか ---
    # 全 CREATE が IF NOT EXISTS のため、DROP 漏れがあるとそのテーブルだけ旧データごと
    # 生き残り、再作成された親テーブルに対して外部キーが宙に浮きます。
    dropped = set(re.findall(r"DROP TABLE IF EXISTS\s+`?(\w+)`?", sql, re.I))
    for table_name in sorted(set(schema_tables) - dropped):
        errors.append(
            f"[{table_name}] CREATE TABLE はあるが DROP TABLE がありません "
            "(再実行時に旧データが残り、外部キーが宙に浮きます)"
        )

    # --- 3. INSERT vs CREATE TABLE ---
    for table_name, columns in parse_inserts(sql):
        if table_name not in schema_tables:
            errors.append(f"[INSERT INTO {table_name}] 対応する CREATE TABLE がありません")
            continue
        undefined = [c for c in columns if c not in schema_tables[table_name]]
        if undefined:
            errors.append(
                f"[INSERT INTO {table_name}] CREATE TABLE に存在しないカラムを {len(undefined)} 個参照しています: "
                + ", ".join(undefined[:5])
                + (" ..." if len(undefined) > 5 else "")
            )

    return errors


def main():
    parser = argparse.ArgumentParser(description="モデルと schema.sql の整合を検証します")
    parser.add_argument("--git", metavar="REV", help="指定したgitリビジョンの schema.sql を検証します")
    args = parser.parse_args()

    print("=== モデル / schema.sql 整合チェック ===")
    errors = check(args.git)

    if errors:
        print(f"\n不整合 {len(errors)} 件:")
        for e in errors:
            print(f"  NG  {e}")
        return 1

    print("\n不整合はありません。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
