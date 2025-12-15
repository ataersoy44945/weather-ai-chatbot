# Pydantic veri şemaları
from pydantic import BaseModel
from typing import Optional

# Kullanıcıdan gelen chat mesajı şeması
class ChatRequest(BaseModel):
    message: str

# Bot'tan dönen cevap şeması
class ChatResponse(BaseModel):
    reply: str

# Hava durumu verisi şeması
class WeatherData(BaseModel):
    city: str  # Şehir adı
    temperature: float  # Sıcaklık (Celsius)
    feels_like: float  # Hissedilen sıcaklık (Celsius)
    humidity: int  # Nem oranı (%)
    wind_speed: float  # Rüzgar hızı (m/s)
    description: str  # Hava durumu açıklaması
    country: Optional[str] = None  # Ülke kodu (opsiyonel)

