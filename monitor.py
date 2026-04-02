import os
import time
import requests

# ── Настройки ──────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]   # из GitHub Secrets
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]  # ваш chat_id
TIMEOUT = 10        # секунд до таймаута запроса
SLOW_THRESHOLD = 3  # секунд — считать сайт «медленным»

# ── Вспомогательные функции ────────────────────────────────────────────────────

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
    """Проверяет доступность и время ответа сайта."""
    result = {"url": url, "ok": False, "status": None, "elapsed": None, "error": None}
    try:
        start = time.time()
        resp = requests.get(url, timeout=TIMEOUT, allow_redirects=True,
                            headers={"User-Agent": "SiteMonitorBot/1.0"})
        elapsed = round(time.time() - start, 2)
        result.update({"ok": resp.ok, "status": resp.status_code, "elapsed": elapsed})
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


# ── Основная логика ────────────────────────────────────────────────────────────

def main():
    sites = load_sites()
    if not sites:
        print("Список сайтов пуст.")
        return

    issues = []
    warnings = []
    report_lines = []

    for url in sites:
        r = check_site(url)

        if not r["ok"]:
            # Сайт недоступен
            if r["error"]:
                line = f"🔴 <b>{url}</b>\n   ⚠️ {r['error']}"
            else:
                line = f"🔴 <b>{url}</b>\n   HTTP {r['status']}"
            issues.append(line)
        elif r["elapsed"] and r["elapsed"] > SLOW_THRESHOLD:
            # Сайт работает, но медленно
            line = f"🟡 <b>{url}</b>\n   HTTP {r['status']} | {r['elapsed']}s (медленно)"
            warnings.append(line)
        else:
            line = f"🟢 {url} | HTTP {r['status']} | {r['elapsed']}s"

        report_lines.append(line)
        print(line.replace("\n", " "))

    # Отправляем уведомление только при проблемах / предупреждениях
    if issues or warnings:
        parts = ["<b>🚨 Site Monitor — обнаружены проблемы</b>\n"]
        if issues:
            parts.append("— Недоступны:")
            parts.extend(issues)
        if warnings:
            parts.append("\n— Медленный ответ:")
            parts.extend(warnings)
        send_telegram("\n".join(parts))
    else:
        # Раз в сутки можно слать «всё ок» — раскомментируйте если нужно:
        # send_telegram("✅ Все сайты работают нормально.")
        print("✅ Все сайты в норме, уведомления не отправлены.")


if __name__ == "__main__":
    main()
