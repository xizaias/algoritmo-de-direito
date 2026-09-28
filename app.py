import streamlit as st
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="LegalFlow - Otimizador de Rotina", layout="wide")
st.title("⚖️ LegalFlow: Dashboard do Operador de Direito")
st.write("Algoritmo de ordenação lógica baseado em criticidade e esforço.")

# 2. BANCO DE DADOS TEMPORÁRIO (Mock)
if "tarefas" not in st.session_state:
    st.session_state.tarefas = pd.DataFrame([
        {"Processo": "00123-2026", "Tarefa": "Contestação Cível", "Prazo": "2026-10-02", "Complexidade": 4},
        {"Processo": "00456-2026", "Tarefa": "Juntar Procuração", "Prazo": "2026-09-30", "Complexidade": 1},
        {"Processo": "00789-2026", "Tarefa": "Recurso Apelação", "Prazo": "2026-10-10", "Complexidade": 5}
    ])

# 3. FORMULÁRIO DE ENTRADA (Input de Dados)
with st.sidebar.form("nova_tarefa"):
    st.header("📋 Cadastrar Demanda")
    proc = st.text_input("Número do Processo")
    tarefa = st.text_input("Descrição da Tarefa")
    prazo = st.date_input("Prazo Fatal", min_value=datetime.today())
    comp = st.slider("Complexidade (Esforço)", 1, 5, 3)
    
    if st.form_submit_button("Agendar"):
        nova_linha = {"Processo": proc, "Tarefa": tarefa, "Prazo": str(prazo), "Complexidade": comp}
        st.session_state.tarefas = pd.concat([st.session_state.tarefas, pd.DataFrame([nova_linha])], ignore_index=True)
        st.rerun()

# 4. O ALGORITMO (Lógica de Ordenação)
df = st.session_state.tarefas.copy()
df['Prazo'] = pd.to_datetime(df['Prazo'])
df['Dias_Restantes'] = (df['Prazo'] - pd.Timestamp.now().normalize()).dt.days

# Regra de negócio: evitar divisão por zero ou números negativos
df['Dias_Restantes'] = df['Dias_Restantes'].apply(lambda x: 0.5 if x <= 0 else x)

# Score de Criticidade (Algoritmo)
# Quanto menor o prazo e maior a complexidade -> Maior o Score
df['Score_Prioridade'] = (df['Complexidade'] / df['Dias_Restantes']).round(2)
df_ordenado = df.sort_values(by='Score_Prioridade', ascending=False)

# 5. VISUALIZAÇÃO (O Dashboard)
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🔥 Fila de Execução Otimizada")
    st.dataframe(
        df_ordenado[['Processo', 'Tarefa', 'Dias_Restantes', 'Complexidade', 'Score_Prioridade']],
        use_container_width=True
    )

with col2:
    st.subheader("💡 Alerta do Algoritmo")
    tarefa_urgente = df_ordenado.iloc[0]
    st.error(f"**Ação Recomendada:** Inicie agora a tarefa **{tarefa_urgente['Tarefa']}** do processo **{tarefa_urgente['Processo']}**.")
    st.metric(label="Fator de Urgência", value=tarefa_urgente['Score_Prioridade'])
