import httpx

# Default coordinates for Anand, Gujarat, India
DEFAULT_LAT = 22.5560
DEFAULT_LON = 72.9515
DEFAULT_CITY = "Anand, Gujarat"

async def get_coordinates(city_name: str) -> tuple:
    """
    Geocodes a city name to latitude and longitude using Open-Meteo's free geocoding API.
    """
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=en&format=json"
        async with httpx.AsyncClient() as client:
            res = await client.get(url, timeout=5.0)
            if res.status_code == 200:
                data = res.json()
                if "results" in data and len(data["results"]) > 0:
                    result = data["results"][0]
                    name = result.get("name", city_name)
                    country = result.get("country", "")
                    label = f"{name}, {country}" if country else name
                    return float(result["latitude"]), float(result["longitude"]), label
    except Exception as e:
        print(f"Geocoding error: {e}")
    return DEFAULT_LAT, DEFAULT_LON, DEFAULT_CITY

async def get_weather(city: str = None) -> dict:
    """
    Fetches real-time weather data for a city.
    """
    lat, lon, label = DEFAULT_LAT, DEFAULT_LON, DEFAULT_CITY
    if city:
        lat, lon, label = await get_coordinates(city)
        
    try:
        # Fetch current weather details
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=temperature_2m,relativehumidity_2m&timezone=auto"
        async with httpx.AsyncClient() as client:
            res = await client.get(url, timeout=5.0)
            if res.status_code == 200:
                data = res.json()
                current = data.get("current_weather", {})
                
                temp = current.get("temperature", "--")
                wind_speed = current.get("windspeed", "--")
                wind_dir = current.get("winddirection", "--")
                weather_code = current.get("weathercode", 0)
                
                # Simple weather code mapping to human-readable description
                code_map = {
                    0: "Clear Sky",
                    1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
                    45: "Foggy", 48: "Depositing Rime Fog",
                    51: "Light Drizzle", 53: "Moderate Drizzle", 55: "Dense Drizzle",
                    61: "Slight Rain", 63: "Moderate Rain", 65: "Heavy Rain",
                    71: "Slight Snowfall", 73: "Moderate Snowfall", 75: "Heavy Snowfall",
                    77: "Snow Grains",
                    80: "Slight Rain Showers", 81: "Moderate Rain Showers", 82: "Violent Rain Showers",
                    85: "Slight Snow Showers", 86: "Heavy Snow Showers",
                    95: "Thunderstorm", 96: "Thunderstorm with Slight Hail", 99: "Thunderstorm with Heavy Hail"
                }
                desc = code_map.get(weather_code, "Cloudy")
                
                return {
                    "city": label,
                    "temp": f"{temp}°C",
                    "wind": f"{wind_speed} km/h",
                    "wind_dir": f"{wind_dir}°",
                    "description": desc,
                    "raw_temp": temp,
                    "success": True
                }
    except Exception as e:
        print(f"Weather fetch error: {e}")
        
    return {
        "city": label,
        "temp": "N/A",
        "wind": "N/A",
        "wind_dir": "N/A",
        "description": "Offline, sir.",
        "raw_temp": None,
        "success": False
    }
