"""Databases with SQLite: the runnable examples from lesson 6.2 of the Complete Python Tutorial.

Run it with:  python3 28_sqlite.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# sqlite_crud.py
# ----------------------------------------------------------------------
import sqlite3

conn = sqlite3.connect(":memory:")      # in-memory DB for practice; use "shop.db" for a file
conn.row_factory = sqlite3.Row          # rows behave like dicts
cur = conn.cursor()

cur.executescript("""
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    price REAL NOT NULL CHECK (price >= 0),
    stock INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE sales (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    qty INTEGER NOT NULL,
    sold_on TEXT NOT NULL
);
""")

# CREATE — always use ? placeholders, NEVER f-strings (SQL injection!)
products = [("Analog Watch", 2450, 12), ("Leather Strap", 350, 40), ("Wall Clock", 899, 5)]
cur.executemany("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)", products)
cur.executemany("INSERT INTO sales (product_id, qty, sold_on) VALUES (?, ?, ?)",
                [(1, 2, "2026-11-08"), (2, 5, "2026-11-08"), (1, 1, "2026-11-09"), (3, 1, "2026-11-09")])
conn.commit()

# READ
for row in cur.execute("SELECT * FROM products WHERE price > ? ORDER BY price DESC", (500,)):
    print(dict(row))

# UPDATE & DELETE
cur.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (2, 1))
cur.execute("DELETE FROM products WHERE stock = 0")
conn.commit()
print("Watch stock:", cur.execute("SELECT stock FROM products WHERE id = 1").fetchone()["stock"])

# JOIN + GROUP BY report
report = cur.execute("""
    SELECT p.name, SUM(s.qty) AS units, SUM(s.qty * p.price) AS revenue
    FROM sales s JOIN products p ON p.id = s.product_id
    GROUP BY p.name ORDER BY revenue DESC
""").fetchall()
for r in report:
    print(f"{r['name']:<14} {r['units']:>3} units  ₹{r['revenue']:>8,.0f}")
conn.close()

# ----------------------------------------------------------------------
# sql_injection.py
# ----------------------------------------------------------------------
import sqlite3
conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE users (username TEXT, password TEXT)")
conn.execute("INSERT INTO users VALUES ('admin', 'secret')")

attack = "' OR '1'='1"

unsafe = f"SELECT * FROM users WHERE username = '{attack}' AND password = '{attack}'"
print("UNSAFE query returns:", conn.execute(unsafe).fetchall())      # logged in without a password!

safe = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (attack, attack))
print("SAFE query returns:", safe.fetchall())                         # []

# ----------------------------------------------------------------------
# transactions.py
# ----------------------------------------------------------------------
import sqlite3
conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE wallets (name TEXT PRIMARY KEY, balance INTEGER CHECK (balance >= 0))")
conn.executemany("INSERT INTO wallets VALUES (?, ?)", [("Anu", 1000), ("Rahul", 200)])
conn.commit()

def transfer(frm, to, amount):
    try:
        with conn:                                   # commits on success, rolls back on error
            conn.execute("UPDATE wallets SET balance = balance + ? WHERE name = ?", (amount, to))
            conn.execute("UPDATE wallets SET balance = balance - ? WHERE name = ?", (amount, frm))
        print(f"Transferred ₹{amount}")
    except sqlite3.IntegrityError:
        print(f"Failed: {frm} has insufficient balance — nothing changed")

transfer("Anu", "Rahul", 300)
transfer("Rahul", "Anu", 5000)
print(conn.execute("SELECT * FROM wallets").fetchall())
