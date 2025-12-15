// Chat arayüzü JavaScript dosyası - Kullanıcı etkileşimlerini yönetir

// DOM elementlerini seç
const messagesContainer = document.getElementById('messages');  // Mesajların gösterileceği container
const messageInput = document.getElementById('messageInput');  // Kullanıcı mesaj input alanı
const sendButton = document.getElementById('sendButton');  // Gönder butonu

// Enter tuşu ile gönderme - Enter'a basıldığında mesaj gönder
messageInput.addEventListener('keypress', (e) => {
    // Enter tuşuna basıldıysa ve Shift basılı değilse mesaj gönder
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();  // Varsayılan davranışı engelle
        sendMessage();  // Mesaj gönder
    }
});

// Gönder butonu tıklama event'i
sendButton.addEventListener('click', sendMessage);

// Mesaj gönderme fonksiyonu - API'ye istek atar
async function sendMessage() {
    // Input'tan mesajı al ve başındaki/sonundaki boşlukları temizle
    const message = messageInput.value.trim();
    
    // Boş mesaj kontrolü
    if (!message) {
        return;  // Mesaj boşsa işlemi durdur
    }
    
    // Kullanıcı mesajını ekrana ekle
    addMessage(message, 'user');
    // Input alanını temizle
    messageInput.value = '';
    
    // Butonu devre dışı bırak (çift gönderimi önlemek için)
    sendButton.disabled = true;
    sendButton.textContent = 'Gönderiliyor...';
    
    // Loading mesajı göster (geçici mesaj)
    const loadingId = addMessage('Yükleniyor...', 'bot', true);
    
    try {
        // API'ye POST isteği gönder
        const response = await fetch('/api/chat', {
            method: 'POST',  // HTTP metodu
            headers: {
                'Content-Type': 'application/json',  // JSON formatında gönder
            },
            body: JSON.stringify({ message: message })  // Mesajı JSON'a çevir
        });
        
        // Yanıtı JSON formatına çevir
        const data = await response.json();
        
        // Loading mesajını kaldır
        removeMessage(loadingId);
        
        // Bot cevabını ekrana ekle
        addMessage(data.reply, 'bot');
        
    } catch (error) {
        // Hata durumunda loading mesajını kaldır
        removeMessage(loadingId);
        
        // Hata mesajı göster
        addMessage('Bir hata oluştu. Lütfen tekrar deneyin.', 'bot');
        // Konsola hata yazdır (debug için)
        console.error('Error:', error);
    } finally {
        // Her durumda butonu tekrar aktif et
        sendButton.disabled = false;
        sendButton.textContent = 'Gönder';
        // Input alanına focus ver
        messageInput.focus();
    }
}

// Mesaj ekleme fonksiyonu - Chat ekranına yeni mesaj ekler
function addMessage(text, type, isTemporary = false) {
    // Yeni mesaj div elementi oluştur
    const messageDiv = document.createElement('div');
    // Benzersiz mesaj ID'si oluştur (zaman damgası + rastgele sayı)
    const messageId = 'msg-' + Date.now() + '-' + Math.random();
    messageDiv.id = messageId;
    // Mesaj tipine göre CSS class ekle (user veya bot)
    messageDiv.className = `message ${type}-message`;
    
    // İkon ekle
    const iconSpan = document.createElement('span');
    iconSpan.className = 'message-icon';
    iconSpan.textContent = type === 'user' ? '🧑‍💻' : '🌤️';
    messageDiv.appendChild(iconSpan);
    
    // Mesaj içeriği için div oluştur
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Geçici mesaj ise (loading) HTML içeriği ekle
    if (isTemporary) {
        contentDiv.innerHTML = '<span class="loading"></span> ' + text;
    } else {
        // Aylık hava durumu mesajı mı kontrol et (JSON formatında)
        if (text.startsWith('MONTHLY_CALENDAR:')) {
            const jsonData = text.replace('MONTHLY_CALENDAR:', '');
            try {
                const monthlyData = JSON.parse(jsonData);
                contentDiv.innerHTML = formatMonthlyCalendar(monthlyData);
            } catch (e) {
                contentDiv.textContent = text;
            }
        }
        // Haftalık hava durumu mesajı mı kontrol et
        else if (text.includes('günlük hava durumu tahmini:')) {
            contentDiv.innerHTML = formatWeeklyWeatherMessage(text);
        }
        // Günlük hava durumu mesajı mı kontrol et
        else if (text.includes('için hava durumu:') || text.includes('Sıcaklık:')) {
            contentDiv.innerHTML = formatWeatherMessage(text);
        } else {
            // Normal mesajlar için - boşlukları düzelt ama satır sonlarını koru
            const cleanText = text.trim().replace(/\s+/g, ' ').replace(/\n+/g, '\n');  // Satır sonlarını koru
            contentDiv.innerHTML = cleanText.replace(/\n/g, '<br>');  // Satır sonlarını <br> ile değiştir
        }
    }
    
    // İçeriği mesaj div'ine ekle
    messageDiv.appendChild(contentDiv);
    // Mesajı container'a ekle
    messagesContainer.appendChild(messageDiv);
    
    // Scroll'u en alta kaydır (yeni mesajı görmek için)
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // Mesaj ID'sini döndür (geçici mesajları silmek için)
    return messageId;
}

// Hava durumu mesajını formatla
function formatWeatherMessage(text) {
    const lines = text.split('\n');
    const cityLine = lines[0];
    const tempLine = lines.find(line => line.includes('Sıcaklık:'));
    const feelsLikeLine = lines.find(line => line.includes('Hissedilen:'));
    const humidityLine = lines.find(line => line.includes('Nem:'));
    const windLine = lines.find(line => line.includes('Rüzgar:'));
    const statusLine = lines.find(line => line.includes('Durum:'));
    
    // Sıcaklık değerini çıkar
    const tempMatch = tempLine?.match(/Sıcaklık:\s*([\d.]+)/);
    const temp = tempMatch ? tempMatch[1] : '';
    
    // Durum açıklamasını çıkar
    const statusMatch = statusLine?.match(/Durum:\s*(.+)/);
    const status = statusMatch ? statusMatch[1] : '';
    
    // Hava durumu ikonu seç
    const weatherIcon = getWeatherIcon(status);
    
    // Şehir adını çıkar
    const cityMatch = cityLine.match(/(.+?)\s+için/);
    const city = cityMatch ? cityMatch[1] : '';
    
    let html = `<div class="weather-message">`;
    html += `<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">`;
    html += `<span style="font-size: 24px;">${weatherIcon}</span>`;
    html += `<strong style="font-size: 18px; color: #0F172A;">${city}</strong>`;
    html += `</div>`;
    
    if (temp) {
        html += `<div class="weather-temp">${temp}°C</div>`;
    }
    
    html += `<div class="weather-details">`;
    
    if (feelsLikeLine) {
        const feelsMatch = feelsLikeLine.match(/Hissedilen:\s*([\d.]+)/);
        if (feelsMatch) {
            html += `<div class="weather-detail-item"><span>🌡️</span><span>Hissedilen: ${feelsMatch[1]}°C</span></div>`;
        }
    }
    
    if (humidityLine) {
        const humidityMatch = humidityLine.match(/Nem:\s*(.+)/);
        if (humidityMatch) {
            html += `<div class="weather-detail-item"><span>💧</span><span>Nem: ${humidityMatch[1]}</span></div>`;
        }
    }
    
    if (windLine) {
        const windMatch = windLine.match(/Rüzgar:\s*(.+)/);
        if (windMatch) {
            html += `<div class="weather-detail-item"><span>💨</span><span>Rüzgar: ${windMatch[1]}</span></div>`;
        }
    }
    
    if (status) {
        html += `<div class="weather-detail-item"><span>${weatherIcon}</span><span>${status}</span></div>`;
    }
    
    html += `</div></div>`;
    
    return html;
}

// Aylık hava durumu takvimi formatla
function formatMonthlyCalendar(data) {
    // Veri kontrolü - güvenli erişim
    const city = data?.city || 'Bilinmeyen Şehir';
    const month = data?.month || '';
    const days = data?.days || [];
    const year = data?.year || new Date().getFullYear();
    const month_num = data?.month_num || new Date().getMonth() + 1;
    
    // Türkçe gün isimleri (kısa)
    const dayNames = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz'];
    
    // Ayın ilk gününün haftanın hangi günü olduğunu bul
    const firstDay = new Date(year, month_num - 1, 1);
    const firstDayOfWeek = firstDay.getDay(); // 0=Pazar, 1=Pazartesi, ...
    // Pazartesi bazlı hafta (0=Pazartesi, 6=Pazar)
    const startOffset = firstDayOfWeek === 0 ? 6 : firstDayOfWeek - 1;
    
    // Günleri tarih bazlı map'e çevir
    const daysMap = {};
    if (Array.isArray(days)) {
        days.forEach(day => {
            if (day && day.day) {
                daysMap[day.day] = day;
            }
        });
    }
    
    // Ayın kaç gün olduğunu bul
    const daysInMonth = new Date(year, month_num, 0).getDate();
    
    let html = `<div class="weather-message monthly-calendar">`;
    html += `<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 24px;">`;
    html += `<span style="font-size: 32px;">📅</span>`;
    html += `<strong style="font-size: 22px; color: #0F172A;">${city} - ${month}</strong>`;
    html += `</div>`;
    
    // Takvim grid - CSS class kullan
    html += `<div class="calendar-grid">`;
    
    // Gün başlıkları - CSS class kullan
    dayNames.forEach(dayName => {
        html += `<div class="calendar-day-header">${dayName}</div>`;
    });
    
    // Boş hücreler (ayın ilk gününden önce)
    for (let i = 0; i < startOffset; i++) {
        html += `<div class="calendar-empty-cell"></div>`;
    }
    
    // Günler - CSS class kullan
    for (let day = 1; day <= daysInMonth; day++) {
        const dayData = daysMap[day];
        const dayOfWeek = (startOffset + day - 1) % 7;
        const isWeekend = dayOfWeek === 5 || dayOfWeek === 6;
        
        if (dayData) {
            const weatherIcon = getWeatherIcon(dayData.description);
            const weekendClass = isWeekend ? ' weekend' : '';
            html += `<div class="calendar-day-cell${weekendClass}">`;
            html += `<div class="calendar-day-number">${day}</div>`;
            html += `<div class="calendar-day-icon">${weatherIcon}</div>`;
            html += `<div class="calendar-day-temp">${dayData.temperature}°</div>`;
            html += `</div>`;
        } else {
            const weekendClass = isWeekend ? ' weekend' : '';
            html += `<div class="calendar-day-cell empty${weekendClass}">`;
            html += `<div style="font-weight: 500; color: #CBD5E1; font-size: 15px;">${day}</div>`;
            html += `</div>`;
        }
    }
    
    html += `</div>`;
    
    // Açıklama - CSS class kullan
    html += `<div class="calendar-note">`;
    html += `💡 Not: Open-Meteo API'si maksimum 16 günlük tahmin veriyor. Bu yüzden sadece önümüzdeki 16 gün için detaylı bilgi gösteriliyor.`;
    html += `</div>`;
    
    html += `</div>`;
    
    return html;
}

// Haftalık hava durumu mesajını formatla
function formatWeeklyWeatherMessage(text) {
    const lines = text.split('\n');
    const headerLine = lines[0];  // "İstanbul için 7 günlük hava durumu tahmini:"
    const cityMatch = headerLine.match(/(.+?)\s+için/);
    const city = cityMatch ? cityMatch[1] : '';
    
    let html = `<div class="weather-message">`;
    html += `<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">`;
    html += `<span style="font-size: 24px;">📅</span>`;
    html += `<strong style="font-size: 18px; color: #0F172A;">${city} - 7 Günlük Tahmin</strong>`;
    html += `</div>`;
    
    html += `<div style="display: flex; flex-direction: column; gap: 12px;">`;
    
    // Her gün için satır oluştur
    for (let i = 1; i < lines.length; i++) {
        const dayLine = lines[i].trim();
        if (!dayLine) continue;
        
        // Format: "15 Aralık 2025 Pazartesi - Yağmurlu 8.9°C"
        const parts = dayLine.split(' - ');
        if (parts.length === 2) {
            const datePart = parts[0];  // "15 Aralık 2025 Pazartesi"
            const weatherPart = parts[1];  // "Yağmurlu 8.9°C"
            
            const weatherMatch = weatherPart.match(/(.+?)\s+([\d.]+)°C/);
            const description = weatherMatch ? weatherMatch[1] : weatherPart;
            const temp = weatherMatch ? weatherMatch[2] : '';
            
            const weatherIcon = getWeatherIcon(description);
            
            html += `<div style="display: flex; align-items: center; gap: 16px; padding: 16px; background: #F8FAFC; border-radius: 12px; border-left: 4px solid #6366F1;">`;
            html += `<span style="font-size: 28px;">${weatherIcon}</span>`;
            html += `<div style="flex: 1;">`;
            html += `<div style="font-weight: 600; color: #0F172A; margin-bottom: 6px; font-size: 16px;">${datePart}</div>`;
            html += `<div style="color: #64748B; font-size: 15px;">${description} ${temp ? temp + '°C' : ''}</div>`;
            html += `</div>`;
            html += `</div>`;
        } else {
            // Eğer format beklenen gibi değilse, satırı olduğu gibi göster
            html += `<div style="padding: 8px; color: #334155;">${dayLine}</div>`;
        }
    }
    
    html += `</div></div>`;
    
    return html;
}

// Hava durumu ikonu seç
function getWeatherIcon(status) {
    const statusLower = status.toLowerCase();
    if (statusLower.includes('açık') || statusLower.includes('güneşli')) {
        return '☀️';
    } else if (statusLower.includes('bulutlu')) {
        return '☁️';
    } else if (statusLower.includes('parçalı')) {
        return '⛅';
    } else if (statusLower.includes('yağmur')) {
        return '🌧️';
    } else if (statusLower.includes('kar')) {
        return '❄️';
    } else if (statusLower.includes('fırtına')) {
        return '⛈️';
    } else if (statusLower.includes('sis')) {
        return '🌫️';
    } else {
        return '🌤️';
    }
}

// Mesaj silme fonksiyonu - Geçici mesajları kaldırmak için
function removeMessage(messageId) {
    // ID'ye göre mesaj elementini bul
    const message = document.getElementById(messageId);
    // Eğer mesaj bulunduysa sil
    if (message) {
        message.remove();
    }
}

// Sayfa yüklendiğinde input alanına otomatik focus ver
window.addEventListener('load', () => {
    messageInput.focus();
});

