import sqlite3

def ajustar_tabela_pagamentos():
    # Conexão com o banco de dados
    conn = sqlite3.connect('condominio.db')
    cursor = conn.cursor()

    # Verificar se a coluna 'mes' ainda existe
    cursor.execute("PRAGMA table_info(pagamentos)")
    columns = cursor.fetchall()
    if any(column[1] == "mes" for column in columns):
        print("A coluna 'mes' ainda está presente. Ajustando...")

        # Criar uma tabela temporária sem a coluna 'mes'
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pagamentos_temp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            apartamento TEXT NOT NULL,
            valor REAL NOT NULL
        )
        """)

        # Copiar os dados da tabela antiga para a nova (sem a coluna 'mes')
        cursor.execute("""
        INSERT INTO pagamentos_temp (data, apartamento, valor)
        SELECT data, apartamento, valor FROM pagamentos
        """)

        # Substituir a tabela antiga pela nova
        cursor.execute("DROP TABLE pagamentos")
        cursor.execute("ALTER TABLE pagamentos_temp RENAME TO pagamentos")
        print("Ajuste na tabela 'pagamentos' concluído.")
    else:
        print("A coluna 'mes' não está presente. Nenhum ajuste necessário.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    ajustar_tabela_pagamentos()
