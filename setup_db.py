import sqlite3

# Função para conectar ao banco de dados
def connect_db():
    return sqlite3.connect('condominio.db')
def registrar_despesa(data, valor, descricao, categoria, comprovante):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO despesas_condominio (data, valor, descricao, categoria, comprovante) VALUES (?, ?, ?, ?, ?)",
        (data, valor, descricao, categoria, comprovante),
    )
    conn.commit()
    conn.close()

# Função para adicionar ou atualizar tabelas e colunas no banco de dados
def atualizar_tabela_despesas():
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE despesas_condominio ADD COLUMN comprovante TEXT")
        print("Coluna 'comprovante' adicionada à tabela 'despesas_condominio'.")
    except sqlite3.OperationalError:
        print("Coluna 'comprovante' já existe na tabela 'despesas_condominio'.")
    conn.commit()
    conn.close()

def setup_database():
    conn = connect_db()
    cursor = conn.cursor()

    # Adicionar coluna 'data' às tabelas, se ainda não existir
    try:
        cursor.execute("ALTER TABLE despesas_condominio ADD COLUMN data TEXT DEFAULT '2024-01-01'")
        print("Coluna 'data' adicionada à tabela 'despesas_condominio'.")
    except sqlite3.OperationalError:
        print("Coluna 'data' já existe na tabela 'despesas_condominio'.")

    try:
        cursor.execute("ALTER TABLE pagamentos ADD COLUMN data TEXT DEFAULT '2024-01-01'")
        print("Coluna 'data' adicionada à tabela 'pagamentos'.")
    except sqlite3.OperationalError:
        print("Coluna 'data' já existe na tabela 'pagamentos'.")

    # Criar tabelas, caso ainda não existam
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS despesas_condominio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        valor REAL NOT NULL,
        descricao TEXT,
        comprovante TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pagamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        apartamento TEXT NOT NULL,
        valor REAL NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS apartamentos (
        numero TEXT PRIMARY KEY
    )
    """)

    # Inserir os apartamentos, caso ainda não existam
    apartamentos = [str(num) for num in range(101, 105)] + [str(num) for num in range(201, 205)] + [str(num) for num in range(301, 305)]
    cursor.executemany("INSERT OR IGNORE INTO apartamentos (numero) VALUES (?)", [(ap,) for ap in apartamentos])

    # Confirmar as alterações e fechar a conexão
    conn.commit()
    conn.close()

    print("Banco de dados atualizado com sucesso!")

if __name__ == "__main__":
    setup_database()
    atualizar_tabela_despesas()
