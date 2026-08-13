from geopy.geocoders import Nominatim


def find_city(lat: float, lon: float):
    try:
        geolocator = Nominatim(user_agent="geoapi")
        location = geolocator.reverse(f"{lat},{lon}", language="tr")
        city = location.raw["address"]["state"]
    except Exception:
        city = ""
    return city


if __name__ == "__main__":
    print(find_city(39.9334, 32.8597))
