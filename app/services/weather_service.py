"""
Open-Meteo API ile hava durumu bilgisi çeken servis modülü
- Ücretsiz, API key gerektirmez
- Bugün, yarın ve dün için destek eklenmiştir
"""
import httpx
from typing import Optional, List
from datetime import datetime, timedelta
from app.core.config import settings
from app.models.schemas import WeatherData

# Hava durumu açıklamaları için Türkçe mapping
WEATHER_DESCRIPTIONS = {
    "clear": "Açık",
    "sunny": "Güneşli",
    "partly cloudy": "Parçalı bulutlu",
    "cloudy": "Bulutlu",
    "overcast": "Kapalı",
    "fog": "Sisli",
    "drizzle": "Çiseleme",
    "rain": "Yağmurlu",
    "snow": "Karlı",
    "thunderstorm": "Fırtınalı",
    "windy": "Rüzgarlı"
}

# Hava durumu servisi için özel hata sınıfı
class WeatherServiceError(Exception):
    """Hava durumu servisi hataları için özel exception"""
    pass

# Hava durumu servisi sınıfı
class WeatherService:
    def __init__(self):
        # Geocoding API URL'ini config'den al
        self.geocoding_url = settings.GEOCODING_API_URL
        # Weather API URL'ini config'den al
        self.weather_url = settings.WEATHER_API_URL

    def _target_datetime_iso(self, offset_days: int) -> str:
        """Hedef gün için 12:00 zaman damgası (ISO) döndürür."""
        target_dt = datetime.utcnow().replace(minute=0, second=0, microsecond=0) + timedelta(days=offset_days)
        target_dt = target_dt.replace(hour=12)
        return target_dt.strftime("%Y-%m-%dT%H:%M")

    def _closest_hour_index(self, times: List[str], target_iso: str) -> int:
        """Verilen zaman listesinde hedef zamana en yakın index'i döndürür."""
        try:
            return times.index(target_iso)
        except ValueError:
            target_dt = datetime.fromisoformat(target_iso)
            diffs = [abs(datetime.fromisoformat(t) - target_dt) for t in times]
            return diffs.index(min(diffs))

    async def _get_city_coordinates(self, city: str) -> tuple:
        """
        Şehir adından koordinat (enlem, boylam) bulur.
        
        Args:
            city: Şehir adı
            
        Returns:
            tuple: (latitude, longitude, city_name, country_code)
        """
        # Geocoding API'ye istek gönder
        # httpx otomatik olarak URL encoding yapar
        params = {
            "name": city.strip(),  # Şehir adı
            "count": 1,  # Sadece ilk sonucu al
            "language": "tr"  # Türkçe sonuçlar için
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(self.geocoding_url, params=params)
            
            if response.status_code != 200:
                raise WeatherServiceError(f"Şehir arama hatası: {response.status_code}")
            
            data = response.json()
            
            # Sonuç yoksa hata fırlat
            if not data.get("results") or len(data["results"]) == 0:
                raise WeatherServiceError(f"'{city}' şehri bulunamadı. Lütfen geçerli bir şehir adı girin.")
            
            # İlk sonucu al
            result = data["results"][0]
            latitude = result["latitude"]
            longitude = result["longitude"]
            city_name = result.get("name", city)
            country_code = result.get("country_code", "")
            
            return latitude, longitude, city_name, country_code
    
    async def _get_weather_description(self, weather_code: int) -> str:
        """
        WMO hava durumu kodunu Türkçe açıklamaya çevirir.
        
        Args:
            weather_code: WMO hava durumu kodu
            
        Returns:
            str: Türkçe hava durumu açıklaması
        """
        # WMO Weather Interpretation Codes (WW)
        # Basitleştirilmiş mapping
        if weather_code == 0:
            return "Açık"
        elif weather_code in [1, 2, 3]:
            return "Parçalı bulutlu"
        elif weather_code in [45, 48]:
            return "Sisli"
        elif weather_code in [51, 53, 55, 56, 57]:
            return "Çiseleme"
        elif weather_code in [61, 63, 65, 66, 67]:
            return "Yağmurlu"
        elif weather_code in [71, 73, 75, 77]:
            return "Karlı"
        elif weather_code in [80, 81, 82]:
            return "Sağanak yağışlı"
        elif weather_code in [85, 86]:
            return "Kar fırtınası"
        elif weather_code in [95, 96, 99]:
            return "Fırtınalı"
        else:
            return "Bulutlu"
    
    async def get_current_weather(self, city: str, offset_days: int = 0) -> WeatherData:
        """
        Belirtilen şehir için güncel hava durumu bilgisini getirir.
        
        Args:
            city: Şehir adı
            offset_days: 0 (bugün), 1 (yarın), -1 (dün)
            
        Returns:
            WeatherData: Hava durumu bilgileri
            
        Raises:
            WeatherServiceError: API hatası veya geçersiz şehir durumunda
        """
        # Şehir adı boş mu kontrol et
        if not city or not city.strip():
            raise WeatherServiceError("Şehir adı boş olamaz.")

        # forecast/past parametrelerini hazırla
        forecast_days = max(1, offset_days + 1) if offset_days >= 0 else 1
        past_days = abs(offset_days) if offset_days < 0 else 0

        try:
            # Önce şehir adından koordinat bul
            latitude, longitude, city_name, country_code = await self._get_city_coordinates(city)

            # Koordinatlardan hava durumu bilgisi al
            params = {
                "latitude": latitude,  # Enlem
                "longitude": longitude,  # Boylam
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",  # Güncel veriler
                "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",  # Saatlik veriler
                "timezone": "auto",  # Otomatik zaman dilimi
                "forecast_days": forecast_days,
                "past_days": past_days,
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.weather_url, params=params)

                # HTTP hata kontrolü
                if response.status_code != 200:
                    raise WeatherServiceError(f"Hava durumu servisi hatası: {response.status_code}")

                # JSON yanıtını parse et
                data = response.json()

                # offset 0 ise current kullan
                if offset_days == 0:
                    current = data.get("current", {})
                    weather_code = current.get("weather_code", 0)
                    description = await self._get_weather_description(weather_code)
                    return WeatherData(
                        city=city_name,  # Şehir adı
                        temperature=current.get("temperature_2m", 0),  # Sıcaklık (2m yükseklikte)
                        feels_like=current.get("temperature_2m", 0),  # Open-Meteo'da ayrı değer yok, aynı değeri kullan
                        humidity=current.get("relative_humidity_2m", 0),  # Nem oranı (%)
                        wind_speed=current.get("wind_speed_10m", 0),  # Rüzgar hızı (10m yükseklikte, km/h)
                        description=description,  # Hava durumu açıklaması
                        country=country_code.upper() if country_code else None  # Ülke kodu
                    )

                # offset ≠ 0 ise hedef günün saat 12:00 verisini al
                hourly = data.get("hourly", {})
                times = hourly.get("time", [])
                if not times:
                    raise WeatherServiceError("Hava durumu verisi bulunamadı.")

                target_iso = self._target_datetime_iso(offset_days)
                idx = self._closest_hour_index(times, target_iso)

                temp = hourly.get("temperature_2m", [0])[idx]
                humidity = hourly.get("relative_humidity_2m", [0])[idx]
                wind_speed = hourly.get("wind_speed_10m", [0])[idx]
                weather_code = hourly.get("weather_code", [0])[idx]
                description = await self._get_weather_description(weather_code)

                return WeatherData(
                    city=city_name,  # Şehir adı
                    temperature=temp,  # Sıcaklık
                    feels_like=temp,  # Feels like verisi yok, aynı değeri kullanıyoruz
                    humidity=humidity,  # Nem oranı (%)
                    wind_speed=wind_speed,  # Rüzgar hızı (km/h)
                    description=description,  # Hava durumu açıklaması
                    country=country_code.upper() if country_code else None  # Ülke kodu
                )

        # Timeout hatası
        except httpx.TimeoutException:
            raise WeatherServiceError("Hava durumu servisine bağlanılamadı. Lütfen daha sonra tekrar deneyin.")
        # İstek hatası
        except httpx.RequestError as e:
            raise WeatherServiceError(f"Bağlantı hatası: {str(e)}")
        # JSON parse hatası veya eksik alan
        except KeyError as e:
            raise WeatherServiceError(f"API yanıtı beklenmeyen formatta: {str(e)}")
        # Diğer beklenmeyen hatalar
        except Exception as e:
            raise WeatherServiceError(f"Beklenmeyen hata: {str(e)}")
    
    async def get_weekly_weather(self, city: str) -> list:
        """
        Belirtilen şehir için 7 günlük hava durumu tahminini getirir.
        
        Args:
            city: Şehir adı
            
        Returns:
            list: Her gün için hava durumu bilgileri içeren liste
            Her eleman: {
                "date": "15 Aralık 2025",
                "day_name": "Pazartesi",
                "temperature": 16.0,
                "description": "Bulutlu"
            }
            
        Raises:
            WeatherServiceError: API hatası veya geçersiz şehir durumunda
        """
        # Şehir adı boş mu kontrol et
        if not city or not city.strip():
            raise WeatherServiceError("Şehir adı boş olamaz.")
        
        try:
            # Önce şehir adından koordinat bul
            latitude, longitude, city_name, country_code = await self._get_city_coordinates(city)
            
            # 7 günlük tahmin için API isteği
            from datetime import date, timedelta
            start_date = date.today().isoformat()
            end_date = (date.today() + timedelta(days=6)).isoformat()  # 7 günlük tahmin
            
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "daily": "weather_code,temperature_2m_max,temperature_2m_min",  # Günlük veriler
                "timezone": "auto",
                "start_date": start_date,
                "end_date": end_date
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.weather_url, params=params)
                
                if response.status_code != 200:
                    raise WeatherServiceError(f"Hava durumu servisi hatası: {response.status_code}")
                
                data = response.json()
                daily = data.get("daily", {})
                
                dates = daily.get("time", [])
                weather_codes = daily.get("weather_code", [])
                temps_max = daily.get("temperature_2m_max", [])
                temps_min = daily.get("temperature_2m_min", [])
                
                if not dates:
                    raise WeatherServiceError("Haftalık hava durumu verisi bulunamadı.")
                
                # Türkçe gün isimleri
                import locale
                from datetime import datetime
                
                # Her gün için veri oluştur
                weekly_data = []
                for i in range(min(7, len(dates))):
                    date_str = dates[i]
                    # ISO formatından datetime'a çevir
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    
                    # Türkçe tarih formatı
                    turkish_months = {
                        1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan",
                        5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos",
                        9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
                    }
                    
                    turkish_days = {
                        0: "Pazartesi", 1: "Salı", 2: "Çarşamba", 3: "Perşembe",
                        4: "Cuma", 5: "Cumartesi", 6: "Pazar"
                    }
                    
                    day_name = turkish_days[date_obj.weekday()]
                    month_name = turkish_months[date_obj.month]
                    formatted_date = f"{date_obj.day} {month_name} {date_obj.year}"
                    
                    weather_code = weather_codes[i] if i < len(weather_codes) else 0
                    description = await self._get_weather_description(weather_code)
                    
                    # Ortalama sıcaklık (max ve min'in ortalaması)
                    temp_max = temps_max[i] if i < len(temps_max) else 0
                    temp_min = temps_min[i] if i < len(temps_min) else 0
                    temp_avg = (temp_max + temp_min) / 2 if temp_max and temp_min else temp_max or temp_min
                    
                    weekly_data.append({
                        "date": formatted_date,
                        "day_name": day_name,
                        "temperature": round(temp_avg, 1),
                        "description": description
                    })
                
                return weekly_data
                
        except httpx.TimeoutException:
            raise WeatherServiceError("Hava durumu servisine bağlanılamadı. Lütfen daha sonra tekrar deneyin.")
        except httpx.RequestError as e:
            raise WeatherServiceError(f"Bağlantı hatası: {str(e)}")
        except KeyError as e:
            raise WeatherServiceError(f"API yanıtı beklenmeyen formatta: {str(e)}")
        except Exception as e:
            raise WeatherServiceError(f"Beklenmeyen hata: {str(e)}")
    
    async def get_monthly_weather(self, city: str) -> dict:
        """
        Belirtilen şehir için aylık (16 günlük) hava durumu tahminini getirir.
        Open-Meteo API'si maksimum 16 günlük tahmin verir.
        
        Args:
            city: Şehir adı
            
        Returns:
            dict: Aylık hava durumu verileri
            {
                "city": "İstanbul",
                "month": "Aralık 2025",
                "days": [...],
                "year": 2025,
                "month_num": 12
            }
            
        Raises:
            WeatherServiceError: API hatası veya geçersiz şehir durumunda
        """
        # Şehir adı boş mu kontrol et
        if not city or not city.strip():
            raise WeatherServiceError("Şehir adı boş olamaz.")
        
        try:
            # Önce şehir adından koordinat bul
            latitude, longitude, city_name, country_code = await self._get_city_coordinates(city)
            
            # 16 günlük tahmin için API isteği (Open-Meteo maksimum 16 gün verir)
            from datetime import date, timedelta
            start_date = date.today().isoformat()
            end_date = (date.today() + timedelta(days=15)).isoformat()  # 16 günlük tahmin
            
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "daily": "weather_code,temperature_2m_max,temperature_2m_min",
                "timezone": "auto",
                "start_date": start_date,
                "end_date": end_date
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.weather_url, params=params)
                
                if response.status_code != 200:
                    raise WeatherServiceError(f"Hava durumu servisi hatası: {response.status_code}")
                
                data = response.json()
                daily = data.get("daily", {})
                
                dates = daily.get("time", [])
                weather_codes = daily.get("weather_code", [])
                temps_max = daily.get("temperature_2m_max", [])
                temps_min = daily.get("temperature_2m_min", [])
                
                if not dates:
                    raise WeatherServiceError("Aylık hava durumu verisi bulunamadı.")
                
                # Türkçe ay ve gün isimleri
                from datetime import datetime
                
                turkish_months = {
                    1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan",
                    5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos",
                    9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
                }
                
                turkish_days = {
                    0: "Pazartesi", 1: "Salı", 2: "Çarşamba", 3: "Perşembe",
                    4: "Cuma", 5: "Cumartesi", 6: "Pazar"
                }
                
                # İlk günün ayını al
                first_date = datetime.fromisoformat(dates[0].replace('Z', '+00:00'))
                month_name = turkish_months[first_date.month]
                month_label = f"{month_name} {first_date.year}"
                
                # Her gün için veri oluştur
                days_data = []
                for i in range(len(dates)):
                    date_str = dates[i]
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    
                    day_name = turkish_days[date_obj.weekday()]
                    formatted_date = f"{date_obj.day} {turkish_months[date_obj.month]} {date_obj.year}"
                    
                    weather_code = weather_codes[i] if i < len(weather_codes) else 0
                    description = await self._get_weather_description(weather_code)
                    
                    # Ortalama sıcaklık
                    temp_max = temps_max[i] if i < len(temps_max) else 0
                    temp_min = temps_min[i] if i < len(temps_min) else 0
                    temp_avg = (temp_max + temp_min) / 2 if temp_max and temp_min else temp_max or temp_min
                    
                    days_data.append({
                        "day": date_obj.day,
                        "date": formatted_date,
                        "day_name": day_name,
                        "temperature": round(temp_avg, 1),
                        "description": description,
                        "weather_code": weather_code
                    })
                
                return {
                    "city": city_name,
                    "month": month_label,
                    "days": days_data,
                    "year": first_date.year,
                    "month_num": first_date.month
                }
                
        except httpx.TimeoutException:
            raise WeatherServiceError("Hava durumu servisine bağlanılamadı. Lütfen daha sonra tekrar deneyin.")
        except httpx.RequestError as e:
            raise WeatherServiceError(f"Bağlantı hatası: {str(e)}")
        except KeyError as e:
            raise WeatherServiceError(f"API yanıtı beklenmeyen formatta: {str(e)}")
        except Exception as e:
            raise WeatherServiceError(f"Beklenmeyen hata: {str(e)}")

