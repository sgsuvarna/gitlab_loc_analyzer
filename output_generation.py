import csv
import cx_Oracle

def generate_csv(rows, file):
    if not rows:
        return
    with open(file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

def insert_into_db(rows, cfg):
    """
    Optimized database insert using batch operations and merge statement.
    Steps:
    1. Truncate staging table
    2. Batch insert data into staging table
    3. Merge from staging to target table
    """
    if not rows:
        print("No rows to insert")
        return
    
    conn = None
    try:
        # Create DSN and connection
        dsn = cx_Oracle.makedsn(
            cfg["HOST"], 
            cfg["PORT"], 
            service_name=cfg["SERVICE"]
        )
        
        conn = cx_Oracle.connect(cfg["USER"], cfg["PASSWORD"], dsn)
        cur = conn.cursor()
        
        try:
            # Step 1: Truncate staging table
            print(f"Truncating staging table {cfg['STAGING_TABLE']}...")
            cur.execute(f"TRUNCATE TABLE {cfg['STAGING_TABLE']}")
            # Note: TRUNCATE is auto-commit in Oracle
            
            # Step 2: Batch insert into staging table
            staging_columns = cfg["COLUMNS"]
            placeholders = ','.join([f":{i+1}" for i in range(len(staging_columns))])
            insert_sql = f"""
                INSERT INTO {cfg['STAGING_TABLE']} 
                ({','.join(staging_columns)})
                VALUES ({placeholders})
            """
            
            print(f"Inserting {len(rows)} rows into staging table in batches of {cfg['BATCH_SIZE']}...")
            
            batch_data = []
            total_inserted = 0
            
            for row in rows:
                # Prepare row data in correct column order
                row_data = [row.get(col, None) for col in staging_columns]
                batch_data.append(row_data)
                
                # Execute batch when size reached
                if len(batch_data) >= cfg["BATCH_SIZE"]:
                    cur.executemany(insert_sql, batch_data)
                    total_inserted += len(batch_data)
                    print(f"  Processed {total_inserted} rows...")
                    batch_data = []
            
            # Insert remaining rows
            if batch_data:
                cur.executemany(insert_sql, batch_data)
                total_inserted += len(batch_data)
                print(f"  Processed {total_inserted} rows (final batch)")
            
            # Commit all inserts at once
            conn.commit()
            print(f"Successfully committed {total_inserted} rows to staging table.")
            
            # Step 3: Merge from staging to target table
            print(f"Merging data from staging to target table {cfg['TARGET_TABLE']}...")
            
            merge_sql = f"""
                MERGE INTO {cfg['TARGET_TABLE']} tgt
                USING {cfg['STAGING_TABLE']} stg
                ON (
                    tgt.project = stg.project 
                    AND tgt.CommitSHA = stg.CommitSHA
                )
                WHEN MATCHED THEN
                    UPDATE SET
                        tgt.FromBranch = stg.FromBranch,
                        tgt.ToBranch = stg.ToBranch,
                        tgt.Title = stg.Title,
                        tgt.AuthorName = stg.AuthorName,
                        tgt.AuthorEmail = stg.AuthorEmail,
                        tgt.Date = stg.Date,
                        tgt.LinesAdded = stg.LinesAdded,
                        tgt.LinesDeleted = stg.LinesDeleted,
                        tgt.TotalChanges = stg.TotalChanges,
                        tgt.ds_update_dt = SYSDATE
                WHEN NOT MATCHED THEN
                    INSERT (
                        project,
                        FromBranch,
                        ToBranch,
                        CommitSHA,
                        Title,
                        AuthorName,
                        AuthorEmail,
                        Date,
                        LinesAdded,
                        LinesDeleted,
                        TotalChanges
                    )
                    VALUES (
                        stg.project,
                        stg.FromBranch,
                        stg.ToBranch,
                        stg.CommitSHA,
                        stg.Title,
                        stg.AuthorName,
                        stg.AuthorEmail,
                        stg.Date,
                        stg.LinesAdded,
                        stg.LinesDeleted,
                        stg.TotalChanges
                    )
            """
            
            cur.execute(merge_sql)
            merged_rows = cur.rowcount
            conn.commit()
            
            print(f"Merge completed successfully. {merged_rows} rows affected in target table.")
            
        finally:
            # Always close cursor
            if cur:
                cur.close()
                
    except cx_Oracle.Error as e:
        error, = e.args
        print(f"Oracle error occurred: {error.code} - {error.message}")
        if conn:
            conn.rollback()
            print("Transaction rolled back due to error.")
        raise
    except Exception as e:
        print(f"Error occurred during database operation: {str(e)}")
        if conn:
            conn.rollback()
            print("Transaction rolled back due to error.")
        raise
    finally:
        # Always close connection
        if conn:
            conn.close()
            print("Database connection closed.")
