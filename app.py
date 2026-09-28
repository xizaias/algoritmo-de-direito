import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA (Identidade Visual)
st.set_page_config(
    page_title="LegalFlow - Otimizador de Rotina", 
    page_icon="⚖️",
    layout="wide"
)

# Título Principal com estilo limpo
st.title("⚖️ LegalFlow")
st.caption("Painel Inteligente de Otimização de Carga de Trabalho para Operadores de Direito")
st.markdown("---")

# 2. CONEXÃO COM O BANCO DE DADOS (Google Sheets)
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        dados = conn.read(ttl="0")
        if dados is not None and not dados.empty:
            # Garante que todas as colunas fiquem em letras minúsculas para não quebrar o código
            dados.columns = [str(c).strip().lower() for c in dados.columns]
        return dados
    except Exception as e:
        st.error(f"Erro ao conectar com a Planilha do Google: {e}")
        return pd.DataFrame()

df_base = carregar_dados()

# Verificar se as colunas essenciais existem, senão cria uma tabela vazia estruturada
colunas_necessarias = ['processo', 'tarefa', 'prazo', 'complexidade']
if df_base.empty or not all(c in df_base.columns for c in colunas_necessarias):
    df_base = pd.DataFrame(columns=colunas_necessarias)

# 3. BARRA LATERAL - CADASTRO MODERNO
with st.sidebar:
    st.image("https://flaticon.com", width=80)
    st.header("Cadastrar Demanda")
    st.write("Insira os dados para alimentar o algoritmo.")
    
    with st.form("nova_tarefa", clear_on_submit=True):
        proc = st.text_input("Número do Processo ou Disciplina", placeholder="Ex: 00123-2026")
        tarefa = st.text_input("Descrição da Atividade", placeholder="Ex: Protocolar Contestação")
        prazo = st.date_input("Prazo Limite (Fatal)", min_value=datetime.today())
        comp = st.select_slider("Nível de Esforço / Complexidade", options=[1, 2, 3, 4, 5], value=3)
        
        botao_salvar = st.form_submit_button("✨ Agendar e Salvar na Nuvem")
        
        if botao_salvar:
            if proc and tarefa:
                nova_linha = pd.DataFrame([{
                    "processo": proc,
                    "tarefa": tarefa,
                    "prazo": str(prazo),
                    "complexidade": int(comp)
                }])
                df_atualizado = pd.concat([df_base[colunas_necessarias], nova_linha], ignore_index=True)
                conn.update(data=df_atualizado)
                st.success("Salvo com sucesso!")
                st.rerun()
            else:
                st.warning("Preencha todos os campos.")

# 4. PROCESSAMENTO DO ALGORITMO
if not df_base.empty and len(df_base) > 0:
    df = df_base.copy()
    
    # Tratamento e conversão de tipos de dados de segurança
    df['prazo'] = pd.to_datetime(df['prazo'], errors='coerce')
    df['complexidade'] = pd.to_numeric(df['complexidade'], errors='coerce').fillna(3)
    
    # Remove linhas com datas inválidas se houver lixo na planilha
    df = df.dropna(subset=['prazo'])
    
    df['Dias_Restantes'] = (df['prazo'] - pd.Timestamp.now().normalize()).dt.days
    df['Dias_Restantes'] = df['Dias_Restantes'].apply(lambda x: 0.5 if x <= 0 else x)
    df['Score_Prioridade'] = (df['complexidade'] / df['Dias_Restantes']).round(2)
    df_ordenado = df.sort_values(by='Score_Prioridade', ascending=False)

    # Dicionário de tradução e estética das colunas
    df_exibicao = df_ordenado.rename(columns={
        "processo": "Identificador",
        "tarefa": "Tarefa",
        "prazo": "Data Limite",
        "complexidade": "Esforço (1-5)",
        "Dias_Restantes": "Dias Restantes",
        "Score_Prioridade": "Urgência"
    })

    # CARDS DE MÉTRICAS (Visual de Dashboard de Mercado)
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(label="Total de Demandas", value=len(df_base))
    with m2:
        if not df_ordenado.empty:
            tarefa_critica = df_ordenado.iloc[0]['tarefa']
            st.metric(label="🚨 Alerta Crítico", value=f"{str(tarefa_critica)[:18]}...")
        else:
            st.metric(label="🚨 Alerta Crítico", value="Nenhum")
    with m3:
        media_esforco = df_base['complexidade'].mean()
        media_esforco = round(media_esforco, 1) if pd.notna(media_esforco) else 0.0
        st.metric(label="Média de Esforço Geral", value=f"{media_esforco} / 5")

    st.markdown("###")

    # CRIAÇÃO DAS ABAS VIRTUAIS
    aba_fila, aba_graficos = st.tabs(["📋 Fila de Execução Inteligente", "📊 Análise de Produtividade"])

    with aba_fila:
        col_tabela, col_card = st.columns([2, 1])
        
        with col_tabela:
            st.write("O algoritmo ordenou as tarefas abaixo priorizando menor prazo e maior complexidade:")
            st.dataframe(
                df_exibicao[['Identificador', 'Tarefa', 'Data Limite', 'Dias Restantes', 'Esforço (1-5)', 'Urgência']],
                use_container_width=True,
                hide_index=True
            )
            
        with col_card:
            st.info("💡 **Recomendação do Sistema**")
            if not df_ordenado.empty:
                tarefa_urgente = df_ordenado.iloc[0]
                st.error(f"**FOCO TOTAL AGORA:**\n\n**O que fazer:** {tarefa_urgente['tarefa']}\n\n**Onde:** {tarefa_urgente['processo']}")
                st.metric(label="Fator de Risco", value=tarefa_urgente['Score_Prioridade'])

    with aba_graficos:
        st.write("Entenda como a carga de trabalho está distribuída para organizar seu dia:")
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("**Volume de Trabalho por Nível de Esforço**")
            contagem_esforco = df_base['complexidade'].value_counts().sort_index()
            st.bar_chart(contagem_esforco, color="#264653")
            
        with col_g2:
            st.markdown("**Próximos Prazos (Linha do Tempo)**")
            df_datas = df_base.copy()
            df_datas['prazo'] = pd.to_datetime(df_datas['prazo']).dt.strftime('%d/%m')
            contagem_datas = df_datas['prazo'].value_counts().sort_index()
            st.line_chart(contagem_datas, color="#e76f51")
else:
    st.info("👋 Bem-vindo! Cadastre a primeira demanda na barra lateral para ativar o dashboard.")
