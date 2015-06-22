# Postgres provisioner.

All data are scrubbed. Using the following pattern to create the postgres data:

    pg_dump --schema-only > db.schema.sql` # Dump the database schema
    psql -c "COPY (SELECT * FROM t LIMIT 1000) TO STDOUT" > db.data.sql # Dump the data (Will not work for relational data, of course)

(On new database)

    psql -c "CREATE DATABASE db;"
    psql -c "CREATE USER u;"
    psql -c "ALTER DATABASE db OWNER TO u;"

    psql < db.schema.sql;
    psql -c "COPY t FROM STDIN" < db.data.sql;
