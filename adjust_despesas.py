import sqlite3


def ajustar_tabela_despesas():
    # Conexão com o banco de dados
    conn = sqlite3.connect('condominio.db')
    cursor = conn.cursor()

    # Verificar se a coluna 'mes' ainda existe
    cursor.execute("PRAGMA table_info(despesas_condominio)")
    columns = cursor.fetchall()
    if any(column[1] == "mes" for column in columns):
        print("A coluna 'mes' ainda está presente. Ajustando...")

        # Criar uma tabela temporária sem a coluna 'mes'
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS despesas_temp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            valor REAL NOT NULL,
            descricao TEXT
        )
        """)

        # Copiar os dados da tabela antiga para a nova (sem a coluna 'mes')
        cursor.execute("""
        INSERT INTO despesas_temp (data, valor, descricao)
        SELECT data, valor, descricao FROM despesas_condominio
        """)

        # Substituir a tabela antiga pela nova
        cursor.execute("DROP TABLE despesas_condominio")
        cursor.execute("ALTER TABLE despesas_temp RENAME TO despesas_condominio")
        print("Ajuste na tabela 'despesas_condominio' concluído.")
    else:
        print("A coluna 'mes' não está presente. Nenhum ajuste necessário.")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    ajustar_tabela_despesas()
