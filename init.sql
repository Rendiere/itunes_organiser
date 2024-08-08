-- Create role if it doesn't exist
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'itunes_user') THEN

      CREATE ROLE itunes_user WITH LOGIN PASSWORD 'itunes_password';
   END IF;
END
$do$;

-- Create database if it doesn't exist
DO
$do$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_catalog.pg_database
        WHERE  datname = 'itunes_library') THEN

        CREATE DATABASE itunes_library;
    END IF;
END
$do$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE itunes_library TO itunes_user;