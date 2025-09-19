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
    """
    Lê um calendário ICS remoto e retorna eventos:
    (inicio_dt, fim_dt, resumo, id)
    """
    # Normaliza esquemas "webcal://"
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

    try:
        text = resp.text if resp.encoding else resp.content.decode("utf-8", "ignore")
    except Exception:
        text = resp.content.decode("utf-8", "ignore")

    ctype = (resp.headers.get("Content-Type") or "").lower()
    if "text/calendar" not in ctype and not text.lstrip().startswith("BEGIN:VCALENDAR"):
        raise ValueError(
            "Conteúdo recebido não é um arquivo ICS válido. "
            "Confirme se o link está público e em formato .ics (não página de login)."
        )

    cal = Calendar(text)

    tz_sp = tz.gettz(tzname)
    busy = []
    for ev in getattr(cal, "events", []):
        if not getattr(ev, "begin", None) or not getattr(ev, "end", None):
            continue
        try:
            start = ev.begin.astimezone(tz_sp)
            end = ev.end.astimezone(tz_sp)
        except Exception:
            continue
        if start < fim and end > inicio:
            resumo = (ev.name or "Ocupado").strip()
            busy.append((start, end, resumo, "marcelo.vasserman@arlequim.com"))
    return busy




# --- Diagnóstico ICS (para logs/UI) ---
def diagnostico_ics(ics_url: str) -> dict:
    """
    Faz um GET no ICS e retorna um dicionário com informações de diagnóstico
    sem lançar exceção (ideal para logs e UI).
    """
    info = {"input_url": ics_url}
    try:
        url = ics_url
        if url.lower().startswith("webcal://"):
            url = "https://" + url[len("webcal://"):]
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/123.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        info.update(
            {
                "final_url": getattr(resp, "url", url),
                "status_code": resp.status_code,
                "content_type": (resp.headers.get("Content-Type") or "").lower(),
                "content_length": int(resp.headers.get("Content-Length", "0") or 0),
                "redirected": bool(getattr(resp, "history", [])),
            }
        )
        # tenta obter texto com tolerância
        try:
            text = resp.text if resp.encoding else resp.content.decode("utf-8", "ignore")
        except Exception:
            text = resp.content.decode("utf-8", "ignore")
        snippet = (text or "")[:300]
        info["preview"] = snippet
        info["looks_like_ics"] = snippet.lstrip().startswith("BEGIN:VCALENDAR") or \
            "text/calendar" in info["content_type"]
        info["error"] = None
    except Exception as e:
        info.update(
            {
                "final_url": None,
                "status_code": None,
                "content_type": None,
                "content_length": None,
                "redirected": None,
                "preview": "",
                "looks_like_ics": False,
                "error": str(e),
            }
        )
    return info
