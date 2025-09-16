from contatos import CONTATOS_ALYVIA, CONTATOS_LAUDITE
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from datetime import datetime, timedelta
from autenticar import autenticar_laudite
from uuid import uuid4

import os

def autenticar_gmail():
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    creds = None
    if os.path.exists('token_gmail.json'):
        creds = Credentials.from_authorized_user_file('token_gmail.json', SCOPES)
    if not creds or not creds.valid:
        # Aqui, se não tiver token, deve rodar OAuth localmente para gerar o token.json
        raise Exception("Token OAuth do Gmail não encontrado ou inválido.")
    return build('calendar', 'v3', credentials=creds)


def agendar_reuniao_gmail(dt_inicio_str, dt_fim_str, titulo, descricao, convidados, meet_link=False):
    service = autenticar_gmail()
    calendar_id = 'primary'

    dt_inicio = datetime.strptime(dt_inicio_str, "%Y-%m-%dT%H:%M:%S")
    dt_fim = datetime.strptime(dt_fim_str, "%Y-%m-%dT%H:%M:%S")

    evento = {
        'summary': titulo,
        'description': descricao or "",
        'start': {'dateTime': dt_inicio.isoformat(), 'timeZone': 'America/Sao_Paulo'},
        'end': {'dateTime': dt_fim.isoformat(), 'timeZone': 'America/Sao_Paulo'},
        'attendees': [{'email': e} for e in (convidados or [])],
    }

    if meet_link:
        evento['conferenceData'] = {
            'createRequest': {
                'conferenceSolutionKey': {'type': 'hangoutsMeet'},
                'requestId': f"req-{uuid4().hex}"
            }
        }

    evento_criado = service.events().insert(
        calendarId=calendar_id,
        body=evento,
        sendUpdates='all',
        conferenceDataVersion=1
    ).execute()

    return evento_criado.get('htmlLink')


def buscar_emails_convidados(nomes, agenda):
    contatos = CONTATOS_LAUDITE if agenda == "laudite" else CONTATOS_ALYVIA
    emails = []
    for nome in nomes:
        emails += contatos.get(nome, [])
    return emails


def criar_evento(data_inicio, duracao_min, titulo, descricao=None, convidados=None, meet_link=True):
    from autenticar import autenticar_laudite
    service = autenticar_laudite()
    calendar_id = 'primary'

    dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%dT%H:%M:%S')
    dt_fim = dt_inicio + timedelta(minutes=duracao_min)

    evento = {
        'summary': titulo,
        'description': descricao or "",
        'start': {'dateTime': dt_inicio.isoformat(), 'timeZone': 'America/Sao_Paulo'},
        'end': {'dateTime': dt_fim.isoformat(), 'timeZone': 'America/Sao_Paulo'},
        'attendees': [{'email': e} for e in (convidados or [])],
    }

    if meet_link:
        evento['conferenceData'] = {
            'createRequest': {
                'conferenceSolutionKey': {'type': 'hangoutsMeet'},
                'requestId': f"req-{uuid4().hex}"
            }
        }

    evento_criado = service.events().insert(
        calendarId=calendar_id,
        body=evento,
        sendUpdates='all',
        conferenceDataVersion=1
    ).execute()

    return evento_criado.get('htmlLink')

def agendar_reuniao_laudite(dt_inicio_str, dt_fim_str, titulo, descricao, convidados, meet_link=True):
    dt_inicio = datetime.strptime(dt_inicio_str, "%Y-%m-%dT%H:%M:%S")
    dt_fim = datetime.strptime(dt_fim_str, "%Y-%m-%dT%H:%M:%S")
    duracao = int((dt_fim - dt_inicio).total_seconds() // 60)

    return criar_evento(
        data_inicio=dt_inicio_str,
        duracao_min=duracao,
        titulo=titulo,
        descricao=descricao,
        convidados=convidados,
        meet_link=meet_link
    )


def gerar_url_gmail(dt_inicio_str, dt_fim_str, titulo, descricao, convidados):
    # Converte datas para formato Google Calendar
    from datetime import datetime
    ini = datetime.strptime(dt_inicio_str, "%Y-%m-%dT%H:%M:%S")
    fim = datetime.strptime(dt_fim_str, "%Y-%m-%dT%H:%M:%S")
    ini_fmt = ini.strftime('%Y%m%dT%H%M%S')
    fim_fmt = fim.strftime('%Y%m%dT%H%M%S')
    url = (
        f"https://calendar.google.com/calendar/u/0/r/eventedit?"
        f"text={titulo.replace(' ', '+')}"
        f"&dates={ini_fmt}/{fim_fmt}"
        f"&details={descricao}"
        f"&add={','.join(convidados)}"
    )
    return url
