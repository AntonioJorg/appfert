# --- IMPORTS PRINCIPAIS ---
import streamlit as st
import requests
import math
import datetime

# ==============================================================================
# MÓDULO 2: BASE DE CONHECIMENTO (O "Receituário")
# (Copiar exatamente como estava)
# ==============================================================================
receituario_agronomico = {
    "Vegetativo": {
        "ec_ideal_solucao": 2.2,
        "ph_ideal_solucao": 5.8,
        "meta_deficit_pressao_vapor_kpa": 1.0,
        "kc": 0.6
    },
    "Florescimento": {
        "ec_ideal_solucao": 2.4,
        "ph_ideal_solucao": 5.8,
        "meta_deficit_pressao_vapor_kpa": 1.2,
        "kc": 0.8
    },
    "Frutificação Inicial": {
        "ec_ideal_solucao": 2.5,
        "ph_ideal_solucao": 5.8,
        "meta_deficit_pressao_vapor_kpa": 1.2,
        "kc": 1.0
    },
    "Plena Frutificação/Colheita": {
        "ec_ideal_solucao": 2.8,
        "ph_ideal_solucao": 5.8,
        "meta_deficit_pressao_vapor_kpa": 1.3,
        "kc": 1.15
    }
}

# ==============================================================================
# MÓDULO 3: FUNÇÕES DA API DE CLIMA
# (Copiar exatamente como estava - V4 Corrigida)
# ==============================================================================
def get_lat_long(cidade, estado):
    try:
        url_geocoding = f"https://geocoding-api.open-meteo.com/v1/search"
        params = {"name": cidade, "admin1": estado, "count": 1, "language": "pt", "format": "json"}
        response = requests.get(url_geocoding, params=params)
        response.raise_for_status() 
        data = response.json()
        if "results" in data and len(data["results"]) > 0:
            result = data["results"][0]
            return result["latitude"], result["longitude"], result.get("name", cidade)
        else:
            st.error(f"Erro: Cidade '{cidade}, {estado}' não encontrada.")
            return None, None, None
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao conectar à API de geocoding: {e}")
        return None, None, None

def get_previsao_clima(lat, long):
    if lat is None or long is None: return None
    try:
        url_forecast = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": long,
            "daily": "shortwave_radiation_sum,temperature_2m_max,temperature_2m_min",
            "timezone": "auto",
            "forecast_days": 1
        }
        response = requests.get(url_forecast, params=params)
        response.raise_for_status()
        data = response.json()
        if "daily" in data:
            return {
                "solar_radiation_sum": data["daily"]["shortwave_radiation_sum"][0], 
                "temp_max_externa": data["daily"]["temperature_2m_max"][0],
                "temp_min_externa": data["daily"]["temperature_2m_min"][0]
            }
        else:
            st.error("Erro: Resposta da API de clima não contém dados 'daily'.")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao conectar à API de clima: {e}")
        return None

# ==============================================================================
# MÓDULO 4: FUNÇÕES DO "CÉREBRO" (Cálculos)
# (Copiar exatamente como estava)
# ==============================================================================
TRANSMISSIVIDADE_ESTUFA = 0.70
DENSIDADE_PLANTAS = 3.0
FATOR_CONVERSAO_RADIACAO_ETO = 0.408
FRACAO_LIXIVIACAO = 1.20

def calcular_dvp(temperatura, umidade_relativa):
    if umidade_relativa <= 0 or umidade_relativa > 100: return 0.0
    pvs = 0.6108 * math.exp((17.27 * temperatura) / (temperatura + 237.3))
    pva = pvs * (umidade_relativa / 100.0)
    dvp = pvs - pva
    return dvp

def calcular_volume_irrigacao(radiacao_solar_externa_mj, kc):
    radiacao_interna = radiacao_solar_externa_mj * TRANSMISSIVIDADE_ESTUFA
    eto_mm_dia = radiacao_interna * FATOR_CONVERSAO_RADIACAO_ETO
    etc_mm_dia = eto_mm_dia * kc
    litros_por_m2 = etc_mm_dia
    litros_por_planta = litros_por_m2 / DENSIDADE_PLANTAS
    volume_total_irrigacao_planta = litros_por_planta * FRACAO_LIXIVIACAO
    return volume_total_irrigacao_planta

# ==============================================================================
# MÓDULO DE INTERFACE (Streamlit)
# (Substitui os Módulos 1, 5 e 6)
# ==============================================================================

# --- Configuração da Página ---
st.set_page_config(
    page_title="Cérebro Fertirrigação V1.2",
    page_icon="🧠",
    layout="wide"
)

# --- LÓGICA DE CAPTURA DE LEAD (O "PORTÃO") ---
if 'lead_captured' not in st.session_state:
    st.session_state.lead_captured = False

if not st.session_state.lead_captured:
    st.title("Bem-vindo ao 🧠 Cérebro V1.2")
    st.subheader("Seu Concierge Pessoal de Fertirrigação")
    st.markdown("""
    Para acessar a ferramenta de recomendação, por favor, insira seus dados. 
    Prometemos não enviar spam, apenas informações relevantes sobre o projeto!
    """)
    
    with st.form(key='lead_form'):
        nome = st.text_input("Seu Nome *")
        email = st.text_input("Seu E-mail *")
        submit_button = st.form_submit_button(label='Acessar Ferramenta')

        if submit_button:
            if not nome or not email:
                st.error("Por favor, preencha todos os campos obrigatórios.")
            else:
                # --- PRÓXIMO PASSO (V1.3): Salvar o Lead ---
                # Aqui você adicionaria o código para salvar o (nome, email)
                # em um Google Sheet ou banco de dados.
                # Por enquanto, apenas "desbloqueamos" o app.
                st.session_state.lead_captured = True
                st.session_state.user_name = nome
                st.rerun() # Recarrega a página no modo "logado"

# --- O APLICATIVO PRINCIPAL (Se o lead foi capturado) ---
else:
    st.title(f"🧠 Cérebro V1.2: Concierge")
    st.markdown(f"**Olá, {st.session_state.user_name}!** Pronto para a recomendação do dia.")
    
    # --- MÓDULO 1: Inputs (agora na Barra Lateral) ---
    st.sidebar.header("Módulo 1: Dados do Cliente")
    in_cidade = st.sidebar.text_input('Cidade:', value='Pitimbu')
    in_estado = st.sidebar.text_input('Estado (Sigla):', value='PB')
    in_estagio = st.sidebar.selectbox(
        'Estágio Fenológico:',
        options=list(receituario_agronomico.keys()),
        index=1 # Padrão "Florescimento"
    )
    in_temp_max_int = st.sidebar.number_input('Temp. Máx. Interna (24h):', value=30.0, format="%.1f")
    in_temp_min_int = st.sidebar.number_input('Temp. Mín. Interna (24h):', value=20.0, format="%.1f")
    in_umidade_media_int = st.sidebar.number_input('Umidade Média Interna (%):', value=70.0, format="%.1f")
    in_ec_drenado = st.sidebar.number_input('EC da Solução Drenada (mS/cm):', value=2.8, format="%.1f")
    
    st.divider()

    # --- MÓDULO 5: Recomendação Estratégica (Principal) ---
    st.header("Módulo 5: Recomendação Estratégica (Diária)")
    
    if st.button('Gerar Recomendação (V1.2)', type="primary"):
        with st.spinner("Processando... Buscando dados de clima e rodando o cérebro..."):
            
            # --- Lógica de Geração (copiada do Módulo 5, V1.2) ---
            try:
                # 1. Coleta de API
                lat, long, nome_cidade_api = get_lat_long(in_cidade, in_estado)
                if lat is None: raise Exception("Falha no Geocoding.")
                
                dados_clima = get_previsao_clima(lat, long)
                if dados_clima is None: raise Exception("Falha ao buscar clima.")
                
                radiacao_prevista = dados_clima['solar_radiation_sum']

                # 2. Busca Receituário
                parametros = receituario_agronomico[in_estagio]
                ec_ideal_base = parametros['ec_ideal_solucao']
                ph_ideal = parametros['ph_ideal_solucao']
                dvp_meta = parametros['meta_deficit_pressao_vapor_kpa']
                kc_atual = parametros['kc']

                # 3. Lógica de Água e Frequência
                if radiacao_prevista > 24: recomendacao_agua_freq = "Alta (12-16 pulsos)"
                elif radiacao_prevista < 15: recomendacao_agua_freq = "Baixa (6-8 pulsos)"
                else: recomendacao_agua_freq = "Padrão (8-12 pulsos)"
                
                recomendacao_agua_vol = calcular_volume_irrigacao(radiacao_prevista, kc_atual)
                fracao_lix_base = (FRACAO_LIXIVIACAO - 1) * 100
                nota_lixiviacao = f"(Nota: Volume inclui {fracao_lix_base:.0f}% de lixiviação)"

                # 4. Lógica de Nutrientes (Ajuste Clima + Flush)
                ec_ajuste_clima = 0.0
                if radiacao_prevista > 25:
                    ec_ajuste_clima = -0.2
                    nota_ajuste_clima = f"(EC reduzido em 0.2 devido à alta radiação prevista de {radiacao_prevista} MJ/m²)"
                elif radiacao_prevista < 12:
                    ec_ajuste_clima = 0.2
                    nota_ajuste_clima = f"(EC aumentado em 0.2 devido à baixa radiação prevista de {radiacao_prevista} MJ/m²)"
                else:
                    nota_ajuste_clima = "(EC padrão para esta radiação)"
                
                ec_ideal_ajustado = ec_ideal_base + ec_ajuste_clima
                delta_ec = in_ec_drenado - ec_ideal_ajustado
                
                if delta_ec > 0.5:
                    fator_flush = 1.15 
                    recomendacao_agua_vol *= fator_flush
                    acao_nutrientes = (f"**ATENÇÃO:** Risco de salinidade. O EC do dreno ({in_ec_drenado:.1f} mS/cm) está alto.\n"
                                       f"   - O volume de água já foi aumentado em 15% para lixiviar (lavar) o substrato.\n" 
                                       f"   - Reduzir o EC da solução nutritiva para {ec_ideal_ajustado - 0.2:.1f} mS/cm temporariamente.")
                    nota_lixiviacao = f"*(Nota: Volume inclui {fracao_lix_base:.0f}% de lixiviação + 15% de 'flush' para lavagem de sais.)*"
                elif delta_ec < -0.5:
                    acao_nutrientes = (f"**INFO:** A planta está absorvendo nutrientes ativamente. O EC do dreno ({in_ec_drenado:.1f} mS/cm) está baixo.\n"
                                       f"   - Aumentar o EC da solução nutritiva para {ec_ideal_ajustado + 0.2:.1f} mS/cm.")
                else:
                    acao_nutrientes = (f"**OK:** O EC do dreno ({in_ec_drenado:.1f} mS/cm) está próximo da meta.\n"
                                       f"   - Manter o EC da solução nutritiva em {ec_ideal_ajustado:.1f} mS/cm.")

                # 5. Lógica de Ambiente (DVP)
                temp_media_int = (in_temp_max_int + in_temp_min_int) / 2.0
                dvp_calculado = calcular_dvp(temp_media_int, in_umidade_media_int)
                alerta_ambiente_str = ""
                
                if dvp_calculado > (dvp_meta + 0.3): 
                    alerta_ambiente_str = f"   - **[ALERTA DE ESTRESSE]**\n"
                    acao_ambiente = (f"O DVP calculado ({dvp_calculado:.2f} kPa) está acima da meta ({dvp_meta} kPa).\n"
                                     f"   - O ar está seco, aumentando o risco de estresse hídrico e deficiência de Cálcio (fundo-preto).\n"
                                     f"   - **AÇÃO:** Aumentar a FREQUÊNCIA dos pulsos (conforme sugerido) para manter o substrato úmido.\n"
                                     f"   - Se disponível, acionar nebulização/sombreamento.")
                    recomendacao_agua_freq = f"{recomendacao_agua_freq} (AUMENTADA DEVIDO AO DVP ALTO)"
                elif dvp_calculado < (dvp_meta - 0.4):
                    alerta_ambiente_str = f"   - **[ALERTA DE UMIDADE]**\n"
                    acao_ambiente = (f"O DVP calculado ({dvp_calculado:.2f} kPa) está muito baixo ({dvp_meta} kPa).\n"
                                     f"   - O ar está muito úmido, reduzindo a transpiração e o risco de doenças fúngicas.\n"
                                     f"   - **AÇÃO:** Aumentar a ventilação da estufa (abrir janelas/ventoinhas) para renovar o ar.")
                else:
                    acao_ambiente = f"**OK:** O DVP calculado ({dvp_calculado:.2f} kPa) está dentro da faixa ideal (Meta: {dvp_meta} kPa)."

                # --- SUCESSO: Exibe o Output ---
                data_hoje = datetime.date.today().strftime("%d/%m/%Y")
                st.markdown(f"## --- RECOMENDAÇÃO DE FERTIRRIGAÇÃO ({data_hoje}) ---")
                st.markdown(f"**Cultura:** Tomate Grape (Estágio: {in_estagio})\n**Local:** {nome_cidade_api}, {in_estado}")
                
                st.subheader("1. GESTÃO DE ÁGUA")
                st.markdown(f"*(Baseado em previsão de {radiacao_prevista:.2f} MJ/m² de radiação)*")
                st.markdown(f"**Volume Total por Planta:** `{recomendacao_agua_vol:.2f} Litros/planta/dia`")
                st.markdown(f"**Sugestão de Frequência:** `{recomendacao_agua_freq}`")
                st.caption(nota_lixiviacao)
                
                st.subheader("2. GESTÃO DE NUTRIENTES")
                st.markdown(f"**Meta de EC Base (Estágio):** `{ec_ideal_base} mS/cm`")
                st.markdown(f"**Meta de EC Ajustada (Clima):** `{ec_ideal_ajustado:.1f} mS/cm`")
                st.caption(nota_ajuste_clima)
                st.markdown(f"**Meta de pH da Solução:** `{ph_ideal}`")
                st.markdown(f"**AÇÃO:**\n {acao_nutrientes}")

                st.subheader("3. ANÁLISE DE AMBIENTE (INTERNO)")
                st.markdown(alerta_ambiente_str + "   - " + acao_ambiente)

            except Exception as e:
                st.error(f"Ocorreu um erro ao gerar a recomendação: {e}")
                st.error("Verifique os dados de entrada e a conexão com a API.")

    st.divider()

    # --- MÓDULO 6: Check-Point Tático (em um Expander) ---
    with st.expander("Módulo 6: Check-Point de Meio-Dia (Manejo Tático)"):
        
        st.markdown("Use esta seção para uma análise rápida (ex: 13h) e ações imediatas.")
        
        # Inputs do Módulo 6
        check_estagio = st.selectbox(
            'Estágio Fenológico (Check):',
            options=list(receituario_agronomico.keys()),
            index=1,
            key="check_estagio" # 'key' é importante para diferenciar de outros widgets
        )
        check_temp_atual = st.number_input('Temp. Interna (AGORA):', value=32.0, format="%.1f")
        check_umidade_atual = st.number_input('Umidade Interna (AGORA %):', value=60.0, format="%.1f")
        check_ec_aplicado = st.number_input('EC da Solução (APLICADA):', value=2.4, format="%.1f")
        check_ec_dreno_atual = st.number_input('EC da Solução (DRENADA AGORA):', value=3.0, format="%.1f")

        if st.button("Analisar Check-Point"):
            with st.spinner("Analisando dados táticos..."):
                
                # --- Lógica de Geração (copiada do Módulo 6) ---
                parametros_check = receituario_agronomico[check_estagio]
                dvp_meta_check = parametros_check['meta_deficit_pressao_vapor_kpa']
                
                DVP_CRITICO = 1.8 
                dvp_atual = calcular_dvp(check_temp_atual, check_umidade_atual)
                alerta_ambiente_tatico_str = ""

                if dvp_atual > DVP_CRITICO:
                    alerta_ambiente_tatico_str = "**[ALERTA DE ESTRESSE AGUDO]**"
                    acao_ambiente_tatico = (f"O DVP atual ({dvp_atual:.2f} kPa) está acima do limite crítico ({DVP_CRITICO} kPa).\n"
                                            f"   - A planta está em forte estresse hídrico (risco de 'fundo-preto').\n"
                                            f"   - **AÇÃO IMEDIATA:** Aumentar a FREQUÊNCIA dos pulsos de irrigação (ex: de 60 para 40 min).\n"
                                            f"   - Se disponível, acionar nebulização/sombreamento AGORA.")
                elif dvp_atual > (dvp_meta_check + 0.4):
                    alerta_ambiente_tatico_str = "**[ATENÇÃO: Estresse Elevado]**"
                    acao_ambiente_tatico = (f"O DVP atual ({dvp_atual:.2f} kPa) está elevado (Meta: {dvp_meta_check} kPa).\n"
                                            f"   - Aumentar a frequência dos pulsos de irrigação para o restante da tarde.")
                else:
                    acao_ambiente_tatico = f"**OK:** O DVP atual ({dvp_atual:.2f} kPa) está dentro da faixa ideal."
                
                delta_ec_tatico = check_ec_dreno_atual - check_ec_aplicado
                DELTA_EC_CRITICO = 1.0
                alerta_nutricao_tatico_str = ""

                if delta_ec_tatico > DELTA_EC_CRITICO:
                    alerta_nutricao_tatico_str = "**[ALERTA DE ACÚMULO SALINO]**"
                    acao_nutricao_tatico = (f"O EC do dreno ({check_ec_dreno_atual:.1f} mS/cm) está muito acima do EC aplicado ({check_ec_aplicado:.1f} mS/cm).\n"
                                            f"   - Isso indica que a planta não está conseguindo absorver a solução, e os sais estão concentrando rápido.\n"
                                            f"   - **AÇÃO IMEDIATA:** Realizar 1-2 pulsos de irrigação com EC 50% mais baixo (ou água pura) para lavar o substrato.")
                elif delta_ec_tatico < 0.2:
                    alerta_nutricao_tatico_str = "**[INFO: CONSUMO ALTO]**"
                    acao_nutricao_tatico = (f"O EC do dreno ({check_ec_dreno_atual:.1f} mS/cm) está muito próximo (ou abaixo) do EC aplicado ({check_ec_aplicado:.1f} mS/cm).\n"
                                            f"   - A planta está consumindo nutrientes mais rápido do que a aplicação.\n"
                                            f"   - **AÇÃO:** Considerar aumentar o EC da solução no próximo preparo de tanque.")
                else:
                    acao_nutricao_tatico = f"**OK:** O EC do dreno ({check_ec_dreno_atual:.1f} mS/cm) está com um diferencial saudável em relação ao aplicado ({check_ec_aplicado:.1f} mS/cm)."

                # --- Exibe o Output Tático ---
                data_check = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                st.markdown(f"### --- CHECK-POINT DE MANEJO ({data_check}) ---")
                
                st.subheader("1. ANÁLISE DE AMBIENTE (TEMPO REAL)")
                if alerta_ambiente_tatico_str: st.markdown(alerta_ambiente_tatico_str)
                st.markdown(acao_ambiente_tatico)
                
                st.subheader("2. ANÁLISE DE NUTRIÇÃO (TEMPO REAL)")
                if alerta_nutricao_tatico_str: st.markdown(alerta_nutricao_tatico_str)
                st.markdown(acao_nutricao_tatico)
# --- COLE ESTE CÓDIGO NO FINAL DO SEU 'app.py' ---
# (Ainda dentro do 'else' principal, após o 'expander' do Módulo 6)

    st.divider()

    # --- MÓDULO 9: Detetive de Sintomas ---
    with st.expander("Módulo 9: Detetive de Sintomas 🕵️"):
        
        st.markdown("""
        Selecione os sintomas que você está vendo na sua planta para um
        possível diagnóstico focado em nutrição e ambiente.
        """)
        
        # --- Base de Conhecimento de Diagnóstico ---
        # (Um sistema especialista simples em forma de dicionário)
        diagnostico_db = {
            "Frutos": {
                "Mancha escura/aquosa no fundo (oposto ao caule)": {
                    "diagnostico": "Deficiência de Cálcio (Fisiológica) - 'Fundo-Preto' (Blossom-End Rot)",
                    "causa_provavel": (
                        "Este é um problema clássico de **transporte de Cálcio**, não de falta dele na solução.\n\n"
                        "Causas Comuns:\n"
                        "1. **Estresse Hídrico (DVP Alto):** O ar está muito seco (DVP > 1.5 kPa). A planta transpira muito rápido, e o 'puxão' de água é tão forte que ela não consegue levar o Cálcio (que é um nutriente 'preguiçoso') até a ponta do fruto.\n"
                        "2. **Acúmulo de Sais (EC do Dreno Alto):** O EC do substrato está muito alto (ex: > 3.5 mS/cm). O excesso de outros sais (K, Mg) compete com o Cálcio e 'bloqueia' sua absorção pela raiz."
                    ),
                    "acao_recomendada": (
                        "**AÇÃO IMEDIATA:**\n"
                        "1. Use o **Módulo 6** para checar o DVP e o EC do dreno *agora*.\n"
                        "2. Se o DVP estiver alto, aumente a **FREQUÊNCIA** dos pulsos de irrigação para manter o substrato sempre úmido.\n"
                        "3. Se o EC do dreno estiver alto, realize um **FLUSH** (conforme Módulo 6) para lavar os sais."
                    ),
                    "style": "error" # Mostra como um alerta vermelho
                },
                "Rachaduras (principalmente perto do caule)": {
                    "diagnostico": "Rachaduras por Pressão (Cracking)",
                    "causa_provavel": (
                        "Isso é causado por uma **mudança brusca na absorção de água**.\n\n"
                        "A casca do fruto 'endureceu' durante um período de estresse ou crescimento lento (dias nublados, EC alto), e de repente a planta absorveu muita água (dia de sol forte, ou uma rega muito volumosa após um período seco), 'inflando' o fruto mais rápido do que a casca pode aguentar."
                    ),
                    "acao_recomendada": (
                        "**AÇÃO PREVENTIVA:**\n"
                        "1. Mantenha a irrigação e o EC do substrato o mais **constante** possível (evite 'altos e baixos').\n"
                        "2. Use o **Módulo 5** diariamente para ajustar o volume de água à previsão de radiação, evitando excessos em dias nublados e falta em dias de sol."
                    ),
                    "style": "warning" # Mostra como um alerta amarelo
                }
            },
            "Folhas Novas (Ponteiro)": {
                "Amareladas (nervuras verdes, resto amarelo)": {
                    "diagnostico": "Deficiência de Ferro (Clorose Férrica)",
                    "causa_provavel": (
                        "Geralmente não é falta de Ferro na solução, mas sim um **bloqueio de absorção**.\n\n"
                        "Causa Comum:\n"
                        "1. **pH da Solução Nutritiva Alto:** O pH na zona da raiz está acima de 6.2-6.5. O Ferro (e outros micronutrientes como Manganês) se torna insolúvel e a planta não consegue absorvê-lo."
                    ),
                    "acao_recomendada": (
                        "**AÇÃO IMEDIATA:**\n"
                        "1. Verifique o **pH da sua solução nutritiva** e o **pH do seu dreno**.\n"
                        "2. Certifique-se de que a sua meta de pH (definida no Módulo 5, ex: 5.8) está sendo atingida. Ajuste seu dosador de ácido se necessário."
                    ),
                    "style": "warning"
                },
                "Folhas pequenas, deformadas ou 'queimadas' na ponta": {
                    "diagnostico": "Deficiência de Cálcio (Sistêmico) ou Boro",
                    "causa_provavel": (
                        "Similar ao 'Fundo-Preto' no fruto, isso indica um problema de **transporte de Cálcio** para os pontos de crescimento mais novos (o 'ponteiro').\n\n"
                        "Causa Comum:\n"
                        "1. **DVP Muito Baixo (Umidade Alta):** O ar está muito úmido (DVP < 0.5 kPa). A planta não consegue transpirar, e sem transpiração, não há 'puxão' de água para levar o Cálcio até as folhas novas.\n"
                        "2. **DVP Muito Alto (Estresse):** O estresse é tão grande que o fluxo de água é interrompido."
                    ),
                    "acao_recomendada": (
                        "**AÇÃO IMEDIATA:**\n"
                        "1. Use o **Módulo 6** para checar o DVP.\n"
                        "2. Se o DVP estiver **muito baixo** (muito úmido), aumente a ventilação da estufa (abra janelas/ventoinhas) para forçar a transpiração.\n"
                        "3. Se o DVP estiver **muito alto**, siga as recomendações de aumentar a frequência de rega."
                    ),
                    "style": "error"
                }
            },
            "Folhas Velhas (Baixeiro)": {
                "Amarelamento geral (começa nas pontas e avança)": {
                    "diagnostico": "Deficiência de Nitrogênio (N)",
                    "causa_provavel": (
                        "A planta está 'passando fome' e 'comendo' seus próprios tecidos. O Nitrogênio é um nutriente móvel, então a planta o retira das folhas velhas (menos importantes) para enviar às folhas novas (crescimento).\n\n"
                        "Causa Comum:\n"
                        "1. **EC da Solução Aplicada Muito Baixo:** O EC alvo (definido no Módulo 5) está abaixo da demanda da planta para o estágio atual."
                    ),
                    "acao_recomendada": (
                        "**AÇÃO IMEDIATA:**\n"
                        "1. Verifique o EC da solução que você está aplicando. Ele está de acordo com a meta do **Módulo 5**?\n"
                        "2. Use o **Módulo 6** para checar o Delta de EC. Se o EC do dreno estiver *abaixo* do EC aplicado, é um sinal claro de alto consumo. Aumente o EC da sua solução."
                    ),
                    "style": "warning"
                },
                "Amarelamento entre as nervuras (V invertido)": {
                    "diagnostico": "Deficiência de Magnésio (Mg)",
                    "causa_provavel": (
                        "O Magnésio é o centro da molécula de clorofila. A planta o retira das folhas velhas para as novas.\n\n"
                        "Causa Comum:\n"
                        "1. **EC da Solução Aplicada Muito Baixo** (similar ao Nitrogênio).\n"
                        "2. **Excesso de Potássio (K):** O Potássio (K) compete diretamente com o Magnésio (Mg) pela absorção. Se o EC do seu dreno está muito alto (Módulo 6), o excesso de K pode estar bloqueando o Mg."
                    ),
                    "acao_recomendada": (
                        "**AÇÃO IMEDIATA:**\n"
                        "1. Verifique o EC da solução aplicada (Módulo 5).\n"
                        "2. Verifique se há acúmulo de sais no dreno (Módulo 6). Se o EC do dreno estiver alto, aplique um 'flush' para reequilibrar os nutrientes no substrato."
                    ),
                    "style": "warning"
                }
            }
        }
        
        # --- Lógica do Fluxograma ---
        
        # Pergunta 1: Local do Sintoma
        q1_options = ["---", "Frutos", "Folhas Novas (Ponteiro)", "Folhas Velhas (Baixeiro)"]
        q1 = st.selectbox("1. Onde o sintoma é mais visível?", options=q1_options)
        
        # Pergunta 2: Sintoma Específico
        if q1 in diagnostico_db:
            q2_options = ["---"] + list(diagnostico_db[q1].keys())
            q2 = st.selectbox("2. Qual é o sintoma específico?", options=q2_options)
            
            # Resposta Final: Diagnóstico
            if q2 in diagnostico_db[q1]:
                resultado = diagnostico_db[q1][q2]
                
                st.subheader(f"Possível Diagnóstico: {resultado['diagnostico']}")
                
                # Exibe o diagnóstico com o estilo correto
                if resultado['style'] == 'error':
                    st.error(f"**Causa Provável:**\n{resultado['causa_provavel']}")
                else:
                    st.warning(f"**Causa Provável:**\n{resultado['causa_provavel']}")
                
                st.info(f"**Ação Recomendada (Pelo Cérebro):**\n{resultado['acao_recomendada']}")
