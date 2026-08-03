-- =================================================================
-- 001: staff テーブルにパスワード変更管理用のカラムを追加する
-- =================================================================
-- 対象: 既にデータが入っている稼働中のデータベース
--
-- schema.sql は先頭で DROP TABLE を行うため、既存環境に流すと患者データが
-- 全て消えます。既存DBへの反映には必ずこのファイルを使用してください。
--
-- 実行方法:
--   docker compose exec -T db mysql -uroot -p"$MYSQL_ROOT_PASSWORD" rehab_db < migrations/001_add_password_change_columns.sql
--   (外部DBの場合)
--   mysql -h <host> -u <user> -p <dbname> < migrations/001_add_password_change_columns.sql
--
-- 注意: 既存の職員アカウントには must_change_password = FALSE を設定します。
--       TRUE にすると全職員がパスワード変更画面から出られなくなるためです。
--       新規に作成されるアカウントは、モデル側の default=True により
--       変更が強制されます。

ALTER TABLE staff
    ADD COLUMN `must_change_password` BOOLEAN NOT NULL DEFAULT FALSE
        COMMENT 'TRUEの間はパスワード変更画面以外を使用できない',
    ADD COLUMN `password_updated_at` TIMESTAMP NULL
        COMMENT '最後にパスワードを変更した日時';

-- 旧 schema.sql が投入していた既知の資格情報を持つアカウントが残っている場合は、
-- パスワード変更を強制します（平文パスワードが README とコメントに記載されていたため）。
UPDATE staff
SET `must_change_password` = TRUE
WHERE `username` IN ('yamada', 'sato', 'admin');
