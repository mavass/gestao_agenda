from datetime import datetime, timedelta
import pandas as pd
import plotly.figure_factory as ff
import pytz


def buscar_eventos_ocupados(service, calendar_id, inicio, fim, email_real=None):
    """
    Busca eventos ocupados em um calendário Google no período definido.
    - service: objeto Google Calendar autenticado
    - calendar_id: e-mail da agenda
    - inicio, fim: datetime com tzinfo
    """
        
    id_real = email_real if email_real else calendar_id
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=inicio.isoformat(),
        timeMax=fim.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    busy_slots = []
    for event in events_result.get('items', []):
        start = event['start'].get('dateTime')
        end = event['end'].get('dateTime')
        if start and end:
            busy_slots.append((
                datetime.fromisoformat(start),
                datetime.fromisoformat(end),
                event.get('summary', ''),
                id_real
            ))
    return busy_slots



def montar_tabela_agenda(busy_slots, inicio, fim, intervalo_min=15):
    import pandas as pd

    dias = pd.date_range(inicio, fim)
    dias = [d for d in dias if d.weekday() < 5]  # Só dias úteis

    horarios = []
    h = 8 * 60  # minutos
    while h <= 18 * 60:
        hora = h // 60
        minuto = h % 60
        horarios.append(f"{hora:02d}:{minuto:02d}")
        h += intervalo_min

    tabela = pd.DataFrame('', index=horarios, columns=[d.strftime('%d/%m (%a)') for d in dias])

    for evento in busy_slots:
        # Ajusta para 4 campos (ini, fin, resumo, calendar_id)
        if len(evento) == 4:
            ini, fin, resumo, calendar_id = evento
            if calendar_id == 'marcelo.vasserman@gmail.com':
                texto = "(GMAIL) " + (resumo or "Ocupado")
            elif calendar_id == 'marcelo.vasserman@laudite.com.br':
                texto = "(LAUDITE) " + (resumo or "Ocupado")
            elif calendar_id == 'marcelo.vasserman@arlequim.com':
                texto = "(ARLEQUIM) " + (resumo or "Ocupado")                
            else:
                texto = resumo or "Ocupado"
        else:
            ini, fin, resumo = evento
            texto = resumo or "Ocupado"

        dia = ini.date()
        col = dia.strftime('%d/%m (%a)')
        bloco_ini = ini.hour * 60 + ini.minute
        bloco_fim = fin.hour * 60 + fin.minute
        for h in range(8 * 60, 18 * 60 + 1, intervalo_min):
            if bloco_ini <= h < bloco_fim:
                row = f"{h // 60:02d}:{h % 60:02d}"
                if row in tabela.index and col in tabela.columns:
                    if tabela.at[row, col]:
                        # Junta os existentes e o novo, removendo 'Ocupado' se houver mais de um
                        eventos = [e.strip() for e in tabela.at[row, col].split('|')] + [texto]
                        if len(eventos) > 1:
                            eventos = [e for e in eventos if e.lower().replace("(gmail) ", "").replace("(laudite) ", "") != "ocupado"]
                        tabela.at[row, col] = " | ".join(eventos)
                    else:
                        tabela.at[row, col] = texto
    return tabela


def exibir_tabela_agenda(tabela, st):
    tabela_str = tabela.applymap(lambda x: x[0] if isinstance(x, tuple) else x)
    st.dataframe(tabela_str, use_container_width=True, height=500)


def encontrar_horarios_livres_consolidado(busy_slots, inicio, fim, intervalo_min=30):
    from datetime import datetime, timedelta, timezone
    import pandas as pd

    dias_semana_pt = ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo']

    dias = pd.date_range(inicio, fim)
    dias = [d for d in dias if d.weekday() < 5]

    horarios = []
    h = 8 * 60
    while h <= 18 * 60 - intervalo_min:
        hora = h // 60
        minuto = h % 60
        horarios.append((hora, minuto))
        h += intervalo_min

    resultado = {}
    for dia in dias:
        lista_livres = []
        for hora, minuto in horarios:
            ini = datetime.combine(dia, datetime.min.time(), tzinfo=timezone.utc).replace(hour=hora, minute=minuto)
            fin = ini + timedelta(minutes=intervalo_min)
            conflito = False
            for evento in busy_slots:
                ev_ini, ev_fin = evento[:2]
                if ev_ini < fin and ev_fin > ini:
                    conflito = True
                    break
            if not conflito:
                lista_livres.append(f"{ini.strftime('%H:%M')}–{fin.strftime('%H:%M')}")
        if lista_livres:
            resultado[dia] = lista_livres

    linhas = []
    for dia, horarios_livres in resultado.items():
        data_str = dia.strftime('%d/%m/%Y')
        dia_semana = dias_semana_pt[dia.weekday()]
        linhas.append({
            "Data": data_str,
            "Dia da semana": dia_semana,
            "Horários livres": '<br>'.join(horarios_livres)
        })
    return pd.DataFrame(linhas, columns=["Data", "Dia da semana", "Horários livres"])

def encontrar_horarios_livres_consolidado(busy_slots, inicio, fim, intervalo_min=30):
    dias_semana_pt = ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo']

    tz_sp = pytz.timezone('America/Sao_Paulo')

    dias = pd.date_range(inicio, fim)
    dias = [d for d in dias if d.weekday() < 5]

    horarios = []
    h = 8 * 60
    while h <= 18 * 60 - intervalo_min:
        hora = h // 60
        minuto = h % 60
        horarios.append((hora, minuto))
        h += intervalo_min

    resultado = {}
    for dia in dias:
        lista_livres = []
        for hora, minuto in horarios:
            ini_naive = datetime.combine(dia, datetime.min.time()).replace(hour=hora, minute=minuto)
            ini = tz_sp.localize(ini_naive)
            fin = ini + timedelta(minutes=intervalo_min)
            conflito = False
            for evento in busy_slots:
                ev_ini, ev_fin = evento[:2]
                # Converte tudo para o mesmo timezone
                ev_ini = ev_ini.astimezone(tz_sp)
                ev_fin = ev_fin.astimezone(tz_sp)
                if ev_ini < fin and ev_fin > ini:
                    conflito = True
                    break
            if not conflito:
                lista_livres.append(f"{ini.strftime('%H:%M')}–{fin.strftime('%H:%M')}")
        if lista_livres:
            resultado[dia] = lista_livres

    linhas = []
    for dia, horarios_livres in resultado.items():
        data_str = dia.strftime('%d/%m/%Y')
        dia_semana = dias_semana_pt[dia.weekday()]
        linhas.append({
            "Data": data_str,
            "Dia da semana": dia_semana,
            "Horários livres": '<br>'.join(horarios_livres)
        })
    return pd.DataFrame(linhas, columns=["Data", "Dia da semana", "Horários livres"])

def buscar_eventos_ocupados_todos(service, inicio, fim, email_real=None):
    """Busca eventos ocupados em TODOS os calendários do usuário."""
    all_busy_slots = []
    calendars = service.calendarList().list().execute().get('items', [])
    for cal in calendars:
        calendar_id = cal['id']
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=inicio.isoformat(),
            timeMax=fim.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        for event in events_result.get('items', []):
            start = event['start'].get('dateTime')
            end = event['end'].get('dateTime')
            if start and end:
                all_busy_slots.append((
                    datetime.fromisoformat(start),
                    datetime.fromisoformat(end),
                    event.get('summary', ''),
                    email_real or calendar_id
                ))
    return all_busy_slots
