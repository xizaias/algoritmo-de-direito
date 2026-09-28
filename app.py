import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="LegalFlow - Otimizador de Rotina", layout="wide")
st.title("⚖️ LegalFlow: Dashboard do Operador de Direito")
st.write("Sistema conectado ao Banco de Dados Nuvem (Google Sheets). Não perde dados!")

# 2. CONEXÃO COM O BANCO DE DADOS (Google Sheets)
conn = st.connection("gsheets", type=GSheetsConnection)

# Função para ler os dados da planilha
def carregar_dados():
    return conn.read(ttl="0") # ttl=0 força o app a buscar dados novos sempre, sem cache

df_base = carregar_dados()

# 3. FORMULÁRIO DE ENTRADA (Input de Dados)
with st.sidebar.form("nova_tarefa"):
    st.header("📋 Cadastrar Demanda")
    proc = st.text_input("Número do Processo / Matéria")
    tarefa = st.text_input("Descrição da Atividade")
    prazo = st.date_input("Prazo de Entrega", min_value=datetime.today())
    comp = st.slider("Complexidade (Esforço de 1 a 5)", 1, 5, 3)
    
    if st.form_submit_button("Agendar e Salvar na Nuvem"):
        if proc and tarefa:
            # Cria a nova linha combinando com o nome das colunas da planilha
            nova_linha = pd.DataFrame([{
                "processo": proc,
                "tarefa": tarefa,
                "prazo": str(prazo),
                "complexidade": int(comp)
            }])
            
            # Junta o dado novo com os dados antigos que já estavam na planilha
            df_atualizado = pd.concat([df_base, nova_linha], ignore_index=True)
            
            # ATUALIZA A PLANILHA DO GOOGLE NA NUVEM! (Persistência Real)
            conn.update(data=df_atualizado)
            
            st.success("Dado salvo no Banco de Dados com sucesso!")
            st.rerun()
        else:
            st.warning("Por favor, preencha todos os campos.")

# 4. O ALGORITMO DE ORDENAÇÃO
if not df_base.empty:
    df = df_base.copy()
    df['prazo'] = pd.to_datetime(df['prazo'])
    df['Dias_Restantes'] = (df['prazo'] - pd.Timestamp.now().normalize()).dt.days
    df['Dias_Restantes'] = df['Dias_Restantes'].apply(lambda x: 0.5 if x <= 0 else x)

    # Cálculo do Score de Prioridade
    df['Score_Prioridade'] = (df['complexidade'] / df['Dias_Restantes']).round(2)
    df_ordenado = df.sort_values(by='Score_Prioridade', ascending=False)

    # Renomear para exibição amigável
    df_exibicao = df_ordenado.rename(columns={
        "processo": "Identificador",
        "tarefa": "Tarefa",
        "prazo": "Data Limite",
        "complexidade": "Esforço (1-5)",
        "Dias_Restantes": "Dias Restantes",
        "Score_Prioridade": "Urgência"
    })

    # 5. VISUALIZAÇÃO DO DASHBOARD
    col1, col2 = st.columns()

    with col1:
        st.subheader("🔥 Fila de Execução Otimizada")
        st.dataframe(
            df_exibicao[['Identificador', 'Tarefa', 'Dias Restantes', 'Esforço (1-5)', 'Urgência']],
            use_container_width=True
        )

    with col2:
        st.subheader("💡 Próxima Ação Crítica")
        tarefa_urgente = df_ordenado.iloc[0]
        st.error(f"**Inicie agora:** {tarefa_urgente['tarefa']}\n\n**Foco no processo:** {tarefa_urgente['processo']}")
        st.metric(label="Fator de Risco de Atraso", value=tarefa_urgente['Score_Prioridade'])
else:
    st.info("Nenhuma tarefa cadastrada no Banco de Dados ainda.")
