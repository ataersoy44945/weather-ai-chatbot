# Doğal dil işleme modülü - Kullanıcı mesajından şehir adı ve soru tipi çıkarma
import re
from typing import Optional, Tuple
from enum import Enum
from datetime import date

# Türkçe zaman ifadeleri listesi
TIME_KEYWORDS = ["yarın", "haftaya", "gelecek", "sonra", "önce", "bugün", "şimdi", "şu an"]

# Soru tipleri enum'u
class QuestionType(Enum):
    GENERAL = "general"  # Genel hava durumu
    TEMPERATURE = "temperature"  # Sıcaklık
    HUMIDITY = "humidity"  # Nem
    WIND = "wind"  # Rüzgar
    CLOTHING = "clothing"  # Giyinme önerisi
    WEEKLY = "weekly"  # Haftalık hava durumu
    MONTHLY = "monthly"  # Aylık hava durumu


class Timeframe(Enum):
    TODAY = "today"       # Bugün
    TOMORROW = "tomorrow" # Yarın
    YESTERDAY = "yesterday" # Dün
    FUTURE = "future"     # Daha ileri tarih (desteklenmiyor)
    PAST = "past"         # Daha eski tarih (desteklenmiyor)


def normalize_city_token(token: str) -> str:
    """
    Şehir adının sonundaki Türkçe ekleri temizler.
    Örn: "dubaide" -> "dubai", "ankara'da" -> "ankara", "istanbulun" -> "istanbul"
    """
    cleaned = token.strip(" '\".,!?")
    lower = cleaned.lower()
    
    # Türkçe ekler listesi (öncelik sırasına göre - uzun olanlar önce)
    suffixes = [
        "'da", "'de", "'ta", "'te",  # İyelik + bulunma (İstanbul'da)
        "'nin", "'nın", "'nun", "'nün",  # İyelik ekleri (Ankara'nın)
        "'un", "'ün", "'ın", "'in",  # İyelik ekleri (İstanbul'un)
        "nin", "nın", "nun", "nün",  # İyelik ekleri (Ankaranın)
        "da", "de", "ta", "te",      # Bulunma hali (Ankarada)
        "un", "ün", "ın", "in",      # İyelik ekleri (İstanbulun)
    ]
    
    for suf in suffixes:
        if lower.endswith(suf):
            cleaned = cleaned[: -len(suf)]
            break
    
    return cleaned

def extract_city_from_message(message: str) -> Tuple[Optional[str], bool]:
    """
    Kullanıcı mesajından şehir ismini çıkarır.
    
    Args:
        message: Kullanıcının yazdığı mesaj
    
    Returns:
        Tuple[Optional[str], bool]: (şehir_ismi, gelecek_zaman_var_mı)
    """
    # Boş mesaj kontrolü
    if not message or not message.strip():
        return None, False
    
    # Mesajı küçük harfe çevir ve başındaki/sonundaki boşlukları temizle
    message_lower = message.lower().strip()
    
    # Gelecek zaman kontrolü - mesajda zaman ifadesi var mı?
    has_future_time = any(keyword in message_lower for keyword in TIME_KEYWORDS)
    
    # Mesajı temizle ve kelimelere ayır
    # Türkçe karakterleri koru - orijinal mesajı kullan
    words = re.findall(r'\b\w+\b', message)
    
    # Eğer tek kelime varsa, şehir olarak kabul et
    if len(words) == 1:
        # Türkçe karakterleri koruyarak capitalize yap
        city_name = normalize_city_token(words[0])
        if city_name:
            # İlk harfi büyük yap, geri kalanını küçük
            city_name = city_name[0].upper() + city_name[1:].lower() if len(city_name) > 1 else city_name.upper()
        return city_name, has_future_time
    
    # Soru kelimeleri listesi
    question_keywords = ["hava", "havası", "durumu", "nem", "sıcaklık", "rüzgar", "nasıl", "ne", "kaç", "haftalık", "hafta", "yaz", "yazar"]
    
    # Eğer ikinci kelime soru kelimesi ise, ilk kelime şehirdir
    if len(words) >= 2 and words[1].lower() in question_keywords:
        city_name = normalize_city_token(words[0])
        city_name = city_name[0].upper() + city_name[1:].lower() if len(city_name) > 1 else city_name.upper()
        return city_name, has_future_time
    
    # Çok kelimeli mesajlarda şehir ismini bulmaya çalış
    # Önce apostrof içeren durumları kontrol et (İstanbul'da, İstanbul'un gibi)
    apostrophe_patterns = [
        (r"([A-Za-zÇĞİÖŞÜçğıöşü]+)'?(?:da|de|ta|te)", message),  # İstanbul'da, Ankarada
        (r"([A-Za-zÇĞİÖŞÜçğıöşü]+)'?(?:un|ün|ın|in)", message),  # İstanbul'un, Ankaranın
        (r"([A-Za-zÇĞİÖŞÜçğıöşü]+)'?(?:nin|nın|nun|nün)", message),  # Ankara'nın
    ]
    for pattern, search_text in apostrophe_patterns:
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            city_raw = match.group(1)  # Şehir adını al (ekler dahil değil)
            city = normalize_city_token(city_raw)  # Ekleri temizle
            if city and city.lower() not in question_keywords and len(city) > 2:  # En az 3 karakter olsun
                city = city[0].upper() + city[1:].lower() if len(city) > 1 else city.upper()
                return city, has_future_time
    
    # Diğer pattern'ler ile dene
    city_patterns = [
        (r"(\S+?)\s+(?:için|hakkında|ile ilgili)", message_lower),  # İstanbul için, Ankara hakkında gibi
    ]
    
    # Her pattern'i dene
    for pattern, search_text in city_patterns:
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            # Şehir adını bulduk
            city_raw = normalize_city_token(match.group(1))
            # Apostrof ve noktalama işaretlerini temizle
            city_raw = city_raw.strip("'\".,!?")
            if city_raw and city_raw.lower() not in question_keywords:
                # Orijinal mesajdan şehir adını al
                start_pos = match.start(1)
                end_pos = match.end(1)
                city = message[start_pos:end_pos]
                # Apostrof ve noktalama işaretlerini temizle
                city = city.strip("'\".,!?")
                # İlk harfi büyük yap, geri kalanını küçük
                city = city[0].upper() + city[1:].lower() if len(city) > 1 else city.upper()
                return city, has_future_time
    
    # Eğer hiçbir pattern eşleşmezse, ilk kelimeyi şehir olarak dene
    if words:
        city_name = words[0]
        city_name = city_name[0].upper() + city_name[1:].lower() if len(city_name) > 1 else city_name.upper()
        return city_name, has_future_time
    
    # Hiçbir şey bulunamadı
    return None, has_future_time

def detect_question_type(message: str) -> QuestionType:
    """
    Kullanıcı mesajından soru tipini tespit eder.
    
    Args:
        message: Kullanıcının yazdığı mesaj
    
    Returns:
        QuestionType: Soru tipi
    """
    # Mesajı küçük harfe çevir
    message_lower = message.lower().strip()
    
    # Nem soruları - daha kapsamlı pattern
    humidity_keywords = ["nem", "nem oranı", "nem durumu", "nem nasıl", "nem ne kadar", "nem var mı", "nem kaç"]
    if any(keyword in message_lower for keyword in humidity_keywords):
        return QuestionType.HUMIDITY
    
    # Sıcaklık soruları
    temperature_keywords = ["sıcaklık", "sıcak", "soğuk", "kaç derece", "derece", "sıcaklık nasıl"]
    if any(keyword in message_lower for keyword in temperature_keywords):
        return QuestionType.TEMPERATURE
    
    # Rüzgar soruları
    wind_keywords = ["rüzgar", "rüzgar hızı", "rüzgar nasıl", "rüzgarlı"]
    if any(keyword in message_lower for keyword in wind_keywords):
        return QuestionType.WIND
    
    # Giyinme önerisi soruları
    clothing_keywords = ["giyin", "giyim", "ne giy", "nasıl giyin", "kıyafet", "giyinme", "giyim önerisi"]
    if any(keyword in message_lower for keyword in clothing_keywords):
        return QuestionType.CLOTHING
    
    # Aylık hava durumu soruları
    monthly_keywords = ["aylık", "ay", "aylık hava", "aylık tahmin", "aylık durum", "aylık göster"]
    if any(keyword in message_lower for keyword in monthly_keywords):
        return QuestionType.MONTHLY
    
    # Haftalık hava durumu soruları
    weekly_keywords = ["haftalık", "hafta", "7 gün", "yedi gün", "bir hafta"]
    if any(keyword in message_lower for keyword in weekly_keywords):
        return QuestionType.WEEKLY
    
    # Genel hava durumu (varsayılan)
    return QuestionType.GENERAL


def detect_timeframe(message: str) -> Timeframe:
    """
    Mesajdan istenen zaman bilgisini tespit eder (bugün, yarın, dün).
    Daha ileri tarih veya daha eski tarih talebinde kısıtlı destek verilir.
    """
    message_lower = message.lower().strip()

    # Yarın
    if any(key in message_lower for key in ["yarın", "tomorrow"]):
        return Timeframe.TOMORROW

    # Dün
    if any(key in message_lower for key in ["dün", "dunku", "dünkü", "yesterday"]):
        return Timeframe.YESTERDAY

    # Gelecek ifadeleri (haftaya, sonraki günler)
    if any(key in message_lower for key in ["haftaya", "gelecek", "sonraki", "sonra", "ileriki", "ileri"]):
        return Timeframe.FUTURE

    # Geçmiş ifadeleri (geçen hafta vb.)
    if any(key in message_lower for key in ["geçen", "gecen", "önceki", "geçmiş", "gecmis"]):
        return Timeframe.PAST

    # Varsayılan: bugün
    return Timeframe.TODAY

