import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime

# --- AYARLAR ---
# Takip edilecek hisseler (İstediğini ekle çıkar)
HISSE_LISTESI = [
    "THYAO.IS", "ASELS.IS", "GARAN.IS", "AKBNK.IS", "EREGL.IS", 
    "KCHOL.IS", "SAHOL.IS", "TUPRS.IS", "SISE.IS", "BIMAS.IS",
    "PETKM.IS", "YKBNK.IS", "ISCTR.IS", "EKGYO.IS", "KOZAL.IS"
]

def veri_getir_ve_hazirla(hisse_kodu):
    try:
        data = yf.download(hisse_kodu, period="1y", interval="1d", progress=False)
        if len(data) < 50: return None
        
        # Teknik İndikatörler
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        data.dropna(inplace=True)
        return data
    except Exception:
        return None

def yapay_zeka_tahmin(data):
    data['Target'] = (data['Close'].shift(-1) > data['Close']).astype(int)
    features = ['SMA_20', 'SMA_50', 'RSI', 'Close', 'Volume']
    X = data[features][:-1]
    y = data['Target'][:-1]
    
    model = RandomForestClassifier(n_estimators=100, min_samples_split=10, random_state=42)
    model.fit(X, y)
    
    son_veri = data[features].iloc[[-1]]
    tahmin = model.predict(son_veri)[0]
    olasilik = model.predict_proba(son_veri)[0][1]
    return tahmin, olasilik

def mail_gonder(icerik):
    GMAIL_USER = os.environ.get('GMAIL_USER')
    GMAIL_PASSWORD = os.environ.get('GMAIL_PASS')
    ALICI_MAIL = os.environ.get('ALICI_MAIL')

    if not GMAIL_USER or not GMAIL_PASSWORD:
        print("Mail bilgileri eksik!")
        return

    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = ALICI_MAIL
    msg['Subject'] = f"Borsa AI Sinyalleri - {datetime.now().strftime('%Y-%m-%d')}"
    msg.attach(MIMEText(icerik, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.sendmail(GMAIL_USER, ALICI_MAIL, msg.as_string())
        server.quit()
        print("Mail gönderildi.")
    except Exception as e:
        print(f"Mail hatası: {e}")

if __name__ == "__main__":
    print("Analiz başladı...")
    rapor = "--- YAPAY ZEKA GÜNLÜK TARAMA ---\n\n"
    sinyal_var_mi = False
    
    for hisse in HISSE_LISTESI:
        df = veri_getir_ve_hazirla(hisse)
        if df is not None:
            tahmin, olasilik = yapay_zeka_tahmin(df)
            if tahmin == 1 and olasilik > 0.60:
                son_fiyat = float(df['Close'].iloc[-1])
                rapor += f"HISSE: {hisse}\nTahmin: YÜKSELİŞ (%{olasilik*100:.0f})\nFiyat: {son_fiyat:.2f}\n------------------\n"
                sinyal_var_mi = True
    
    if not sinyal_var_mi:
        rapor += "Bugün güçlü bir AL sinyali çıkmadı."
        
    mail_gonder(rapor)
