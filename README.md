# 🌤️ Hava Durumu Chatbot

Modern ve kullanıcı dostu bir hava durumu chatbot web uygulaması. Python FastAPI backend ve vanilla JavaScript frontend ile geliştirilmiştir.

## ✨ Özellikler

### 🤖 Chatbot Özellikleri
- **Doğal Dil İşleme**: Türkçe mesajlardan şehir adı ve soru tipi çıkarma
- **Çoklu Soru Tipleri**:
  - Genel hava durumu sorguları
  - Sıcaklık sorguları ("kaç derece?")
  - Nem sorguları ("nem nasıl?")
  - Rüzgar sorguları ("rüzgar hızı?")
  - Giyinme önerileri ("ne giyeyim?")
  - Haftalık hava durumu tahmini (7 günlük)
  - Aylık hava durumu takvimi (16 günlük)
- **Zaman Çerçevesi Desteği**: Bugün, yarın, dün için hava durumu
- **Konuşma Bağlamı**: Son sorgulanan şehri hatırlama
- **Selamlama ve Etkileşim**: Kullanıcı selamlamalarına ve "nasılsın" sorularına özel yanıtlar

### 🎨 Tasarım Özellikleri
- Modern ve temiz UI/UX tasarımı
- Responsive tasarım (mobil uyumlu)
- Animasyonlu arka plan video
- Renkli chat balonları (kullanıcı/bot ayrımı)
- Haftalık ve aylık hava durumu için özel takvim görünümü
- Hover efektleri ve geçiş animasyonları

### 🌍 API Entegrasyonu
- **Open-Meteo API**: Ücretsiz, API key gerektirmeyen hava durumu servisi
- Geocoding API ile şehir adından koordinat bulma
- Gerçek zamanlı hava durumu verileri
- 16 güne kadar hava durumu tahmini

## 🚀 Kurulum

### Gereksinimler
- Python 3.8+
- pip (Python paket yöneticisi)

### Adımlar

1. **Projeyi klonlayın veya indirin**
```bash
cd havadurumu-python
```

2. **Sanal ortam oluşturun (önerilir)**
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# veya
venv\Scripts\activate  # Windows
```

3. **Bağımlılıkları yükleyin**
```bash
pip install -r requirements.txt
```

4. **Video dosyasını ekleyin (opsiyonel)**
```bash
# Weather_Background_Loop_Video_Generation.mp4 dosyasını 
# app/static/video/ klasörüne kopyalayın
mkdir -p app/static/video
cp Weather_Background_Loop_Video_Generation.mp4 app/static/video/
```

5. **Uygulamayı başlatın**
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

6. **Tarayıcıda açın**
```
http://localhost:8000
```

## 📁 Proje Yapısı

```
havadurumu-python/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI ana uygulama
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py           # Konfigürasyon ayarları
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic veri modelleri
│   ├── routes/
│   │   ├── __init__.py
│   │   └── chat.py             # Chat API endpoint'leri
│   ├── services/
│   │   ├── __init__.py
│   │   ├── nlp.py              # Doğal dil işleme
│   │   └── weather_service.py  # Hava durumu API servisi
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css      # CSS stilleri
│   │   ├── js/
│   │   │   └── chat.js         # Frontend JavaScript
│   │   └── video/
│   │       └── Weather_Background_Loop_Video_Generation.mp4
│   └── templates/
│       └── index.html          # Ana HTML template
├── tests/
│   └── test_weather_service.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## 💬 Kullanım Örnekleri

### Temel Sorgular
- `İstanbul` → İstanbul için güncel hava durumu
- `Ankara'da hava nasıl?` → Ankara için detaylı hava durumu
- `İzmir` → İzmir için güncel hava durumu

### Zaman Çerçeveli Sorgular
- `Ankara'da yarın hava nasıl?` → Yarın için hava durumu
- `İstanbul'da dün hava nasıldı?` → Dün için hava durumu

### Özel Sorular
- `Ankara'da kaç derece?` → Sadece sıcaklık bilgisi
- `İstanbul'da nem nasıl?` → Nem oranı bilgisi
- `İzmir'de rüzgar hızı?` → Rüzgar hızı bilgisi
- `Ankara'da ne giyeyim?` → Giyinme önerisi

### Haftalık ve Aylık Tahminler
- `İstanbul'da haftalık hava durumunu göster` → 7 günlük tahmin
- `Ankara'da aylık hava durumunu göster` → 16 günlük takvim görünümü
- `İzmir haftalık hava durumu` → 7 günlük liste görünümü

### Konuşma Bağlamı
- `Ankara` → Ankara için hava durumu
- `kaç derece?` → Son sorgulanan şehir (Ankara) için sıcaklık
- `nem nasıl?` → Son sorgulanan şehir için nem

### Etkileşim
- `Merhaba` → Bot selamlama
- `Nasılsın?` → Bot rastgele yanıt

## 🛠️ Teknolojiler

- **Backend**: FastAPI, Python 3.8+
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Template Engine**: Jinja2
- **HTTP Client**: httpx (async)
- **API**: Open-Meteo (ücretsiz, API key gerektirmez)
- **Veri Doğrulama**: Pydantic
- **Sunucu**: Uvicorn

## 📝 API Endpoints

### GET `/`
Ana sayfa - Chat arayüzü HTML sayfasını döndürür.

### POST `/api/chat`
Chat endpoint - Kullanıcı mesajını alır ve bot cevabı döndürür.

**Request:**
```json
{
  "message": "İstanbul'da hava nasıl?"
}
```

**Response:**
```json
{
  "reply": "İstanbul'da hava durumu parçalı bulutlu. Bugün nasıl giyinmen gerektiği hakkında bilgi vermemi ister misin?"
}
```

## 🎨 Tasarım Özellikleri

- **Renk Paleti**: Indigo (#6366F1) ve Sky Blue (#0EA5E9) gradient
- **Chat Balonları**: Kullanıcı mesajları sağa, bot mesajları sola hizalı
- **Takvim Görünümü**: Haftalık ve aylık hava durumu için özel grid tasarımı
- **Animasyonlar**: Fade-in mesaj animasyonları, hover efektleri
- **Arka Plan**: Animasyonlu hava durumu video loop (opsiyonel)

## 🔧 Konfigürasyon

Uygulama varsayılan olarak Open-Meteo API'sini kullanır. API key gerektirmez.

Eğer farklı bir API kullanmak isterseniz, `app/core/config.py` dosyasını düzenleyebilirsiniz.

## 🧪 Test

```bash
# Test dosyalarını çalıştır
pytest tests/
```

## 📄 Lisans

Bu proje bir üniversite ödevi için geliştirilmiştir.

## 👨‍💻 Geliştirici Notları

- Tüm kod dosyaları Türkçe yorum satırları içerir
- Open-Meteo API maksimum 16 günlük tahmin verir
- Aylık takvim görünümünde sadece 16 gün için detaylı bilgi gösterilir
- Video arka plan opsiyoneldir, dosya yoksa uygulama normal çalışır

## 🐛 Bilinen Sorunlar

- Open-Meteo API bazen yavaş yanıt verebilir
- Bazı küçük şehirler için geocoding sonuçları bulunamayabilir

## 🔮 Gelecek Geliştirmeler

- [ ] Daha fazla şehir için otomatik tamamlama
- [ ] Hava durumu grafikleri
- [ ] Bildirim sistemi
- [ ] Çoklu dil desteği
- [ ] Hava durumu geçmişi kaydetme

## 📞 İletişim

Sorularınız veya önerileriniz için issue açabilirsiniz.

---

**Not**: Bu proje eğitim amaçlı geliştirilmiştir. Üretim ortamında kullanmadan önce güvenlik ve performans testlerini yapın.
