# FastAPI ana uygulama dosyası
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import chat
from app.core.config import settings

# FastAPI uygulaması oluştur
app = FastAPI(title="Weather Chatbot", description="Hava durumu chatbot uygulaması")

# Static dosyaları (CSS, JS) mount et
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Chat router'ını uygulamaya ekle
app.include_router(chat.router)

@app.on_event("startup")
async def startup_event():
    """Uygulama başlarken config kontrolü ve başlangıç mesajları"""
    print(f"Weather API URL: {settings.WEATHER_API_URL}")
    print("Weather Chatbot başlatıldı! (Open-Meteo API - Ücretsiz)")

if __name__ == "__main__":
    # Uygulamayı uvicorn ile çalıştır
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

