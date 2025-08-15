# Database Migrations

Migration files in this directory are applied automatically when the bot
starts. Files are executed in lexical order and each file should contain the
SQL required to move the schema forward. After a migration is successfully
applied, the version number extracted from the filename is recorded in the
`schema_version` table.

To add a new migration, create a new `NNNN_description.sql` file with the next
sequential number and the necessary SQL statements.
