import csv

def generate_csv(rows, file):
    if not rows:
        return
    with open(file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

def insert_into_db(rows, cfg):
    import cx_Oracle
    dsn = cx_Oracle.makedsn(cfg["HOST"], cfg["PORT"], service_name=cfg["SERVICE"])
    conn = cx_Oracle.connect(cfg["USER"], cfg["PASSWORD"], dsn)
    cur = conn.cursor()
    sql = f"INSERT INTO {cfg['TABLE']} VALUES ({','.join(':'+str(i+1) for i in range(len(cfg['COLUMNS'])))})"
    for r in rows:
        cur.execute(sql, [r[c] for c in cfg["COLUMNS"]])
    conn.commit()
    cur.close()
    conn.close()
