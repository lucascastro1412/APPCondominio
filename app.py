import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime
import os

# Conexão com o banco de dados
def connect_db():
    return sqlite3.connect('condominio.db')
# Função para verificar os caminhos das imagens
def verificar_caminhos():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT comprovante FROM despesas_condominio")
    comprovantes = cursor.fetchall()
    for c in comprovantes:
        print(f"Caminho no Banco: {c[0]}")
    conn.close()

verificar_caminhos()


# Função para configurar o banco de dados
def setup_database():
    conn = connect_db()
    cursor = conn.cursor()

    # Criar tabelas, caso não existam
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS despesas_condominio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT NOT NULL,
        valor REAL NOT NULL,
        descricao TEXT NOT NULL,
        categoria TEXT DEFAULT 'Outros'
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pagamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT NOT NULL,
        apartamento TEXT NOT NULL,
        valor REAL NOT NULL
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS apartamentos (
        numero TEXT PRIMARY KEY,
        fracao_ideal REAL DEFAULT 1.0
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ajustes_saldo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT NOT NULL,
        ajuste REAL NOT NULL
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS configuracoes (
        id INTEGER PRIMARY KEY,
        valor_mensal REAL DEFAULT 50.0,
        taxa_multa REAL DEFAULT 2.0
    )
    """)
    cursor.execute("INSERT OR IGNORE INTO configuracoes (id) VALUES (1)")

    # Inserir apartamentos padrão (101 a 304)
    apartamentos = [str(num) for num in range(101, 105)] + [str(num) for num in range(201, 205)] + [str(num) for num in range(301, 305)]
    cursor.executemany("INSERT OR IGNORE INTO apartamentos (numero) VALUES (?)", [(ap,) for ap in apartamentos])

    conn.commit()
    conn.close()

# Função para registrar despesas
def registrar_despesa(data, valor, descricao, categoria, comprovante):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO despesas_condominio (data, valor, descricao, categoria, comprovante) VALUES (?, ?, ?, ?, ?)",
        (data, valor, descricao, categoria, comprovante),
    )
    conn.commit()
    conn.close()


# Função para registrar pagamentos
def registrar_pagamento(data, apartamento, valor):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO pagamentos (data, apartamento, valor) VALUES (?, ?, ?)",
        (data, apartamento, valor),
    )
    conn.commit()
    conn.close()

def adicionar_coluna_comprovante():
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE despesas_condominio ADD COLUMN comprovante TEXT")
        print("Coluna 'comprovante' adicionada com sucesso!")
    except sqlite3.OperationalError:
        print("Coluna 'comprovante' já existe.")
    conn.commit()
    conn.close()

# Chamar essa função no setup
adicionar_coluna_comprovante()

# Função para calcular saldo
def calcular_saldo():
    conn = connect_db()
    cursor = conn.cursor()

    # Total de pagamentos recebidos
    cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM pagamentos")
    total_recebido = cursor.fetchone()[0]

    # Total de despesas
    cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM despesas_condominio")
    total_despesas = cursor.fetchone()[0]

    # Ajustes manuais de saldo
    cursor.execute("SELECT COALESCE(SUM(ajuste), 0) FROM ajustes_saldo")
    total_ajustes = cursor.fetchone()[0]

    conn.close()

    # Saldo calculado
    saldo = total_recebido - total_despesas + total_ajustes
    return saldo, total_recebido, total_despesas, total_ajustes

# Função para ajustar saldo manualmente
def ajustar_saldo(ajuste):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ajustes_saldo (data, ajuste) VALUES (datetime('now'), ?)", (ajuste,))
    conn.commit()
    conn.close()

# Função para exportar para Excel
def exportar_para_excel(df, nome_arquivo):
    df.to_excel(nome_arquivo, index=False)


# Função para apagar e recriar o banco de dados
def delete_and_recreate_database():
    # Remove o arquivo do banco de dados
    import os
    db_path = 'condominio.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Banco de dados apagado com sucesso!")
    else:
        print("O banco de dados não existe, criando um novo.")

    # Recria o banco de dados
    setup_database()
    print("Banco de dados recriado com sucesso!")

def gerar_relatorio_inadimplencia():
    conn = connect_db()
    cursor = conn.cursor()

    # Obter pagamentos agrupados por apartamento
    cursor.execute("""
    SELECT apartamento, SUM(valor) AS total_pago
    FROM pagamentos
    GROUP BY apartamento
    """)
    pagamentos = cursor.fetchall()

    # Total esperado por apartamento até o mês atual
    mes_atual = datetime.now().month
    valor_mensal = 50.0
    total_esperado = valor_mensal * mes_atual

    conn.close()

    # Criar DataFrame com inadimplências
    data = []
    apartamentos = [str(num) for num in range(101, 105)] + [str(num) for num in range(201, 205)] + [str(num) for num in range(301, 305)]
    pagamentos_dict = {apt: valor for apt, valor in pagamentos}

    for apartamento in apartamentos:
        total_pago = pagamentos_dict.get(apartamento, 0.0)
        saldo_devedor = total_esperado - total_pago if total_esperado > total_pago else 0.0
        data.append([apartamento, total_pago, total_esperado, saldo_devedor])

    df_inadimplencia = pd.DataFrame(data, columns=["Apartamento", "Total Pago (R$)", "Total Esperado (R$)", "Saldo Devedor (R$)"])

    return df_inadimplencia

def gerar_relatorio_inadimplencia_apartamento():
    conn = connect_db()
    cursor = conn.cursor()

    # Obter pagamentos agrupados por apartamento
    cursor.execute("""
    SELECT apartamento, SUM(valor) AS total_pago
    FROM pagamentos
    GROUP BY apartamento
    """)
    pagamentos = cursor.fetchall()

    # Total esperado por apartamento até o mês atual
    mes_atual = datetime.now().month
    valor_mensal = 50.0
    total_esperado = valor_mensal * mes_atual

    conn.close()

    # Criar DataFrame com inadimplências
    data = []
    apartamentos = [str(num) for num in range(101, 105)] + [str(num) for num in range(201, 205)] + [str(num) for num in range(301, 305)]
    pagamentos_dict = {apt: valor for apt, valor in pagamentos}

    for apartamento in apartamentos:
        total_pago = pagamentos_dict.get(apartamento, 0.0)
        saldo_devedor = total_esperado - total_pago if total_esperado > total_pago else 0.0
        data.append([apartamento, total_pago, total_esperado, saldo_devedor])

    df_apartamento = pd.DataFrame(data, columns=["Apartamento", "Total Pago (R$)", "Total Esperado (R$)", "Saldo Devedor (R$)"])
    return df_apartamento
def registrar_despesa(data, valor, descricao, categoria, comprovante):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO despesas_condominio (data, valor, descricao, categoria, comprovante) VALUES (?, ?, ?, ?, ?)",
        (data, valor, descricao, categoria, comprovante),
    )
    conn.commit()
    conn.close()


def gerar_relatorio_despesas(data_inicio=None, data_fim=None, categoria=None):
    conn = connect_db()
    cursor = conn.cursor()

    # Construir a consulta SQL com filtros opcionais
    query = """
    SELECT data, valor, descricao, categoria, comprovante
    FROM despesas_condominio
    WHERE 1=1
    """
    params = []

    if data_inicio:
        query += " AND date(data) >= date(?)"
        params.append(data_inicio)

    if data_fim:
        query += " AND date(data) <= date(?)"
        params.append(data_fim)

    if categoria and categoria != "Todas":
        query += " AND categoria = ?"
        params.append(categoria)

    query += " ORDER BY data"

    # Executar a consulta e obter os resultados
    cursor.execute(query, params)
    despesas = cursor.fetchall()
    conn.close()

    # Converter os resultados em DataFrame
    df_despesas = pd.DataFrame(despesas, columns=["Data", "Valor (R$)", "Descrição", "Categoria", "Comprovante"])
    return df_despesas


def gerar_relatorio_inadimplencia_mensal():
    conn = connect_db()
    cursor = conn.cursor()

    # Obter pagamentos agrupados por apartamento e mês
    cursor.execute("""
    SELECT apartamento, strftime('%m', data) AS mes, SUM(valor) AS total_pago
    FROM pagamentos
    GROUP BY apartamento, mes
    """)
    pagamentos = cursor.fetchall()

    conn.close()

    # Criar estrutura para exibir inadimplência mensal
    meses = [f"Mês {i:02}" for i in range(1, 13)]
    apartamentos = [str(num) for num in range(101, 105)] + [str(num) for num in range(201, 205)] + [str(num) for num in range(301, 305)]
    valor_mensal = 50.0

    data = []
    for apartamento in apartamentos:
        linha = [apartamento]
        for mes in range(1, 13):
            valor_pago = sum([p[2] for p in pagamentos if p[0] == apartamento and int(p[1]) == mes])
            saldo_devedor = valor_mensal - valor_pago if mes <= datetime.now().month and valor_pago < valor_mensal else 0.0
            linha.append(saldo_devedor)
        data.append(linha)

    colunas = ["Apartamento"] + meses
    df_mensal = pd.DataFrame(data, columns=colunas)
    return df_mensal


# Configuração inicial
setup_database()

# Interface Streamlit
st.title("Controle de Condomínio")

menu = st.sidebar.selectbox(
    "Menu",
    ["Registrar Despesas", "Registrar Pagamentos", "Relatório Mensal", "Relatório Anual", "Conta Corrente", "Dashboard", "Relatório de Despesas","Administração"]
)



if menu == "Registrar Despesas":
    st.header("Registrar Despesas do Condomínio")
    data = st.date_input("Data da Despesa")
    valor = st.number_input("Valor da Despesa (R$)", min_value=0.0, step=0.01)
    descricao = st.text_input("Descrição")
    categoria = st.selectbox("Categoria", ["Manutenção", "Limpeza", "Segurança", "Outros"])
    comprovante = st.file_uploader("Comprovante de Pagamento (Imagem)", type=["png", "jpg", "jpeg"])

    if st.button("Registrar"):
        # Salvar imagem no diretório
        if comprovante:
            import os

            dir_path = "comprovantes/"
            os.makedirs(dir_path, exist_ok=True)
            file_path = os.path.join(dir_path, comprovante.name)
            with open(file_path, "wb") as f:
                f.write(comprovante.getbuffer())
            registrar_despesa(data.isoformat(), valor, descricao, categoria, file_path)
            st.success("Despesa registrada com comprovante!")
        else:
            registrar_despesa(data.isoformat(), valor, descricao, categoria, None)
            st.warning("Despesa registrada sem comprovante!")

elif menu == "Registrar Despesas":
    st.header("Registrar Despesas do Condomínio")
    data = st.date_input("Data da Despesa")
    valor = st.number_input("Valor da Despesa (R$)", min_value=0.0, step=0.01)
    descricao = st.text_input("Descrição")
    categoria = st.selectbox("Categoria", ["Manutenção", "Limpeza", "Segurança", "Outros"])
    comprovante = st.file_uploader("Comprovante da Despesa (opcional)", type=["png", "jpg", "jpeg"])
    if comprovante:
        comprovante_path = f"comprovantes/{comprovante.name}"
        with open(comprovante_path, "wb") as f:
            f.write(comprovante.getbuffer())
    else:
        comprovante_path = None

    if st.button("Registrar"):
        registrar_despesa(data.isoformat(), valor, descricao, categoria, comprovante_path)
        st.success("Despesa registrada com sucesso!")

    if st.button("Registrar"):
        comprovante_path = None
        if comprovante is not None:
            comprovante_path = f"comprovantes/{comprovante.name}"
            with open(comprovante_path, "wb") as f:
                f.write(comprovante.read())

        registrar_despesa(data.isoformat(), valor, descricao, categoria, comprovante_path)
        st.success("Despesa registrada com sucesso!")

elif menu == "Relatório de Despesas":
    st.header("Relatório de Despesas do Condomínio")
    data_inicio = st.date_input("Data de Início")
    data_fim = st.date_input("Data de Fim")

    if data_inicio > data_fim:
        st.error("A data de início não pode ser posterior à data de fim.")
    elif st.button("Gerar Relatório"):
        conn = connect_db()
        cursor = conn.cursor()

        # Recuperar despesas no período
        cursor.execute("""
        SELECT data, valor, descricao, categoria, comprovante
        FROM despesas_condominio
        WHERE date(data) BETWEEN date(?) AND date(?)
        ORDER BY data
        """, (data_inicio.isoformat(), data_fim.isoformat()))
        despesas = cursor.fetchall()
        conn.close()

        if despesas:
            # Criar DataFrame para exibir os dados tabulares
            df_despesas = pd.DataFrame(despesas,
                                       columns=["Data", "Valor (R$)", "Descrição", "Categoria", "Comprovante"])

            # Exibir as despesas no formato customizado
            st.write("**Relatório de Despesas**")
            for _, row in df_despesas.iterrows():
                col1, col2 = st.columns([3, 1])  # Layout: 3 partes para texto, 1 para imagem
                with col1:
                    st.write(f"**Data:** {row['Data']}")
                    st.write(f"**Valor:** R$ {row['Valor (R$)']:.2f}")
                    st.write(f"**Descrição:** {row['Descrição']}")
                    st.write(f"**Categoria:** {row['Categoria']}")
                with col2:
                    if pd.notna(row["Comprovante"]):
                        st.image(row["Comprovante"], caption="Comprovante", use_container_width=True)
                    else:
                        st.write("Sem Comprovante")
        else:
            st.warning("Nenhuma despesa encontrada no período selecionado.")



elif menu == "Relatório de Inadimplência":
    st.header("Relatório de Inadimplência")

    # Relatório por Apartamento
    st.subheader("Por Apartamento")
    if st.button("Gerar Relatório por Apartamento"):
        df_apartamento = gerar_relatorio_inadimplencia_apartamento()
        st.dataframe(df_apartamento)
        total_devedor = df_apartamento["Saldo Devedor (R$)"].sum()
        st.write(f"**Total Geral de Saldo Devedor: R$ {total_devedor:.2f}**")

    # Relatório por Mês
    st.subheader("Por Mês")
    if st.button("Gerar Relatório por Mês"):
        df_mensal = gerar_relatorio_inadimplencia_mensal()
        st.dataframe(df_mensal)

elif menu == "Registrar Pagamentos":
    st.header("Registrar Pagamento")
    data = st.date_input("Data do Pagamento")
    apartamento = st.selectbox("Apartamento", [
        "101", "102", "103", "104",
        "201", "202", "203", "204",
        "301", "302", "303", "304"
    ])
    valor = st.number_input("Valor Pago (R$)", min_value=0.0, step=0.01)
    if st.button("Registrar"):
        registrar_pagamento(data.isoformat(), apartamento, valor)
        st.success(f"Pagamento de R$ {valor:.2f} registrado com sucesso para o apartamento {apartamento}!")

elif menu == "Relatório Mensal":
    st.header("Relatório Mensal")
    data_inicio = st.date_input("Data de Início")
    data_fim = st.date_input("Data de Fim")
    if data_inicio > data_fim:
        st.error("A data de início não pode ser posterior à data de fim.")
    elif st.button("Gerar Relatório"):
        conn = connect_db()
        cursor = conn.cursor()

        # Buscar despesas
        cursor.execute("""
        SELECT data, valor, descricao, categoria
        FROM despesas_condominio
        WHERE date(data) BETWEEN date(?) AND date(?)
        ORDER BY data
        """, (data_inicio.isoformat(), data_fim.isoformat()))
        despesas = cursor.fetchall()

        # Buscar pagamentos
        cursor.execute("""
        SELECT apartamento, SUM(valor) AS total_pago
        FROM pagamentos
        WHERE date(data) BETWEEN date(?) AND date(?)
        GROUP BY apartamento
        ORDER BY apartamento
        """, (data_inicio.isoformat(), data_fim.isoformat()))
        pagamentos = cursor.fetchall()

        conn.close()

        # Criar DataFrames
        df_despesas = pd.DataFrame(despesas, columns=["Data", "Valor (R$)", "Descrição", "Categoria"])
        df_pagamentos = pd.DataFrame(pagamentos, columns=["Apartamento", "Total Pago (R$)"])

        # Exibir DataFrame de despesas
        st.write("**Despesas no Período**")
        if not df_despesas.empty:
            st.write(df_despesas.to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.write("Nenhuma despesa encontrada no período selecionado.")

        # Exibir DataFrame de pagamentos
        st.write("**Pagamentos no Período**")
        if not df_pagamentos.empty:
            st.dataframe(df_pagamentos, use_container_width=True)
        else:
            st.write("Nenhum pagamento encontrado no período selecionado.")


elif menu == "Relatório Mensal":
    st.header("Relatório Mensal")
    data_inicio = st.date_input("Data de Início")
    data_fim = st.date_input("Data de Fim")
    if data_inicio > data_fim:
        st.error("A data de início não pode ser posterior à data de fim.")
    elif st.button("Gerar Relatório"):
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT data, valor, descricao, categoria
        FROM despesas_condominio
        WHERE date(data) BETWEEN date(?) AND date(?)
        ORDER BY data
        """, (data_inicio.isoformat(), data_fim.isoformat()))
        despesas = cursor.fetchall()

        cursor.execute("""
        SELECT apartamento, SUM(valor) AS total_pago
        FROM pagamentos
        WHERE date(data) BETWEEN date(?) AND date(?)
        GROUP BY apartamento
        ORDER BY apartamento
        """, (data_inicio.isoformat(), data_fim.isoformat()))
        pagamentos = cursor.fetchall()

        conn.close()

        df_despesas = pd.DataFrame(despesas, columns=["Data", "Valor (R$)", "Descrição", "Categoria"])
        df_pagamentos = pd.DataFrame(pagamentos, columns=["Apartamento", "Total Pago (R$)"])

        st.write("**Despesas no Período**")
        st.dataframe(df_despesas)

        st.write("**Pagamentos no Período**")
        st.dataframe(df_pagamentos)

elif menu == "Relatório de Inadimplência":
    st.header("Relatório de Inadimplência")

    if st.button("Gerar Relatório de Inadimplência"):
        df_inadimplencia = gerar_relatorio_inadimplencia()

        # Mostrar o relatório no Streamlit
        st.write("**Relatório de Inadimplência**")
        st.dataframe(df_inadimplencia)

        # Resumo
        total_saldo_devedor = df_inadimplencia["Saldo Devedor (R$)"].sum()
        st.write(f"**Total de Saldo Devedor: R$ {total_saldo_devedor:.2f}**")


elif menu == "Relatório Anual":
    st.header("Relatório Anual por Apartamento")
    data_inicio = st.date_input("Data de Início", value=pd.to_datetime("2024-01-01"))
    data_fim = st.date_input("Data de Fim", value=pd.to_datetime("2024-12-31"))
    mes_atual = datetime.now().month
    if data_inicio > data_fim:
        st.error("A data de início não pode ser posterior à data de fim.")
    elif st.button("Gerar Relatório Anual"):
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT apartamento, strftime('%m', data) AS mes, SUM(valor) AS total_pago
        FROM pagamentos
        WHERE date(data) BETWEEN date(?) AND date(?)
        GROUP BY apartamento, mes
        ORDER BY apartamento, mes
        """, (data_inicio.isoformat(), data_fim.isoformat()))
        pagamentos = cursor.fetchall()

        conn.close()

        # Criar estrutura para os apartamentos e pagamentos por mês
        apartamentos = [str(num) for num in range(101, 105)] + [str(num) for num in range(201, 205)] + [str(num) for num in range(301, 305)]
        meses = [f"Mês {i:02}" for i in range(1, 13)]

        data = []
        for apartamento in apartamentos:
            linha = [apartamento]
            total_pago = 0
            total_esperado = 50 * mes_atual  # Valor mensal apenas até o mês atual
            for mes in range(1, 13):
                valor_pago = sum([p[2] for p in pagamentos if p[0] == apartamento and int(p[1]) == mes])
                linha.append(valor_pago)
                if mes <= mes_atual:
                    total_pago += valor_pago
            saldo_devedor = total_esperado - total_pago if total_esperado > total_pago else 0
            linha.append(total_pago)
            linha.append(total_esperado)
            linha.append(saldo_devedor)
            data.append(linha)

        colunas = ["Apartamento"] + meses + ["Total Pago (R$)", "Total Esperado (R$)", "Saldo Devedor (R$)"]
        df_relatorio = pd.DataFrame(data, columns=colunas)

        st.write("**Pagamentos Anuais por Apartamento**")
        st.dataframe(df_relatorio)

elif menu == "Conta Corrente":
    st.header("Conta Corrente do Condomínio")
    saldo, total_recebido, total_despesas, total_ajustes = calcular_saldo()

    st.metric("Saldo Atual", f"R$ {saldo:.2f}")
    st.metric("Total Recebido", f"R$ {total_recebido:.2f}")
    st.metric("Total de Despesas", f"R$ {total_despesas:.2f}")
    st.metric("Ajustes Manuais", f"R$ {total_ajustes:.2f}")

    ajuste = st.number_input("Ajustar Saldo Manualmente (R$)", value=0.0, step=0.01)
    if st.button("Ajustar Saldo"):
        ajustar_saldo(ajuste)
        st.success(f"Saldo ajustado com sucesso! Valor do ajuste: R$ {ajuste:.2f}")

elif menu == "Administração":
    st.header("Administração do Sistema")
    if st.button("Apagar e Recriar Banco de Dados"):
        delete_and_recreate_database()
        st.success("Banco de dados apagado e recriado com sucesso!")


elif menu == "Dashboard":
    st.header("Dashboard de Indicadores")

    conn = connect_db()
    cursor = conn.cursor()

    # Total de despesas por categoria
    cursor.execute("SELECT categoria, SUM(valor) FROM despesas_condominio GROUP BY categoria")
    despesas_por_categoria = cursor.fetchall()
    df_despesas_categoria = pd.DataFrame(despesas_por_categoria, columns=["Categoria", "Total (R$)"])

    # Total de pagamentos por apartamento
    cursor.execute("SELECT apartamento, SUM(valor) FROM pagamentos GROUP BY apartamento")
    pagamentos_por_apartamento = cursor.fetchall()
    df_pagamentos_apartamento = pd.DataFrame(pagamentos_por_apartamento, columns=["Apartamento", "Total Pago (R$)"])

    conn.close()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Despesas por Categoria")
        fig = px.pie(df_despesas_categoria, values="Total (R$)", names="Categoria", title="Distribuição de Despesas")
        st.plotly_chart(fig)

    with col2:
        st.subheader("Pagamentos por Apartamento")
        fig = px.bar(df_pagamentos_apartamento, x="Apartamento", y="Total Pago (R$)", title="Pagamentos por Apartamento")
        st.plotly_chart(fig)