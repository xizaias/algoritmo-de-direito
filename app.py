import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import numpy as np
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="LegalFlow - Otimizador de Rotina", page_icon="⚖️", layout="wide")

st.title("⚖️ LegalFlow")
st.caption("Painel Inteligente de Otimização de Carga de Trabalho (Contagem em Dias Úteis - Regra do CPC)")
st.markdown("---")

# 2. CONEXÃO COM O BANCO DE DADOS (Google Sheets)
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        dados = conn.read(ttl="0")
        if dados is not None and not dados.empty:
            dados.columns = [str(c).strip().lower() for c in dados.columns]
        return dados
    except Exception as e:
        st.error(f"Erro ao conectar com a Planilha do Google: {e}")
        return pd.DataFrame()

df_base = carregar_dados()

colunas_necessarias = ['processo', 'tarefa', 'prazo', 'complexidade']
if df_base.empty or not all(c in df_base.columns for c in colunas_necessarias):
    df_base = pd.DataFrame(columns=colunas_necessarias)

# 3. BARRA LATERAL - CADASTRO E BOTÃO DE RESET
with st.sidebar:
    st.image("https://flaticon.com", width=80)
    st.header("Cadastrar Demanda")
    
    with st.form("nova_tarefa", clear_on_submit=True):
        proc = st.text_input("Número do Processo ou Disciplina", placeholder="Ex: 00123-2026")
        tarefa = st.text_input("Descrição da Atividade", placeholder="Ex: Protocolar Contestação")
        prazo = st.date_input("Prazo Limite (Fatal)", min_value=datetime.today())
        comp = st.select_slider("Nível de Esforço / Complexidade", options=[1, 2, 3, 4, 5], value=3)
        
        botao_salvar = st.form_submit_button("✨ Agendar e Salvar na Nuvem")
        
        if botao_salvar:
            if proc and tarefa:
                nova_linha = pd.DataFrame([{"processo": proc, "tarefa": tarefa, "prazo": str(prazo), "complexidade": int(comp)}])
                df_atualizado = pd.concat([df_base[colunas_necessarias], nova_linha], ignore_index=True)
                conn.update(data=df_atualizado)
                st.success("Salvo com sucesso!")
                st.rerun()
            else:
                st.warning("Preencha todos os campos.")
                
    st.markdown("---")
    # Toque extra de segurança: Botão para limpar a tabela caso acumule lixo de testes
    if st.button("🗑️ Limpar Banco de Dados (Testes)"):
        df_limpo = pd.DataFrame(columns=colunas_necessarias)
        conn.update(data=df_limpo)
        st.success("Banco de dados resetado!")
        st.rerun()

# 4. PROCESSAMENTO DO ALGORITMO (DIAS ÚTEIS)
if not df_base.empty and len(df_base) > 0:
    df = df_base.copy()
    df['prazo'] = pd.to_datetime(df['prazo'], errors='coerce')
    df['complexidade'] = pd.to_numeric(df['complexidade'], errors='coerce').fillna(3)
    df = df.dropna(subset=['prazo'])
    
    # 💡 CÁLCULO DE DIAS ÚTEIS (Descontando Sábados e Domingos)
    hoje = datetime.now().date()
    dias_uteis = []
    for p in df['prazo']:
        data_prazo = p.date()
        if data_prazo <= hoje:
            dias_uteis.append(0.5)
        else:
            # Conta os dias úteis entre hoje e a data limite
            qtd = np.busday_count(hoje, data_prazo)
            dias_uteis.append(0.5 if qtd <= 0 else qtd)
            
    df['Dias_Uteis'] = dias_uteis
    df['Score_Prioridade'] = (df['complexidade'] / df['Dias_Uteis']).round(2)
    df_ordenado = df.sort_values(by='Score_Prioridade', ascending=False)

    df_exibicao = df_ordenado.rename(columns={
        "processo": "Identificador", "tarefa": "Tarefa", "prazo": "Data Limite",
        "complexidade": "Esforço (1-5)", "Dias_Uteis": "Dias Úteis Restantes", "Score_Prioridade": "Urgência"
    })

    # METRICAS
    m1, m2, m3 = st.columns(3)
    with m1: st.metric(label="Total de Demandas", value=len(df_base))
    with m2:
        tarefa_critica = df_ordenado.iloc[0]['tarefa'] if not df_ordenado.empty else "Nenhuma"
        st.metric(label="🚨 Alerta Crítico", value=f"{str(tarefa_critica)[:18]}...")
    with m3:
        media_esforco = df_base['complexidade'].mean()
        st.metric(label="Média de Esforço Geral", value=f"{round(media_esforco, 1) if pd.notna(media_esforco) else 0.0} / 5")

    # ABAS
    aba_fila, aba_graficos = st.tabs(["📋 Fila de Execução Inteligente", "📊 Análise de Produtividade"])

    with aba_fila:
        col_tabela, col_card = st.columns([2, 1])
        with col_tabela:
            st.dataframe(df_exibicao[['Identificador', 'Tarefa', 'Data Limite', 'Dias Úteis Restantes', 'Esforço (1-5)', 'Urgência']], use_container_width=True, hide_index=True)
        with col_card:
            st.info("💡 **Recomendação do Algoritmo**")
            tarefa_urgente = df_ordenado.iloc[0]
            st.error(f"**FOCO TOTAL AGORA:**\n\n{tarefa_urgente['tarefa']}\n\n**ID:** {tarefa_urgente['processo']}")

    with aba_graficos:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("**Volume por Esforço**")
            st.bar_chart(df_base['complexidade'].value_counts().sort_index(), color="#264653")
        with col_g2:
            st.markdown("**Próximos Prazos**")
            df_datas = df_base.copy()
            df_datas['prazo'] = pd.to_datetime(df_datas['prazo']).dt.strftime('%d/%m')
            st.line_chart(df_datas['prazo'].value_counts().sort_index(), color="#e76f51")
else:
    st.info("👋 Cadastre a primeira demanda na barra lateral para ativar o algoritmo em dias úteis.")
