import requests


PROXIES = {
    "http": "http://127.0.0.1:7897",
    "https": "http://127.0.0.1:7897",
}


def get_weather(city):

    url = f"https://wttr.in/{city}?format=j1"

    # 先试直连，不行再走 Clash 代理，都失败则返回错误
    resp = None
    for use_proxy in (False, True):
        try:
            if use_proxy:
                resp = requests.get(url, proxies=PROXIES, timeout=10)
            else:
                resp = requests.get(url, timeout=10)
            break
        except Exception:
            continue

    if resp is None:
        return {"error": f"无法获取{city}天气数据，请检查网络连接"}

    try:
        data = resp.json()
        tomorrow = data["weather"][1]
        noon = tomorrow["hourly"][4]

        weather_desc = noon["weatherDesc"][0]["value"]
        temp = noon["tempC"]
        humidity = noon["humidity"]

        return {
            "city": city,
            "weather": weather_desc,
            "temperature": int(temp),
            "humidity": int(humidity),
        }
    except Exception:
        return {"error": f"天气数据解析失败"}