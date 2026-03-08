import sqlite3

DB_NAME = "spese.db"

# ---------------------------
# CONNESSIONE E SETUP DB
# ---------------------------
def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE CHECK (length(trim(name)) > 0)
    );

    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL CHECK (
            date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]'
        ),
        amount REAL NOT NULL CHECK (amount > 0),
        category_id INTEGER NOT NULL,
        description TEXT,
        FOREIGN KEY (category_id) REFERENCES categories(id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        month TEXT NOT NULL CHECK (
            month GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]'
        ),
        category_id INTEGER NOT NULL,
        amount REAL NOT NULL CHECK (amount > 0),
        UNIQUE (month, category_id),
        FOREIGN KEY (category_id) REFERENCES categories(id)
            ON UPDATE CASCADE
            ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()

# ---------------------------
# GESTIONE CATEGORIE
# ---------------------------
def add_category():
    name = input("Nome categoria: ").strip()
    if not name:
        print("Nome non valido.")
        return

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO categories(name) VALUES (?)", (name,))
        conn.commit()
        print("Categoria aggiunta.")
    except sqlite3.IntegrityError:
        print("Categoria già esistente o nome non valido.")
    finally:
        conn.close()

def list_categories(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM categories ORDER BY id")
    return cursor.fetchall()

# ---------------------------
# INSERIMENTO SPESA
# ---------------------------
def add_expense():
    date = input("Data (YYYY-MM-DD): ").strip()
    try:
        amount = float(input("Importo: "))
        if amount <= 0:
            raise ValueError
    except ValueError:
        print("Importo non valido.")
        return

    conn = get_connection()
    cursor = conn.cursor()

    categories = list_categories(conn)
    if not categories:
        print("Nessuna categoria disponibile.")
        conn.close()
        return

    print("Categorie disponibili:")
    for c in categories:
        print(f"{c[0]} - {c[1]}")

    try:
        category_id = int(input("ID categoria: "))
    except ValueError:
        print("ID non valido.")
        conn.close()
        return

    description = input("Descrizione (opzionale): ").strip()

    try:
        cursor.execute("""
            INSERT INTO expenses(date, amount, category_id, description)
            VALUES (?, ?, ?, ?)
        """, (date, amount, category_id, description))
        conn.commit()
        print("Spesa inserita.")
    except sqlite3.IntegrityError:
        print("Errore nei dati inseriti.")
    finally:
        conn.close()

# ---------------------------
# DEFINIZIONE BUDGET
# ---------------------------
def set_budget():
    month = input("Mese (YYYY-MM): ").strip()

    conn = get_connection()
    cursor = conn.cursor()

    categories = list_categories(conn)
    if not categories:
        print("Nessuna categoria disponibile.")
        conn.close()
        return

    print("Categorie disponibili:")
    for c in categories:
        print(f"{c[0]} - {c[1]}")

    try:
        category_id = int(input("ID categoria: "))
        amount = float(input("Budget: "))
        if amount <= 0:
            raise ValueError
    except ValueError:
        print("Valori non validi.")
        conn.close()
        return

    try:
        cursor.execute("""
            INSERT OR REPLACE INTO budgets(month, category_id, amount)
            VALUES (?, ?, ?)
        """, (month, category_id, amount))
        conn.commit()
        print("Budget salvato.")
    except sqlite3.IntegrityError:
        print("Errore nel salvataggio.")
    finally:
        conn.close()

# ---------------------------
# REPORT
# ---------------------------
def report_total_per_category():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT c.name, ROUND(COALESCE(SUM(e.amount), 0), 2) AS total_spent
    FROM categories c
    LEFT JOIN expenses e ON e.category_id = c.id
    GROUP BY c.id, c.name
    ORDER BY total_spent DESC
    """)

    results = cursor.fetchall()
    print("\nTotale spese per categoria:")
    for row in results:
        print(f"{row[0]}: {row[1]}")
    conn.close()

def report_month_vs_budget():
    month = input("Inserisci mese (YYYY-MM): ").strip()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT b.month, c.name, b.amount AS budget,
           ROUND(COALESCE(SUM(e.amount), 0), 2) AS spent,
           ROUND(b.amount - COALESCE(SUM(e.amount), 0), 2) AS remaining
    FROM budgets b
    JOIN categories c ON c.id = b.category_id
    LEFT JOIN expenses e
        ON e.category_id = b.category_id
       AND substr(e.date,1,7) = b.month
    WHERE b.month = ?
    GROUP BY b.id, b.month, c.name, b.amount
    ORDER BY c.name
    """, (month,))

    results = cursor.fetchall()
    print("\nSpese vs Budget:")
    for row in results:
        print(f"{row[1]} | Budget: {row[2]} | Speso: {row[3]} | Residuo: {row[4]}")
    conn.close()

def report_expenses_ordered():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT e.date, c.name, ROUND(e.amount, 2), COALESCE(e.description, '')
    FROM expenses e
    JOIN categories c ON c.id = e.category_id
    ORDER BY e.date ASC, e.id ASC
    """)

    results = cursor.fetchall()
    print("\nElenco spese ordinate:")
    for row in results:
        print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]}")
    conn.close()

# ---------------------------
# MENU
# ---------------------------
def report_menu():
    while True:
        print("\n--- REPORT ---")
        print("1. Totale spese per categoria")
        print("2. Spese mensili vs budget")
        print("3. Elenco spese ordinate")
        print("4. Torna indietro")

        choice = input("Scelta: ").strip()

        if choice == "1":
            report_total_per_category()
        elif choice == "2":
            report_month_vs_budget()
        elif choice == "3":
            report_expenses_ordered()
        elif choice == "4":
            break
        else:
            print("Scelta non valida.")

def main_menu():
    initialize_database()

    while True:
        print("\n=== GESTIONE SPESE PERSONALI ===")
        print("1. Gestione Categorie")
        print("2. Inserisci Spesa")
        print("3. Definisci Budget Mensile")
        print("4. Visualizza Report")
        print("5. Esci")

        choice = input("Scelta: ").strip()

        if choice == "1":
            add_category()
        elif choice == "2":
            add_expense()
        elif choice == "3":
            set_budget()
        elif choice == "4":
            report_menu()
        elif choice == "5":
            print("Uscita.")
            break
        else:
            print("Scelta non valida.")

if __name__ == "__main__":
    main_menu()

