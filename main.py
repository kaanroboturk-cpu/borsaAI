import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import gspread
import os
from datetime import datetime
# PARALEL İŞLEME İÇİN GEREKLİ KÜTÜPHANE
from concurrent.futures import ThreadPoolExecutor

# --- AYARLAR ---
# ⚠️ ÇEŞİTLENDİRİLMİŞ 100 HİSSELİK LİSTE
HISSE_LISTESI = [
    # HAVACILIK, TURİZM VE TAŞIMACILIK
    "THYAO.IS", "PGSUS.IS", "TAVHL.IS", "ULUUN.IS", 
    # BANKACILIK ve FİNANS
    "GARAN.IS", "AKBNK.IS", "ISCTR.IS", "YKBNK.IS", "HALKB.IS", 
    "VAKBN.IS", "TSKB.IS", 
    # HOLDİNGLER
    "KCHOL.IS", "SAHOL.IS", "AEFES.IS", "DOHOL.IS", "AGHOL.IS", 
    "ENJSA.IS", 
    # SANAYİ VE OTOMOTİV
    "FROTO.IS", "TOASO.IS", "DOAS.IS", "EREGL.IS", "KRDMD.IS", 
    "TTRAK.IS", "BRSAN.IS", "EGEEN.IS", 
    # PERAKENDE VE GIDA
    "BIMAS.IS", "MGROS.IS", "ULKER.IS", "BIZIM.IS", "PETUN.IS", 
    "KONYA.IS", "CIMSA.IS", "BUCIM.IS", 
    # TEKNOLOJİ VE YAZILIM
    "ASELS.IS", "VESTL.IS", "ARCLK.IS", "TCELL.IS", "TTKOM.IS", 
    "LOGO.IS", "NETAS.IS", "KONTR.IS", "GESAN.IS", 
    # ENERJİ VE MADEN
    "TUPRS.IS", "PETKM.IS", "KOZAL.IS", "GUBRF.IS", "AYDEM.IS", 
    "ODAS.IS", "ZOREN.IS", "AKSA.IS", 
    # İLAÇ VE KİMYA
    "SISE.IS", "SASA.IS", "HEKTS.IS", "DEVA.IS", "ECILC.IS", 
    # GAYRİMENKUL VE İNŞAAT
    "ENKA.IS", "EGYO.IS", "OZKGY.IS", "TRGYO.IS", "POLHO.IS", 
    # DİĞER (Çeşitliliği artıranlar ve 100'e tamamlama)
    "MAVI.IS", "PRKME.IS", "GOLTS.IS", "CUSAN.IS", "MRSHL.IS", 
    "VERUS.IS", "SARKY.IS", "GLYHO.IS", "AVOD.IS", "ANACM.IS", 
    "TKFEN.IS", "YATAS.IS", "GSDHO.IS", "ICBCB.IS", "KLGYO.IS",
    "MIPAZ.IS", "NUGYO.IS", "QNBFB.IS", "RYGYO.IS", "SELGD.IS",
    "ULAS.IS", "AKGRT.IS", "AKSGY.IS", "AYGAZ.IS", "ERBOS.IS",
    "FMIZP.IS", "GARFA.IS", "NTHOL.IS", "OTKAR.IS", "OZBAL.IS",
    "SKBNK.IS", "SNGYO.IS", "SELEC.IS", "BRLSM.IS", "KORDS.IS",
    "KOZAL.IS", "YAPRK.IS", "BJKAS.IS", "FENER.IS", "GOODY.IS"
]

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
        # Hangi hisseye ait olduğunu belirtmek için bir tuple olarak döndürülür
        return (hisse_kodu, data)
    except Exception:
        return (hisse_kodu, None)

def yapay_zeka_tahmin(data):
    data['Target'] = (data['Close'].shift(-1) > data['Close']).astype(int)
    features = ['SMA_20', 'SMA_50', 'RSI', 'Close', 'Volume']
    
    # Random Forest modeli eğitimi
    X = data[features][:-1]
    y = data['Target'][:-1]
    
    model = RandomForestClassifier(n_estimators=100, min_samples_split=10, random_state=42)
    model.fit(X, y)
    
    # Son gün tahmini
    son_veri = data[features].iloc[[-1]]
    tahmin = model.predict(son_veri)[0]
    olasilik = model.predict_proba(son_veri)[0][1]
    
    # Rapor için değerleri çek
    rsi_degeri = data['RSI'].iloc[-1].item() if hasattr(data['RSI'].iloc[-1], 'item') else data['RSI'].iloc[-1]
    son_fiyat = data['Close'].iloc[-1].item() if hasattr(data['Close'].iloc[-1], 'item') else data['Close'].iloc[-1]

    return tahmin, olasilik, rsi_degeri, son_fiyat


# GÜNCELLENEN FONKSİYON: HATASIZ TEMİZLEME
def sheets_rapor_gonder(rapor_df):
    try:
        service_account_info = os.environ.get('G_SERVICE_ACCOUNT')
        if not service_account_info: 
            print("❌ HATA: G_SERVICE_ACCOUNT ortam değişkeni bulunamadı. Google Sheets'e yazılamadı.")
            return
        
        gc = gspread.service_account_from_dict(eval(service_account_info))
        sh = gc.open(SHEET_ADI)
        worksheet = sh.get_worksheet(0) 

        # Önceki verileri temizle
        worksheet.delete_rows(2, 1000)

        simdi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        sutun_sirasi = ['Tarih', 'Hisse', 'EYLEM', 'Güven_%', 'RSI', 'Fiyat', 'DANIŞMAN_NOTU']
        rapor_df.insert(0, 'Tarih', simdi)
        rapor_df = rapor_df.reindex(columns=sutun_sirasi)

        # Başlık satırını kontrol et ve ekle
        if worksheet.row_count < 1 or worksheet.cell(1, 1).value != 'Tarih':
            worksheet.append_row(rapor_df.columns.tolist(), value_input_option='USER_ENTERED')
        
        # Yeni verileri ekle
        worksheet.append_rows(rapor_df.values.tolist(), value_input_option='USER_ENTERED')
        
        print(f"✅ Rapor başarıyla Google Sheets'e ({SHEET_ADI}) yazıldı! ({len(rapor_df)} sinyal)")

    except Exception as e:
        print(f"❌ SHEETS YAZMA HATASI: {e}")


# --- ANA ÇALIŞMA BLOĞU (PARALEL) ---
if __name__ == "__main__":
    
    print(f"Analiz başladı. Toplam {len(HISSE_LISTESI)} hisse paralel olarak inceleniyor...")
    
    sinyal_listesi = []
    
    # ThreadPoolExecutor ile Paralel İşlemeyi Başlat
    # max_workers=10, aynı anda 10 farklı hissenin verisinin çekilip analiz edileceği anlamına gelir.
    with ThreadPoolExecutor(max_workers=10) as executor:
        
        # Her hisse için veri çekme ve hazırlama görevini paralel olarak çalıştır
        results = executor.map(veri_getir_ve_hazirla, HISSE_LISTESI)
        
        # Sonuçları işlemeye başla
        for hisse_kodu, df in results:
            if df is not None:
                try:
                    tahmin, olasilik, rsi, fiyat = yapay_zeka_tahmin(df)
                    
                    # Sadece %60 üzeri güçlü AL sinyali varsa raporla
                    if tahmin == 1 and olasilik > 0.60:
                        
                        # --- DANIŞMAN NOTU VE EYLEM BELİRLEME ---
                        if olasilik > 0.85:
                            eylem = 'ÇOK GÜÇLÜ AL'
                            not_metni = "🔥🔥🔥 YÜKSEK ÖNCELİK: Robotun güveni %85 üzerindedir. Piyasa açılışında alım fırsatını kaçırmayın."
                        elif olasilik > 0.70:
                            eylem = 'GÜÇLÜ AL' 
                            not_metni = "🚨 Robot YÜKSEK GÜVEN ile AL sinyali veriyor. Alım emri değerlendirilebilir. (Ortadan Yüksek Risk)"
                        else:
                            eylem = 'AL SİNYALİ'
                            not_metni = "Robot sinyal veriyor ancak risk yüksektir. Kendi analizini yaptıktan sonra ALIM hacmini düşük tutarak değerlendir."
                        
                        if rsi < 50:
                            not_metni += " (Fiyat uygun, RSI alım bölgesinde)."
                        else:
                            not_metni += " (RSI 50 üzeri: Fiyat yükselişte, dikkatli olun)."
                        
                        sinyal_listesi.append({
                            'Hisse': hisse_kodu.replace('.IS', ''),
                            'Fiyat': f"{fiyat:.2f}",
                            'RSI': f"{rsi:.1f}",
                            'Güven_%': f"{int(olasilik * 100)}",
                            'EYLEM': eylem,
                            'DANIŞMAN_NOTU': not_metni 
                        })
                except Exception as e:
                    print(f"Hata oluştu {hisse_kodu} analizi sırasında: {e}")

    # Raporlama kısmını çalıştır
    if sinyal_listesi:
        rapor_df = pd.DataFrame(sinyal_listesi)
        sheets_rapor_gonder(rapor_df)
    else:
        # Eğer sinyal yoksa, Sheets'e BEKLEME raporu gönder
        bos_df = pd.DataFrame([{'Hisse': '', 'EYLEM': 'BEKLEME', 'Güven_%': '', 'RSI': '', 'Fiyat': '', 'DANIŞMAN_NOTU': 'Piyasada yüksek güvenle önerebileceğim bir alım fırsatı bulunmamaktadır. Yeni sinyal için beklemede kalın.'}])
        sheets_rapor_gonder(bos_df)
        print("Güçlü al sinyali bulunamadı. Sheets'e rapor yazıldı (Bekleme).")
