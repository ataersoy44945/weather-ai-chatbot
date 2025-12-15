# Chat API route'ları - Kullanıcı mesajlarını işleyen endpoint'ler
import random
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from app.models.schemas import ChatRequest, ChatResponse
from app.services.weather_service import WeatherService, WeatherServiceError
from app.services.nlp import (
    extract_city_from_message,
    detect_question_type,
    detect_timeframe,
    QuestionType,
    Timeframe,
)

# API router oluştur
router = APIRouter()
# Jinja2 template environment'ı oluştur
env = Environment(loader=FileSystemLoader("app/templates"))
# Hava durumu servisi instance'ı oluştur
weather_service = WeatherService()
# Son sorgu context'i (basit bellek içi)
LAST_CONTEXT = {"city": None, "offset_days": 0}

def get_clothing_advice(temperature: float, description: str) -> str:
    """
    Sıcaklık ve hava durumuna göre giyinme önerisi verir.
    
    Args:
        temperature: Sıcaklık (Celsius)
        description: Hava durumu açıklaması
    
    Returns:
        str: Giyinme önerisi
    """
    desc_lower = description.lower()
    
    # Çok soğuk
    if temperature < 0:
        if "kar" in desc_lower or "karlı" in desc_lower:
            return "Çok soğuk ve karlı! Kalın mont, atkı, bere ve eldiven giymelisin. Bot giymeyi unutma."
        return "Çok soğuk! Kalın mont, atkı ve bere giymelisin."
    
    # Soğuk
    elif temperature < 10:
        if "yağmur" in desc_lower or "yağmurlu" in desc_lower:
            return "Soğuk ve yağmurlu. Kalın mont, şemsiye ve su geçirmez ayakkabı giymelisin."
        return "Soğuk! Kalın mont veya kaban giymelisin. Atkı da iyi olur."
    
    # Serin
    elif temperature < 18:
        if "yağmur" in desc_lower or "yağmurlu" in desc_lower:
            return "Serin ve yağmurlu. Orta kalınlıkta mont ve şemsiye almalısın."
        return "Serin! Hafif mont veya hırka giymelisin."
    
    # Ilık
    elif temperature < 25:
        if "yağmur" in desc_lower or "yağmurlu" in desc_lower:
            return "Ilık ama yağmurlu. Hafif ceket ve şemsiye almalısın."
        return "Ilık! Uzun kollu tişört veya hafif ceket giyebilirsin."
    
    # Sıcak
    elif temperature < 30:
        return "Sıcak! Kısa kollu tişört ve şort giyebilirsin. Güneş kremi sürmeyi unutma."
    
    # Çok sıcak
    else:
        return "Çok sıcak! İnce kıyafetler giymelisin. Bol su iç ve güneşten korun."

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Ana sayfa - Chat arayüzü HTML sayfasını döndürür"""
    # index.html template'ini yükle
    template = env.get_template("index.html")
    # Template'i render et ve HTML olarak döndür
    return HTMLResponse(content=template.render(request=request))

@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint - Kullanıcı mesajını alır ve bot cevabı döner
    
    Args:
        request: Kullanıcının gönderdiği mesaj içeren ChatRequest
    
    Returns:
        ChatResponse: Bot'un cevabı
    """
    # Mesajı temizle (başındaki/sonundaki boşlukları kaldır)
    original_message = request.message.strip()
    message_lower = original_message.lower()
    
    # Boş mesaj kontrolü
    if not original_message:
        return ChatResponse(reply="💬 Lütfen bir şehir adı yazın. Örneğin: İstanbul veya Ankara")

    # Selamlama tespiti (şehir yoksa selamla)
    greeting_keywords = ["selam", "merhaba", "selamlar", "hey", "hi", "hello", "slm"]
    words = original_message.lower().split()
    if any(w in greeting_keywords for w in words):
        return ChatResponse(
            reply="👋 Merhaba! Size hava durumu hakkında yardımcı olabilirim. "
                  "Bir şehir adı yazın veya \"İstanbul'da hava nasıl?\" gibi bir soru sorun."
        )

    # Nasılsın tespiti - farklı, rastgele yanıtlar
    how_are_you_keywords = ["nasılsın", "nasilsin", "naber", "nabersin", "ne haber", "günün nasıl"]
    if any(k in message_lower for k in how_are_you_keywords):
        responses = [
            "🤖 Harikayım, havalarla ilgilenmek beni mutlu ediyor!",
            "😎 Güneşli bir gün gibi hissediyorum. Sana nasıl yardımcı olabilirim?",
            "🌤️ Bulutlar dağınık ama moral yüksek. Hangi şehrin havasını öğrenelim?",
            "☕ Enerjim yerinde, bir hava tahmini yapmaya hazırım!",
            "🚀 Rüzgar gibi hızlıyım, şehir adını söyle yeter!"
        ]
        return ChatResponse(reply=random.choice(responses))
    
    # Giyinme önerisi onayı kontrolü (evet, tabii, istiyorum vb.)
    confirmation_keywords = ["evet", "tabii", "istiyorum", "isterim", "olur", "tamam", "evet lütfen", "evet ver", "ver", "lütfen"]
    if any(keyword in message_lower for keyword in confirmation_keywords):
        # Son mesajda şehir var mı kontrol et
        city, _ = extract_city_from_message(original_message)
        if city and city.lower() == "evet":
            city = None
        if not city and LAST_CONTEXT["city"]:
            city = LAST_CONTEXT["city"]
            offset_days = LAST_CONTEXT["offset_days"]
        else:
            offset_days = 0

        if city:
            try:
                weather_data = await weather_service.get_current_weather(city, offset_days=offset_days)
                clothing_advice = get_clothing_advice(weather_data.temperature, weather_data.description)
                reply = f"💡 {city} için giyinme önerisi:\n{clothing_advice}"
                return ChatResponse(reply=reply)
            except WeatherServiceError:
                pass
        
        # Şehir bulunamazsa genel öneri ver
        return ChatResponse(
            reply="💡 Genel giyinme önerileri:\n"
            "• 0°C altı: Kalın mont, atkı, bere, eldiven\n"
            "• 0-10°C: Kalın mont veya kaban, atkı\n"
            "• 10-18°C: Hafif mont veya hırka\n"
            "• 18-25°C: Uzun kollu tişört veya hafif ceket\n"
            "• 25°C üstü: Kısa kollu tişört, şort\n"
            "Yağmur varsa şemsiye ve su geçirmez ayakkabı unutma! ☔"
        )
    
    # NLP ile şehir çıkarma (orijinal mesajı kullan - büyük/küçük harf korunmalı)
    city, _ = extract_city_from_message(original_message)

    time_tokens = {"bugün", "bugun", "yarın", "yarin", "dün", "dun", "dünkü", "dunku"}

    # Eğer tek kelimelik devam soruları "kaç", "kac" gibi yanlışlıkla şehir sayıldıysa temizle
    invalid_city_tokens = {"kaç", "kac", "kaç?", "kac?", "kaç derece", "kaç derece?", "evet"}
    if city and (city.lower() in invalid_city_tokens or city.lower() in time_tokens):
        city = None

    # Mesaj "yarın Ankara ..." gibi başlayıp ilk kelime zaman ifadesi ise ikinci kelimeyi dene
    words = original_message.split()
    if not city and words and words[0].lower() in time_tokens and len(words) > 1:
        candidate = words[1].strip("'\".,!?")
        if candidate and candidate.lower() not in invalid_city_tokens and candidate.lower() not in time_tokens:
            city = candidate

    # Şehir bulunamazsa son context'i dene
    if not city and LAST_CONTEXT["city"]:
        city = LAST_CONTEXT["city"]

    # Zaman çerçevesi tespiti
    timeframe = detect_timeframe(original_message)

    # Desteklenen aralık: dün (-1), bugün (0), yarın (+1)
    if timeframe == Timeframe.FUTURE:
        return ChatResponse(reply="📅 Şu an yalnızca bugün ve yarın için hava durumu verebiliyorum.")
    if timeframe == Timeframe.PAST:
        return ChatResponse(reply="⏪ Şu an yalnızca bugün ve dün için hava durumu verebiliyorum.")
    
    # Şehir bulunamadıysa
    if not city:
        return ChatResponse(
            reply="❓ Mesajınızdan şehir adını çıkaramadım. Lütfen şehir adını yazın. Örneğin: İstanbul veya Ankara"
        )
    
    # Tarih offset'i belirle
    if timeframe == Timeframe.TOMORROW:
        offset_days = 1
        day_label = "yarın"
    elif timeframe == Timeframe.YESTERDAY:
        offset_days = -1
        day_label = "dün"
    else:
        offset_days = 0
        day_label = "bugün"

    # Eğer şehir hala yoksa hata ver
    if not city:
        return ChatResponse(
            reply="❓ Mesajınızdan şehir adını çıkaramadım. Lütfen şehir adını yazın. Örneğin: İstanbul veya Ankara"
        )

    # City belirlendiyse context'i şimdiden güncelle (kullanıcı devam sorusu sorabilir)
    LAST_CONTEXT["city"] = city
    LAST_CONTEXT["offset_days"] = offset_days

    # Soru tipini tespit et (küçük harfe çevrilmiş mesajı kullan)
    question_type = detect_question_type(message_lower)
    
    # Aylık hava durumu ise özel işlem
    if question_type == QuestionType.MONTHLY:
        try:
            monthly_data = await weather_service.get_monthly_weather(city)
            # JSON formatında döndür (JavaScript'te takvim formatında gösterilecek)
            import json
            reply = f"MONTHLY_CALENDAR:{json.dumps(monthly_data, ensure_ascii=False)}"
            return ChatResponse(reply=reply)
        except WeatherServiceError as e:
            error_msg = str(e)
            if "bulunamadı" in error_msg.lower() or "geçersiz" in error_msg.lower():
                return ChatResponse(reply="⚠️ Bu şehir bulunamadı. Lütfen geçerli bir şehir adı yazın. Örneğin: İstanbul, Ankara, İzmir")
            elif "bağlanılamadı" in error_msg.lower() or "bağlantı" in error_msg.lower():
                return ChatResponse(reply="⚠️ Şu an hava bilgisine ulaşılamıyor. Lütfen daha sonra tekrar deneyin.")
            else:
                return ChatResponse(reply="⚠️ Şu an hava bilgisine ulaşılamıyor. Lütfen daha sonra tekrar deneyin.")
        except Exception as e:
            import logging
            logging.error(f"Beklenmeyen hata: {str(e)}")
            return ChatResponse(reply="⚠️ Bir sorun oluştu. Lütfen daha sonra tekrar deneyin.")
    
    # Haftalık hava durumu ise özel işlem
    if question_type == QuestionType.WEEKLY:
        try:
            weekly_data = await weather_service.get_weekly_weather(city)
            # Haftalık formatı oluştur
            reply_lines = [f"{city} için 7 günlük hava durumu tahmini:"]
            for day in weekly_data:
                reply_lines.append(
                    f"{day['date']} {day['day_name']} - {day['description']} {day['temperature']}°C"
                )
            reply = "\n".join(reply_lines)
            return ChatResponse(reply=reply)
        except WeatherServiceError as e:
            error_msg = str(e)
            if "bulunamadı" in error_msg.lower() or "geçersiz" in error_msg.lower():
                return ChatResponse(reply="⚠️ Bu şehir bulunamadı. Lütfen geçerli bir şehir adı yazın. Örneğin: İstanbul, Ankara, İzmir")
            elif "bağlanılamadı" in error_msg.lower() or "bağlantı" in error_msg.lower():
                return ChatResponse(reply="⚠️ Şu an hava bilgisine ulaşılamıyor. Lütfen daha sonra tekrar deneyin.")
            else:
                return ChatResponse(reply="⚠️ Şu an hava bilgisine ulaşılamıyor. Lütfen daha sonra tekrar deneyin.")
        except Exception as e:
            import logging
            logging.error(f"Beklenmeyen hata: {str(e)}")
            return ChatResponse(reply="⚠️ Bir sorun oluştu. Lütfen daha sonra tekrar deneyin.")
    
    # Hava durumu bilgisini al
    try:
        # Weather service'den hava durumu verisini çek
        weather_data = await weather_service.get_current_weather(city, offset_days=offset_days)
        # Başarılı sorgudan sonra context'i güncelle
        LAST_CONTEXT["city"] = city
        LAST_CONTEXT["offset_days"] = offset_days
        
        # Rüzgar hızını km/h'den m/s'ye çevir (Open-Meteo km/h döndürüyor)
        wind_speed_ms = weather_data.wind_speed / 3.6
        
        # Soru tipine göre özel cevap oluştur
        if question_type == QuestionType.HUMIDITY:
            # Nem soruları için özel cevap
            reply = f"{city}'da {day_label} nem durumu %{weather_data.humidity}"
        
        elif question_type == QuestionType.TEMPERATURE:
            # Sıcaklık soruları için özel cevap
            reply = f"{city}'da {day_label} sıcaklık {weather_data.temperature:.1f}°C. Hissedilen {weather_data.feels_like:.1f}°C"
        
        elif question_type == QuestionType.WIND:
            # Rüzgar soruları için özel cevap
            reply = f"{city}'da {day_label} rüzgar hızı {wind_speed_ms:.1f} m/s"
        
        elif question_type == QuestionType.CLOTHING:
            # Giyinme önerisi için özel cevap
            clothing_advice = get_clothing_advice(weather_data.temperature, weather_data.description)
            reply = f"{city}'da {day_label} hava durumu {weather_data.description.lower()}. {clothing_advice}"
        
        else:
            # Genel hava durumu - giyinme önerisi sorusu ile birlikte
            if offset_days == 0:
                reply = (
                    f"{city}'da hava durumu {weather_data.description.lower()}. "
                    f"Bugün nasıl giyinmen gerektiği hakkında bilgi vermemi ister misin?"
                )
            elif offset_days == 1:
                reply = (
                    f"{city}'da yarın hava durumu {weather_data.description.lower()}. "
                    f"Yarın için giyinme önerisi ister misin?"
                )
            else:
                reply = (
                    f"{city}'da dün hava durumu {weather_data.description.lower()}. "
                    f"Genel giyinme önerisi ister misin?"
                )
        
        # Cevabı döndür
        return ChatResponse(reply=reply)
        
    # Weather service hatası (geçersiz şehir, API hatası vb.)
    except WeatherServiceError as e:
        # Kullanıcı dostu hata mesajı - teknik detayları gizle
        error_msg = str(e)
        if "bulunamadı" in error_msg.lower() or "geçersiz" in error_msg.lower():
            return ChatResponse(reply="⚠️ Bu şehir bulunamadı. Lütfen geçerli bir şehir adı yazın. Örneğin: İstanbul, Ankara, İzmir")
        elif "bağlanılamadı" in error_msg.lower() or "bağlantı" in error_msg.lower():
            return ChatResponse(reply="⚠️ Şu an hava bilgisine ulaşılamıyor. Lütfen daha sonra tekrar deneyin.")
        else:
            return ChatResponse(reply="⚠️ Şu an hava bilgisine ulaşılamıyor. Lütfen daha sonra tekrar deneyin.")
    # Beklenmeyen diğer hatalar
    except Exception as e:
        # Teknik hataları console'a yazdır, kullanıcıya genel mesaj göster
        import logging
        logging.error(f"Beklenmeyen hata: {str(e)}")
        return ChatResponse(reply="⚠️ Bir sorun oluştu. Lütfen daha sonra tekrar deneyin.")

