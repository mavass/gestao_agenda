import requests
from ics import Calendar
from dateutil import tz
from typing import List, Tuple
from datetime import datetime

def buscar_eventos_outlook_ics(
    ics_url: str,
    inicio: datetime,
    fim: datetime,
    tzname: str = "America/Sao_Paulo",
) -> List[Tuple[datetime, datetime, str, str]]:
    # Normaliza webcal://
    if ics_url.lower().startswith("webcal://"):
        ics_url = "https://" + ics_url[len("webcal://"):]

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/123.0 Safari/537.36"
        )
    }
    resp = requests.get(ics_url, headers=headers, timeout=15, allow_redirects=True)
    if resp.status_code in (401, 403):
        raise PermissionError(
            f"ICS não acessível (HTTP {resp.status_code}). "
            "Verifique se o link está público ou se requer autenticação."
        )
    resp.raise_for_status()

    text = resp.text if resp.encoding else resp.content.decode("utf-8", "ignore")
    if "BEGIN:VCALENDAR" not in text:
        raise ValueError("Conteúdo recebido não é um arquivo ICS válido.")

    cal = Calendar(text)
    tz_sp = tz.gettz(tzname)

    def to_sp(arrow_dt):
        """Converte Arrow/datetime para datetime em America/Sao_Paulo sem deslocar naive."""
        dt = getattr(arrow_dt, "datetime", arrow_dt)  # Arrow -> datetime
        if dt.tzinfo is None:
            # Horário sem tz: considerar que já está NO fuso local do calendário
            return dt.replace(tzinfo=tz_sp)
        else:
            return dt.astimezone(tz_sp)

    # Tenta expandir ocorrências (se houver)
    try:
        ocorrencias = list(cal.timeline.between(inicio, fim))
    except Exception:
        try:
            ocorrencias = list(cal.timeline.included(inicio, fim))
        except Exception:
            ocorrencias = [e for e in getattr(cal, "events", []) if getattr(e, "begin", None) and getattr(e, "end", None)]

    busy = []
    for ev in ocorrencias:
        if not getattr(ev, "begin", None) or not getattr(ev, "end", None):
            continue
        start = to_sp(ev.begin)
        end = to_sp(ev.end)

        # Interseção inclusiva com a janela pedida
        if not (end <= inicio or start >= fim):
            resumo = (getattr(ev, "name", None) or "Ocupado").strip()
            busy.append((start, end, resumo, "marcelo.vasserman@arlequim.com"))

    return busy
