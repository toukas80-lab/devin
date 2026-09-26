-- Read-only SQL login for Devin CLI queries against the SoftOne database.
-- Run once in SSMS (or sqlcmd) as sysadmin, on the SoftOne instance (e.g. .\SOFTONE).
-- Replace the password before running. Keep it out of git.

USE [master];
GO
IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = N'devin_ro')
    CREATE LOGIN [devin_ro] WITH PASSWORD = N'CHANGE_ME_STRONG_PASSWORD', CHECK_POLICY = ON;
GO

USE [FOUNTOUKAS];
GO
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'devin_ro')
    CREATE USER [devin_ro] FOR LOGIN [devin_ro];
GO
ALTER ROLE [db_datareader] ADD MEMBER [devin_ro];
GO
-- Belt and braces: explicitly deny writes even if a role is added later by mistake.
DENY INSERT, UPDATE, DELETE, EXECUTE ON SCHEMA::dbo TO [devin_ro];
GO

-- Verify:
-- EXECUTE AS USER = 'devin_ro'; SELECT TOP 1 CODE, NAME FROM dbo.TRDR; REVERT;
