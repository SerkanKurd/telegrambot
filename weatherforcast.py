import os
# import locale
from typing import Any, Dict
from dotenv import load_dotenv
import requests
import flatdict
from datetime import datetime, timedelta, timezone


load_dotenv()
# locale.setlocale(locale.LC_TIME, "tr_TR.UTF-8")


def fetch_openweather_data(
    lat: float,
    lon: float,
) -> Dict[str, Any]:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENWEATHER_API_KEY bulunamadı. Lütfen .env dosyasına ekleyin.")

    params = {
        "lat": lat,
        "lon": lon,
        "exclude": "current,minutely,hourly",
        "appid": api_key,
        "units": "metric",
        "lang": "tr"
    }
    url = "https://api.openweathermap.org/data/3.0/onecall"
    return request_openweather(url, params)


def request_openweather(
    url: str,
    params: Dict[str, Any],
    timeout: int = 10
) -> Dict[str, Any]:
    resp = requests.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    json_data = resp.json()
    return flatdict.FlatterDict(json_data, delimiter=".")


def format_weather_data(location, data: Dict[str, Any]) -> str:
    if type(location) is str:
        lines = [f"Konum              : {location}"]
    else:
        lines = [f"Konum              : {location[0]}/{location[1]}"]
    lines.append(
        f" Tarih              : {convert_unix_to_time(data.get('daily.0.dt', 0), data.get('timezone_offset'), ['day', 'weekday'])}")
    timezone = data.get("timezone_offset")
    sunrise = convert_unix_to_time(
        data.get("daily.0.sunrise", 0),
        timezone)
    lines.append(f" Gün doğumu         : {sunrise}")
    sunset = convert_unix_to_time(
        data.get("daily.0.sunset", 0),
        timezone)
    lines.append(f" Gün batımı         : {sunset}")
    lines.append(f" Hava durumu        : {data.get("daily.0.summary")}")
    temp = float(data.get("daily.0.temp.day", 0))
    lines.append(f" Hava Sıcaklığı     : {round(float(temp))}°C")
    lines.append(
        f" En Düşük Sıcaklık. : {round(float(data.get("daily.0.temp.min", 0)))}°C")
    lines.append(
        f" En Yğksek Sıcaklık : {round(float(data.get("daily.0.temp.max", 0)))}°C")
    lines.append(
        f" Hissedilen Sıcaklık: {round(float(data.get("daily.0.feels_like.day", 0)))}°C")
    lines.append(f" Hava Basıncı       : {data.get("daily.0.pressure")} hPa")
    lines.append(f" Nem                : {data.get("daily.0.humidity")}%")
    dev_point = data.get("daily.0.dew_point", 0)
    lines.append(f" Çiğ Noktası        : {dev_point}°C")
    lines.append(f" Rüzgar Hızı        : {data.get("daily.0.wind_speed")}")
    wind_deg = data.get("daily.0.wind_deg", 0)
    lines.append(f" Rüzgar Yönü        : {wind_deg}°{wind_direction(wind_deg)}")
    lines.append(f" Rüzgar Hamlesi     : {data.get("daily.0.wind_gust")}")
    lines.append(
        f" Açıklama           : {data.get("daily.0.weather.0.description")}")
    lines.append(
        f" Bulut Tabaı        : {round((float(temp) - float(dev_point))*125)} m")
    lines.append(f" Bulutluluk         : {data.get("daily.0.clouds")}%")
    lines.append(f" Yağış Miktarı      : {data.get("daily.0.rain", 0)} mm")
    lines.append(f" Yağış İhtimali     : {data.get("daily.0.pop")}%")
    lines.append(f" UV Endexi          : {data.get("daily.0.uvi")}")
    return "\n".join([l for l in lines if l])


def convert_unix_to_time(unix_timestamp: int,
                         tz_offset,
                         opt: list = ["time"]) -> str:
    offset_seconds = int(tz_offset or 0)
    utc_time = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
    local_time = utc_time + timedelta(seconds=offset_seconds)
    param = ""
    if "day" in opt:
        param += "%d.%m.%Y "
    if "time" in opt:
        param += "%H:%M "
    if "weekday" in opt:
        param += "%A"
    return local_time.strftime(param.strip())


def wind_direction(degree: int) -> str:
    directions = ["K", "KD", "D", "GD", "G", "GB", "B", "KB"]
    idx = round(degree / 45) % 8
    return directions[idx]


def get_takeoff_forcast(
        location=["Orkut Baysal Yamaç Paraşütü Pisti", "Ankara"],
        lat:  float = 40.031,
        lon: float = 32.326,) -> str:
    json_data = fetch_openweather_data(lat, lon)
    return format_weather_data(location, json_data)


if __name__ == "__main__":
    print(get_takeoff_forcast(
        "Ankara",
        40.031,
        32.326))
