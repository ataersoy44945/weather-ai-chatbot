# Ortam değişkenlerini yöneten konfigürasyon modülü
import os
from dotenv import load_dotenv

# .env dosyasından değişkenleri yükle
load_dotenv()

class Settings:
    # Uygulama ayarlarını yöneten sınıf
    def __init__(self):
        # Open-Meteo Geocoding API URL (şehir adından koordinat bulmak için)
        self.GEOCODING_API_URL: str = "https://geocoding-api.open-meteo.com/v1/search"
        # Open-Meteo Weather API URL (hava durumu bilgisi için)
        self.WEATHER_API_URL: str = "https://api.open-meteo.com/v1/forecast"
        # Open-Meteo API key gerektirmez - tamamen ücretsiz

# Global settings instance'ı oluştur
settings = Settings()

