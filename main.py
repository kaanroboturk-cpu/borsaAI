import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import gspread 
import os
from datetime import datetime

# --- AYARLAR ---
HISSE_LISTESI = ["THYAO.IS", "ASELS.IS", "GARAN.IS", "AKBNK.IS", "EREGL.IS", 
                "KCHOL.IS", "SAHOL.IS", "TUPRS.IS", "SISE.IS", "BIMAS.IS"]
SHEET_ADI = "ROBOT_RAPOR" 

# --- TEKNİK FONKSİYONLAR (Aynı Kalıyor) ---
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


# GÜNCELLENEN FONKSİYON: TEK KAYIT YAZAR
def sheets_rapor_gonder(rapor_df):
    try:
        service_account_info = os.environ.get('G_SERVICE_ACCOUNT')
        if not service_account_info: return
        
        gc = gspread.service_account_from_dict(eval(service_account_info))
        sh = gc.open(SHEET_ADI)
        worksheet = sh.get_worksheet(0) 

        # MÜKERRER KAYIT ENGELİ
        worksheet.clear(start='A2') 

        simdi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # SÜTUNLAR: DANIŞMAN_NOTU ile eylem planı sunulacak
        sutun_sirasi = ['Tarih', 'Hisse', 'EYLEM', 'Güven_%', 'RSI', 'Fiyat', 'DANIŞMAN_NOTU']
        rapor_df.insert(0, 'Tarih', simdi)
        rapor_df = rapor_df.reindex(columns=sutun_sirasi)


        if worksheet.row_count < 1 or worksheet.cell(1, 1).value != 'Tarih':
            worksheet.append_row(rapor_df.columns.tolist(), value_input_option='USER_ENTERED')
        
        worksheet.append_rows(rapor_df.values.tolist(), value_input_option='USER_ENTERED')
        
        print(f"✅ Rapor başarıyla Google Sheets'e ({SHEET_ADI}) yazıldı!")

    except Exception as e:
        print(f"❌ SHEETS YAZMA HATASI: {e}")


if __name__ == "__main__":
    print("Analiz başladı...")
    
    sinyal_listesi = []
    
    for hisse in HISSE_LISTESI:
        df = veri_getir_ve_hazirla(hisse)
        if df is not None:
            tahmin, olasilik, rsi, fiyat = yapay_zeka_tahmin(df)
            
            # Sadece %60 üzeri güçlü sinyal varsa raporla
            if tahmin == 1 and olasilik > 0.60:
                eylem = 'AL SİNYALİ'
                
                # --- DANIŞMAN NOTU LOGİĞİ ---
                if olasilik > 0.85: # %85 ve üzeri: Maksimum Güven
                    eylem = 'ÇOK GÜÇLÜ AL'
                    not_metni = "🔥🔥🔥 YÜKSEK ÖNCELİK: Robotun güveni %85 üzerindedir. Piyasa açılışında alım fırsatını kaçırmayın."
                elif olasilik > 0.70: # %70-85 arası: Güçlü Güven
                    eylem = 'GÜÇLÜ AL' 
                    not_metni = "🚨 Robot YÜKSEK GÜVEN ile AL sinyali veriyor. Alım emri değerlendirilebilir. (Ortadan Yüksek Risk)"
                else: # %60-70 arası: Orta Güven
                    eylem = 'AL SİNYALİ'
                    not_metni = "Robot sinyal veriyor ancak risk yüksektir. Kendi analizini yaptıktan sonra ALIM hacmini düşük tutarak değerlendir."
                
                if rsi < 50:
                    not_metni += " **(Fiyat uygun, RSI alım bölgesinde).**"
                else:
                    not_metni += " (RSI 50 üzeri: Fiyat yükselişte, dikkatli olun)."
                
                sinyal_listesi.append({
                    'Hisse': hisse.replace('.IS', ''),
                    'Fiyat': f"{fiyat:.2f}",
                    'RSI': f"{rsi:.1f}",
                    'Güven_%': f"{int(olasilik * 100)}",
                    'EYLEM': eylem,
                    'DANIŞMAN_NOTU': not_metni # YENİ AÇIKLAMA SÜTUNU
                })

    if sinyal_listesi:
        rapor_df = pd.DataFrame(sinyal_listesi)
        sheets_rapor_gonder(rapor_df)
    else:
        bos_df = pd.DataFrame([{'Hisse': '', 'EYLEM': 'BEKLEME', 'Güven_%': '', 'RSI': '', 'Fiyat': '', 'DANIŞMAN_NOTU': 'Piyasada yüksek güvenle önerebileceğim bir alım fırsatı bulunmamaktadır. Yeni sinyal için beklemede kalın.'}])
        sheets_rapor_gonder(bos_df)
        print("Güçlü al sinyali bulunamadı. Sheets'e rapor yazılmadı.")
