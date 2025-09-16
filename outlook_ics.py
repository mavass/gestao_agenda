# outlook_ics.py
import requests
from ics import Calendar
from dateutil import tz

def buscar_eventos_outlook_ics(ics_url, inicio, fim, tzname="America/Sao_Paulo"):
    """
    Lê um calendário ICS remoto e retorna eventos no mesmo formato (ini, fim, resumo, id).
    - inicio/fim: datetime com tzinfo
    """
    resp = requests.get(ics_url)
    resp.raise_for_status()
    cal = Calendar(resp.text)

    tz_sp = tz.gettz(tzname)
    busy = []
    for ev in cal.events:
        if not ev.begin or not ev.end:
            continue
        # Agora ev.begin e ev.end já são datetimes
        start = ev.begin.astimezone(tz_sp)
        end   = ev.end.astimezone(tz_sp)

        if start < fim and end > inicio:
            resumo = ev.name or "Ocupado"
            busy.append((start, end, resumo, "marcelo.vasserman@arlequim.com"))
    return busy
