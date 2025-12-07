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
HISSE_LISTESI = [
    "THYAO.IS", "ASELS.IS", "GARAN.IS", "AKBNK.IS", "EREGL.IS", 
    "KCHOL.IS", "SAHOL.IS", "TUPRS.IS", "SISE.IS", "BIMAS.IS",
    "PETKM.IS", "YKBNK.IS", "ISCTR.IS", "EKGYO.IS", "KOZAL.IS"
]

def veri_getir_ve_hazirla(hisse_kodu):
    try:
        data = yf.download(hisse_kodu, period="1y", interval="1d", progress=False)
        if len(data) < 60: return None
        
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
    
    rsi_degeri = data['RSI'].iloc[-1]
    if hasattr(rsi_degeri, 'item'): rsi_degeri = rsi_degeri.item()
    
    son_fiyat = data['Close'].iloc[-1]
    if hasattr(son_fiyat, 'item'): son_fiyat = son_fiyat.item()

    return tahmin, olasilik, rsi_degeri, son_fiyat

def mail_gonder(html_icerik):
    GMAIL_USER = os.environ.get('GMAIL_USER')
    GMAIL_PASS = os.environ.get('GMAIL_PASS')
    ALICI_MAIL = os.environ.get('ALICI_MAIL')

    if not GMAIL_USER or not GMAIL_PASS:
        print("Mail bilgileri eksik!")
        return

    msg = MIMEMultipart('alternative')
    msg['From'] = GMAIL_USER
    msg['To'] = ALICI_MAIL
    msg['Subject'] = f"🚀 Borsa AI Raporu (Hotmail) - {datetime.now().strftime('%d.%m.%Y')}"
    
    part = MIMEText(html_icerik, 'html')
    msg.attach(part)

    try:
        # BURASI HOTMAIL (OUTLOOK) SMTP SUNUCUSU
        server = smtplib.SMTP('smtp-mail.outlook.com', 587) 
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, ALICI_MAIL, msg.as_string())
        server.quit()
        print("✅ Mail başarıyla gönderildi!")
    except Exception as e:
        print(f"❌ Mail hatası: {e}")

if __name__ == "__main__":
    print("Analiz başladı...")
    html_rapor = """
    <html><head><style>
        table {border-collapse: collapse; width: 100%; font-family: sans-serif;}
        th, td {padding: 10px; border-bottom: 1px solid #ddd; text-align: left;}
        th {background-color: #04AA6D; color: white;}
    </style></head><body>
    <h2>🤖 Borsa AI Günlük Sinyaller</h2>
    <table><tr><th>Hisse</th><th>Fiyat</th><th>RSI</th><th>Güven %</th></tr>
    """
    
    sinyal_var_mi = False
    for hisse in HISSE_LISTESI:
        df = veri_getir_ve_hazirla(hisse)
        if df is not None:
            tahmin, olasilik, rsi, fiyat = yapay_zeka_tahmin(df)
            if tahmin == 1 and olasilik > 0.60:
                html_rapor += f"<tr><td><b>{hisse}</b></td><td>{fiyat:.2f}</td><td>{rsi:.1f}</td><td>%{int(olasilik*100)}</td></tr>"
                sinyal_var_mi = True
    
    html_rapor += "</table></body></html>"
    
    if sinyal_var_mi:
        mail_gonder(html_rapor)
    else:
        print("Sinyal yok, mail atılmadı.")
