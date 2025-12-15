# Weather service için unit testler
import pytest
from app.services.weather_service import WeatherService, WeatherServiceError

# Bu testler için gerçek API key gerekir
# Test ortamında mock kullanılabilir

@pytest.mark.asyncio
async def test_get_current_weather_invalid_city():
    """Geçersiz şehir adı için hata kontrolü testi"""
    # Weather service instance'ı oluştur
    service = WeatherService()
    
    # Geçersiz şehir adı ile hata fırlatılmasını bekle
    with pytest.raises(WeatherServiceError):
        await service.get_current_weather("InvalidCityName12345")

@pytest.mark.asyncio
async def test_get_current_weather_empty_city():
    """Boş şehir adı için hata kontrolü testi"""
    # Weather service instance'ı oluştur
    service = WeatherService()
    
    # Boş şehir adı ile hata fırlatılmasını bekle
    with pytest.raises(WeatherServiceError):
        await service.get_current_weather("")

