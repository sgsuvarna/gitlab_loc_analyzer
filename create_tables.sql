-- =========================================================
-- DDL Script for GitLab Lines of Code Tables
-- =========================================================

-- Drop tables if they exist (optional - for clean recreation)
-- DROP TABLE t_gitlab_lines_of_code;
-- DROP TABLE stg_gitlab_lines_of_code;
-- DROP SEQUENCE seq_gitlab_lines_of_code;

-- =========================================================
-- Create Sequence for Primary Key
-- =========================================================
CREATE SEQUENCE seq_gitlab_lines_of_code
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

-- =========================================================
-- Create Staging Table (No Primary Key)
-- =========================================================
CREATE TABLE stg_gitlab_lines_of_code (
    project             VARCHAR2(500),
    FromBranch          VARCHAR2(200),
    ToBranch            VARCHAR2(200),
    CommitSHA           VARCHAR2(100),
    Title               VARCHAR2(1000),
    AuthorName          VARCHAR2(200),
    AuthorEmail         VARCHAR2(200),
    Date                VARCHAR2(50),
    LinesAdded          NUMBER(10),
    LinesDeleted        NUMBER(10),
    TotalChanges        NUMBER(10),
    ds_create_dt        DATE DEFAULT SYSDATE
);

-- Create indexes on staging table for better merge performance
CREATE INDEX idx_stg_gitlab_proj_sha ON stg_gitlab_lines_of_code(project, CommitSHA);

-- =========================================================
-- Create Target Table (With Primary Key and Audit Columns)
-- =========================================================
CREATE TABLE t_gitlab_lines_of_code (
    gitlab_lines_of_code_id NUMBER(15) PRIMARY KEY,
    project                 VARCHAR2(500) NOT NULL,
    FromBranch              VARCHAR2(200),
    ToBranch                VARCHAR2(200),
    CommitSHA               VARCHAR2(100) NOT NULL,
    Title                   VARCHAR2(1000),
    AuthorName              VARCHAR2(200),
    AuthorEmail             VARCHAR2(200),
    Date                    VARCHAR2(50),
    LinesAdded              NUMBER(10),
    LinesDeleted            NUMBER(10),
    TotalChanges            NUMBER(10),
    ds_create_dt            DATE DEFAULT SYSDATE,
    ds_update_dt            DATE DEFAULT SYSDATE
);

-- Create indexes on target table
CREATE INDEX idx_gitlab_proj_sha ON t_gitlab_lines_of_code(project, CommitSHA);
CREATE INDEX idx_gitlab_commit ON t_gitlab_lines_of_code(CommitSHA);
CREATE INDEX idx_gitlab_project ON t_gitlab_lines_of_code(project);
CREATE INDEX idx_gitlab_author ON t_gitlab_lines_of_code(AuthorName);

-- =========================================================
-- Create Trigger for Auto-Incrementing Primary Key on INSERT
-- =========================================================
CREATE OR REPLACE TRIGGER trg_gitlab_loc_insert
BEFORE INSERT ON t_gitlab_lines_of_code
FOR EACH ROW
BEGIN
    -- Set primary key if not provided
    IF :NEW.gitlab_lines_of_code_id IS NULL THEN
        SELECT seq_gitlab_lines_of_code.NEXTVAL 
        INTO :NEW.gitlab_lines_of_code_id 
        FROM DUAL;
    END IF;
    
    -- Set ds_create_dt if not provided (should use default but ensuring it)
    IF :NEW.ds_create_dt IS NULL THEN
        :NEW.ds_create_dt := SYSDATE;
    END IF;
    
    -- Set ds_update_dt same as ds_create_dt on INSERT
    IF :NEW.ds_update_dt IS NULL THEN
        :NEW.ds_update_dt := SYSDATE;
    END IF;
END;
/

-- =========================================================
-- Create Trigger for Updating ds_update_dt on UPDATE
-- =========================================================
CREATE OR REPLACE TRIGGER trg_gitlab_loc_update
BEFORE UPDATE ON t_gitlab_lines_of_code
FOR EACH ROW
BEGIN
    -- Always update ds_update_dt on UPDATE operations
    :NEW.ds_update_dt := SYSDATE;
END;
/

-- =========================================================
-- Grant Permissions (adjust user as needed)
-- =========================================================
-- GRANT SELECT, INSERT, UPDATE, DELETE ON stg_gitlab_lines_of_code TO your_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON t_gitlab_lines_of_code TO your_user;
-- GRANT SELECT ON seq_gitlab_lines_of_code TO your_user;

-- =========================================================
-- Add Comments for Documentation
-- =========================================================
COMMENT ON TABLE stg_gitlab_lines_of_code IS 'Staging table for GitLab lines of code data - temporary storage before merge';
COMMENT ON TABLE t_gitlab_lines_of_code IS 'Target table for GitLab lines of code data - main production table';

COMMENT ON COLUMN t_gitlab_lines_of_code.gitlab_lines_of_code_id IS 'Primary key - auto-generated sequence number';
COMMENT ON COLUMN t_gitlab_lines_of_code.ds_create_dt IS 'Record creation timestamp';
COMMENT ON COLUMN t_gitlab_lines_of_code.ds_update_dt IS 'Record last update timestamp';
