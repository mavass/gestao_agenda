import streamlit as st
from contatos import CONTATOS_ALYVIA, CONTATOS_LAUDITE
from autenticar import autenticar_laudite, autenticar_gmail
from visualizar_agenda import buscar_eventos_ocupados,buscar_eventos_ocupados_todos, montar_tabela_agenda, exibir_tabela_agenda, encontrar_horarios_livres_consolidado
from agendamento import buscar_emails_convidados, agendar_reuniao_laudite, agendar_reuniao_gmail
from datetime import timezone, datetime, timedelta
from outlook_ics import buscar_eventos_outlook_ics

ics_url = st.secrets["ics"]["url"]

st.set_page_config(page_title="Secretária Virtual", layout="centered")
st.title("🤖 Secretária Virtual de Reuniões")


# Visualizar Agenda Completa

st.subheader("Visualizar Agenda Completa")
data_inicio = st.date_input("Data inicial", value=datetime.now().date())
data_fim = st.date_input("Data final", value=(datetime.now() + timedelta(days=7)).date())

service_laudite = autenticar_laudite()
service_gmail = autenticar_gmail()
if st.button("Mostrar Agenda"):
    inicio_periodo = datetime.combine(data_inicio, datetime.min.time()).replace(tzinfo=timezone.utc)
    fim_periodo = datetime.combine(data_fim, datetime.max.time()).replace(tzinfo=timezone.utc)

    busy_gmail = buscar_eventos_ocupados(service_gmail, 'primary', inicio_periodo, fim_periodo, email_real='marcelo.vasserman@gmail.com')
    busy_laudite = buscar_eventos_ocupados(service_laudite, 'primary', inicio_periodo, fim_periodo, email_real='marcelo.vasserman@laudite.com.br') # aqui 'primary' é da conta Laudte!
    busy_slots = busy_gmail + busy_laudite
    if ics_url:
        try:
            busy_outlook = buscar_eventos_outlook_ics(ics_url, inicio_periodo, fim_periodo)
            busy_slots += busy_outlook
        except Exception as e:
            st.warning(f"Não foi possível carregar agenda Outlook (ICS): {e}")


    tabela = montar_tabela_agenda(busy_slots, data_inicio, data_fim)
    exibir_tabela_agenda(tabela, st)


st.subheader("Visualizar Horários Livres")
data_inicio_2 = st.date_input("Data inicial 2", value=datetime.now().date())
data_fim_2 = st.date_input("Data final 2", value=(datetime.now() + timedelta(days=7)).date())


# Mostrar horários livres

if st.button("Mostrar horários livres"):
    inicio_periodo = datetime.combine(data_inicio_2, datetime.min.time()).replace(tzinfo=timezone.utc)
    fim_periodo = datetime.combine(data_fim_2, datetime.max.time()).replace(tzinfo=timezone.utc)

    busy_gmail = buscar_eventos_ocupados_todos(service_gmail, inicio_periodo, fim_periodo, email_real='marcelo.vasserman@gmail.com')
    busy_laudite = buscar_eventos_ocupados_todos(service_laudite, inicio_periodo, fim_periodo, email_real='marcelo.vasserman@laudite.com.br') # aqui 'primary' é da conta Laudte!
    busy_slots = busy_gmail + busy_laudite
    if ics_url:
        try:
            busy_outlook = buscar_eventos_outlook_ics(ics_url, inicio_periodo, fim_periodo)
            busy_slots += busy_outlook
        except Exception as e:
            st.warning(f"Não foi possível carregar agenda Outlook (ICS): {e}")



    df_livres = encontrar_horarios_livres_consolidado(busy_slots, data_inicio_2, data_fim_2, intervalo_min=30)
    if df_livres.empty:
        st.info("Nenhum horário livre encontrado nesse período.")
    else:
        st.write(df_livres.to_html(escape=False, index=False), unsafe_allow_html=True)

st.subheader("Agendar Reunião")
# Inputs
agenda = st.radio("Escolha a agenda:", ["gmail", "laudite"])
data_inicio = st.date_input("Data de início")
hora_inicio = st.time_input("Hora de início")

# Duracao em incrementos de 15 min, até 3h (180 min)
opcoes_duracao = list(range(15, 195, 15))
duracao = st.selectbox("Duração (minutos):", opcoes_duracao, index=1)  # default 30min

nome_reuniao = st.text_input("Nome da reunião")
descricao = st.text_area("Descrição (opcional)")

# Busca nomes possíveis do dicionário correto
from contatos import CONTATOS_LAUDITE, CONTATOS_ALYVIA
contatos_dict = CONTATOS_LAUDITE if agenda == "laudite" else CONTATOS_ALYVIA
nomes_convidados = st.multiselect("Convidados:", options=list(contatos_dict.keys()))

if st.button("Agendar Reunião"):
    from datetime import datetime, timedelta
    emails_convidados = buscar_emails_convidados(nomes_convidados, agenda)
    if "fred@fireflies.ai" not in emails_convidados:
        emails_convidados.append("fred@fireflies.ai")

    dt_inicio = datetime.combine(data_inicio, hora_inicio)
    dt_fim = dt_inicio + timedelta(minutes=duracao)
    dt_inicio_str = dt_inicio.strftime("%Y-%m-%dT%H:%M:%S")
    dt_fim_str = dt_fim.strftime("%Y-%m-%dT%H:%M:%S")

    if agenda == "laudite":
        link = agendar_reuniao_laudite(dt_inicio_str, dt_fim_str, nome_reuniao, descricao, emails_convidados,meet_link=True)
        st.success("Evento criado na agenda Laudite!")
        if link:
            st.markdown(f"[Abrir no Google Calendar]({link})")
    else:
        link_evento = agendar_reuniao_gmail(dt_inicio_str, dt_fim_str, nome_reuniao, descricao, emails_convidados,meet_link=True)
        st.success("Evento criado na agenda Gmail!")
        if link_evento:
            st.markdown(f"[Abrir no Google Calendar]({link_evento})")





