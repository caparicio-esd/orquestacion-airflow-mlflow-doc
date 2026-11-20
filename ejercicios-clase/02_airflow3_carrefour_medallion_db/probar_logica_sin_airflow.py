"""
Prueba local instantánea (sin Docker ni Airflow) de la lógica Medallion de Carrefour.
Utiliza SQLite en memoria para demostrar Bronze -> Silver (+ cuarentena) -> Gold
y verificar que reejecutar el mismo batch dos veces es 100% idempotente.
"""
import random
import sqlite3

TIENDAS = [
    ("CRF-MAD-01", "Carrefour Hortaleza", "Hipermercado", "Madrid"),
    ("CRF-MAD-02", "Carrefour Alcobendas", "Hipermercado", "Madrid"),
    ("CRF-MAD-03", "Carrefour Express Sol", "Express", "Madrid"),
    ("CRF-BCN-01", "Carrefour Glories", "Hipermercado", "Barcelona"),
    ("CRF-VLC-01", "Carrefour Campanar", "Market", "Valencia"),
]
CATEGORIAS = ["  frescos ", "ALIMENTACION", "Bebidas", "electronica", "Hogar", None]


def inicializar_bd(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE dim_tiendas (tienda_id TEXT PRIMARY KEY, nombre TEXT, formato TEXT, provincia TEXT);
        CREATE TABLE bronze_tickets_raw (
            id_ingesta INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_batch TEXT, ticket_id TEXT, tienda_id TEXT,
            cliente_club TEXT, categoria TEXT, importe_eur REAL, unidades INTEGER
        );
        CREATE TABLE silver_tickets_clean (
            ticket_id TEXT PRIMARY KEY, fecha_batch TEXT, tienda_id TEXT,
            es_socio_club INTEGER, categoria TEXT, importe_eur REAL, unidades INTEGER
        );
        CREATE TABLE silver_tickets_quarantine (
            id_error INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_batch TEXT, ticket_id TEXT, tienda_id TEXT, importe_eur REAL, motivo TEXT
        );
        CREATE TABLE gold_ventas_diarias (
            fecha_batch TEXT, tienda_id TEXT, nombre_tienda TEXT, formato TEXT,
            num_tickets INTEGER, facturacion_eur REAL, ticket_medio_eur REAL, pct_socios_club REAL,
            PRIMARY KEY (fecha_batch, tienda_id)
        );
        """
    )
    conn.executemany("INSERT INTO dim_tiendas VALUES (?, ?, ?, ?);", TIENDAS)


def ejecutar_batch(conn: sqlite3.Connection, ds: str) -> None:
    rng = random.Random(f"carrefour-{ds}")
    tiendas_ids = [t[0] for t in TIENDAS]
    lote = []
    for i in range(1, 81):
        tid = f"TKT-{ds.replace('-', '')}-{i:04d}"
        tienda = rng.choice(tiendas_ids)
        socio = rng.choice(["SI", "si", "NO", "no", "1", "0"])
        cat = rng.choice(CATEGORIAS)
        base = 22.0 if tienda == "CRF-MAD-03" else 58.0
        imp = round(rng.uniform(4.5, base * 1.9), 2)
        uds = rng.randint(1, 14)
        if i % 17 == 0:
            imp = -12.5
        elif i % 23 == 0:
            tienda = "CRF-XXX-99"
        elif i % 29 == 0:
            uds = 0
        lote.append((ds, tid, tienda, socio, cat, imp, uds))
        if i in (5, 12, 31):
            lote.append((ds, tid, tienda, socio, cat, imp, uds))

    # 1. BRONZE (idempotente por fecha)
    conn.execute("DELETE FROM bronze_tickets_raw WHERE fecha_batch = ?;", (ds,))
    conn.executemany(
        "INSERT INTO bronze_tickets_raw (fecha_batch, ticket_id, tienda_id, cliente_club, categoria, importe_eur, unidades) VALUES (?, ?, ?, ?, ?, ?, ?);",
        lote,
    )

    # 2. SILVER + CUARENTENA
    tiendas_ok = {r[0] for r in conn.execute("SELECT tienda_id FROM dim_tiendas;")}
    crudos = conn.execute(
        "SELECT ticket_id, tienda_id, cliente_club, categoria, importe_eur, unidades FROM bronze_tickets_raw WHERE fecha_batch = ? ORDER BY id_ingesta;",
        (ds,),
    ).fetchall()
    vistos, validos, cuarentena = set(), [], []
    for ticket_id, tienda_id, socio, cat, imp, uds in crudos:
        if ticket_id in vistos:
            cuarentena.append((ds, ticket_id, tienda_id, imp, "ticket_duplicado_tpv"))
            continue
        vistos.add(ticket_id)
        if tienda_id not in tiendas_ok:
            cuarentena.append((ds, ticket_id, tienda_id, imp, "tienda_desconocida"))
            continue
        if imp is None or imp <= 0:
            cuarentena.append((ds, ticket_id, tienda_id, imp, "importe_no_positivo"))
            continue
        if uds is None or uds <= 0:
            cuarentena.append((ds, ticket_id, tienda_id, imp, "unidades_invalidas"))
            continue
        es_socio = 1 if str(socio).strip().upper() in {"SI", "1", "TRUE"} else 0
        validos.append((ticket_id, ds, tienda_id, es_socio, (cat or "SIN_CATEGORIA").strip().upper(), imp, uds))

    conn.execute("DELETE FROM silver_tickets_clean WHERE fecha_batch = ?;", (ds,))
    conn.execute("DELETE FROM silver_tickets_quarantine WHERE fecha_batch = ?;", (ds,))
    conn.executemany("INSERT INTO silver_tickets_clean VALUES (?, ?, ?, ?, ?, ?, ?);", validos)
    conn.executemany(
        "INSERT INTO silver_tickets_quarantine (fecha_batch, ticket_id, tienda_id, importe_eur, motivo) VALUES (?, ?, ?, ?, ?);",
        cuarentena,
    )

    # 3. GOLD
    conn.execute("DELETE FROM gold_ventas_diarias WHERE fecha_batch = ?;", (ds,))
    conn.execute(
        """
        INSERT INTO gold_ventas_diarias
        SELECT t.fecha_batch, t.tienda_id, d.nombre, d.formato,
               COUNT(*), ROUND(SUM(t.importe_eur), 2), ROUND(AVG(t.importe_eur), 2),
               ROUND(100.0 * AVG(t.es_socio_club), 2)
        FROM silver_tickets_clean t
        JOIN dim_tiendas d ON d.tienda_id = t.tienda_id
        WHERE t.fecha_batch = ?
        GROUP BY t.fecha_batch, t.tienda_id, d.nombre, d.formato;
        """,
        (ds,),
    )
    conn.commit()


if __name__ == "__main__":
    con = sqlite3.connect(":memory:")
    inicializar_bd(con)

    # Ejecutamos DOS veces la misma fecha para verificar idempotencia
    ejecutar_batch(con, "2026-11-20")
    primera = con.execute("SELECT * FROM gold_ventas_diarias ORDER BY tienda_id;").fetchall()
    ejecutar_batch(con, "2026-11-20")
    segunda = con.execute("SELECT * FROM gold_ventas_diarias ORDER BY tienda_id;").fetchall()
    assert primera == segunda, "Error: el pipeline no es idempotente"

    n_bronze = con.execute("SELECT COUNT(*) FROM bronze_tickets_raw;").fetchone()[0]
    n_silver = con.execute("SELECT COUNT(*) FROM silver_tickets_clean;").fetchone()[0]
    n_quar = con.execute("SELECT COUNT(*) FROM silver_tickets_quarantine;").fetchone()[0]
    print(f"Idempotencia verificada (OK) | Bronze={n_bronze} -> Silver={n_silver} + Cuarentena={n_quar}\n")
    print("Capa GOLD (ventas_diarias_tienda):")
    for row in segunda:
        print(f"  {row[0]} | {row[1]} ({row[2]:<22}) | {row[4]:2d} tickets | {row[5]:8.2f} EUR | medio {row[6]:6.2f} EUR | socios {row[7]:5.1f}%")
