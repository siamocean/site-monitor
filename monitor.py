import os
import time
import requests

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
TIMEOUT = 10
SLOW_THRESHOLD = 3

def send_telegram(text: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"[Telegram error] {e}")

def check_site(url: str) -> dict:
    result = {"url": url, "ok": False, "status": None, "elapsed": None, "error": None}
    try:
        start = time.time()
        resp = requests.get(url, timeout=TIMEOUT, allow_redirects=True,
                            headers={"User-Agent": "SiteMonitorBot/1.0"})
        elapsed = round(time.time() - start, 2)
        ok = resp.status_code < 500
        result.update({"ok": ok, "status": resp.status_code, "elapsed": elapsed})
    except requests.exceptions.Timeout:
        result["error"] = "Таймаут"
    except requests.exceptions.ConnectionError:
        result["error"] = "Нет соединения"
    except Exception as e:
        result["error"] = str(e)
    return result

def load_sites(path: str = "sites.txt") -> list[str]:
    with open(path, encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    return lines

def main():
    sites = load_sites()
    if not sites:
        print("Список сайтов пуст.")
        return

    issues = []
    warnings = []

    for url in sites:
        r = check_site(url)

        if not r["ok"]:
            if r["error"]:
                line = f"<b>{url}</b>\n   {r['error']}"
            else:
                line = f"<b>{url}</b>\n   HTTP {r['status']}"
            issues.append(line)
            print(f"FAIL {url}")
        elif r["elapsed"] and r["elapsed"] > SLOW_THRESHOLD:
            line = f"<b>{url}</b>\n   HTTP {r['status']} | {r['elapsed']}s (медленно)"
            warnings.append(line)
            print(f"SLOW {url} | {r['elapsed']}s")
        else:
            print(f"OK   {url} | HTTP {r['status']} | {r['elapsed']}s")

    if issues or warnings:
        parts = ["<b>Site Monitor — обнаружены проблемы</b>\n"]
        if issues:
            parts.append("Недоступны:")
            parts.extend(issues)
        if warnings:
            parts.append("\nМедленный ответ:")
            parts.extend(warnings)
        send_telegram("\n".join(parts))
    else:
        print("Все сайты в норме.")

if __name__ == "__main__":
    main()
