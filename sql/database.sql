PRAGMA foreign_keys = ON;

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
E dati di esempio:
-- seed.sql
PRAGMA foreign_keys = ON;

INSERT INTO categories(name) VALUES
('Alimentari'),
('Trasporti'),
('Bollette');

INSERT INTO expenses(date, amount, category_id, description) VALUES
('2025-01-15', 25.00, (SELECT id FROM categories WHERE name='Alimentari'), 'Pranzo'),
('2025-01-18', 12.50, (SELECT id FROM categories WHERE name='Trasporti'), 'Metro'),
('2025-01-20', 80.00, (SELECT id FROM categories WHERE name='Bollette'), 'Luce');

INSERT INTO budgets(month, category_id, amount) VALUES
('2025-01', (SELECT id FROM categories WHERE name='Alimentari'), 300.00),
('2025-01', (SELECT id FROM categories WHERE name='Trasporti'), 120.00);
Query report (le riportiamo poi nel PDF e le implementiamo nel codice):
-- REPORT 1: Totale spese per categoria
SELECT c.name AS category, ROUND(SUM(e.amount), 2) AS total_spent
FROM categories c
LEFT JOIN expenses e ON e.category_id = c.id
GROUP BY c.id, c.name
ORDER BY total_spent DESC;

-- REPORT 2: Spese mensili vs budget
-- (per un mese specifico, es. '2025-01')
SELECT
  b.month,
  c.name AS category,
  b.amount AS budget,
  ROUND(COALESCE(SUM(e.amount), 0), 2) AS spent
FROM budgets b
JOIN categories c ON c.id = b.category_id
LEFT JOIN expenses e
  ON e.category_id = b.category_id
 AND substr(e.date, 1, 7) = b.month
WHERE b.month = ?
GROUP BY b.id, b.month, c.name, b.amount
ORDER BY c.name;

-- REPORT 3: Elenco spese ordinate per data (desc o asc)
SELECT
  e.date,
  c.name AS category,
  ROUND(e.amount, 2) AS amount,
  COALESCE(e.description, '') AS description
FROM expenses e
JOIN categories c ON c.id = e.category_id
ORDER BY e.date ASC, e.id ASC;
