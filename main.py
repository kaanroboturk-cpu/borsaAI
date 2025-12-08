import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import gspread 
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# --- AYARLAR ---
# ⚠️ Hatalı hisse kodları temizlendi ve liste tekrar yüklendi.
HISSE_LISTESI = [
    # BİST TEMEL VE MAVİ CHİPLER
    "THYAO.IS", "PGSUS.IS", "TAVHL.IS", "KCHOL.IS", "SAHOL.IS", "AEFES.IS", "DOHOL.IS", 
    "AGHOL.IS", "FROTO.IS", "TOASO.IS", "DOAS.IS", "EREGL.IS", "KRDMD.IS", "TUPRS.IS", 
    "SISE.IS", "BIMAS.IS", "MGROS.IS", "ULKER.IS", "ARCLK.IS", "TCELL.IS", "TTKOM.IS", 
    "ENKA.IS", "KOZAL.IS", "GUBRF.IS", "GARAN.IS", "AKBNK.IS", "ISCTR.IS", "YKBNK.IS", 
    "HALKB.IS", "VAKBN.IS", "TSKB.IS", "AYDEM.IS", "ZOREN.IS", "AKSA.IS", "PETKM.IS", 
    "SASA.IS", "HEKTS.IS", "DEVA.IS", "ECILC.IS", "CIMSA.IS", "BUCIM.IS", "MAVI.IS",
    "ASELS.IS", "VESTL.IS", "KONTR.IS", "GESAN.IS", "ASTOR.IS", "ENJSA.IS", "ODAS.IS", 
    "ANELE.IS", "KARYE.IS", "ALARK.IS", "CELHA.IS", "SMRTG.IS", "TRGYO.IS",
    # Genişletilmiş BIST 100/300/500+ Hisseleri (OZKGYO.IS gibi hatalı kodlar listeden çıkarıldı.)
    "QNBFL.IS", "SKBNK.IS", "ICBCB.IS", "AKGRT.IS", "GARFA.IS", "IHLAS.IS", "ISFIN.IS",
    "DEVAR.IS", "FINBN.IS", "GSDDE.IS", "VAKFN.IS", "TSGYO.IS", "AKCNS.IS", "ALGYO.IS", 
    "DENGE.IS", "ERSU.IS", "GENTS.IS", "HALKS.IS", "HURGZ.IS", "KLNMA.IS", "LIDER.IS", 
    "MNDRS.IS", "PAGYO.IS", "QUAGR.IS", "RTALB.IS", "TURSG.IS", "YUNSA.IS", "ANHYT.IS",
    "BJKAS.IS", "FENER.IS", "GOODY.IS", "ADANA.IS", "AKMGY.IS", "BERA.IS", "BEYAZ.IS", 
    "CUSAN.IS", "ULAS.IS", "VERUS.IS", "YAPRK.IS", "YKSLN.IS", "MRSHL.IS", "PRKME.IS", 
    "AVOD.IS", "ANACM.IS", "TKFEN.IS", "KLGYO.IS", "QNBFB.IS", "ERBOS.IS", "NTHOL.IS", 
    "BRLSM.IS", "KORDS.IS", "ADESE.IS", "ALCTL.IS", "BASCM.IS", "CRDFA.IS", "DMSAS.IS",
    "EUKYO.IS", "FLAP.IS", "KRONT.IS", "KUYAS.IS", "MACKO.IS", "OSTIM.IS", "SAFKR.IS",
    "SEKFK.IS", "SNFR.IS", "TACTR.IS", "TEKTU.IS", "TRILC.IS", "UNLU.IS", "USAK.IS",
    "VANGD.IS", "YGYO.IS", "ACSEL.IS", "AKSEL.IS", "BALAT.IS", "BOBET.IS", "BRKSN.IS",
    "CELHA.IS", "DARDL.IS", "DEVA.IS", "DMSAS.IS", "ETILR.IS", "FRIGO.IS", "GSDMA.IS",
    "HUBVC.IS", "METRO.IS", "MMCAS.IS", "NETAS.IS", "OSTIM.IS", "RYGYO.IS", "TACTR.IS",
    "TEKTU.IS", "TRILC.IS", "VANGD.IS", "VAKFN.IS", "VERUS.IS", "YATAS.IS", "YKSLN.IS",
    "YUNSA.IS", "ZOREN.IS", "ADATR.IS", "AFYON.IS", "AKCNS.IS", "AKMGY.IS", "AKSA.IS", 
    "ALCTL.IS", "ANELT.IS", "ANSGR.IS", "ARCLK.IS", "ARDYZ.IS", "AVOD.IS", "AYEN.IS", 
    "AYGAZ.IS", "BAGFS.IS", "BEYAZ.IS", "BJKAS.IS", "BRKSN.IS", "BUCIM.IS", "CEMAS.IS", 
    "CEMTS.IS", "CIMSA.IS", "CLEBI.IS", "DEVA.IS", "DITAS.IS", "DMSAS.IS", "DOAS.IS", 
    "EGEEN.IS", "EKGYO.IS", "ENJSA.IS", "EREGL.IS", "ERIKC.IS", "ERSU.IS", "ESEN.IS", 
    "ETILR.IS", "FENER.IS", "FMIZP.IS", "GARAN.IS", "GENTS.IS", "GOODY.IS", "GOLTS.IS", 
    "GSDHO.IS", "GUBRF.IS", "HEKTS.IS", "IHLAS.IS", "IHLGM.IS", "INDES.IS", "ISCTR.IS", 
    "KAFEZ.IS", "KARTN.IS", "KCHOL.IS", "KENT.IS", "KERVN.IS", "KLNMA.IS", "KORDS.IS", 
    "KOZAL.IS", "KRONT.IS", "KUYAS.IS", "LIDER.IS", "MNDRS.IS", "MPARK.IS", "MRSHL.IS", 
    "NTHOL.IS", "NUGYO.IS", "OTKAR.IS", "OZBAL.IS", "PAGYO.IS", "PETKM.IS", "POLHO.IS", 
    "PRKME.IS", "QNBFB.IS", "RTALB.IS", "SAHOL.IS", "SARKY.IS", "SASA.IS", "SELEC.IS", 
    "SKBNK.IS", "SNGYO.IS", "TATGD.IS", "TAVHL.IS", "TCELL.IS", "TEKTU.IS", "TETMT.IS", 
    "THYAO.IS", "TKFEN.IS", "TOASO.IS", "TRILC.IS", "TSKB.IS", "TUPRS.IS", "ULUUN.IS", 
    "UNLU.IS", "USAK.IS", "VANGD.IS", "VAKBN.IS", "VESTL.IS", "YKBNK.IS", "YKSLN.IS", 
    "YUNSA.IS", "ZOREN.IS"
]


SHEET_ADI = "ROBOT_RAPOR" 

# --- TEKNİK FONKSİYONLAR ---
# Düzeltildi: Hatalı return ifadesi temizlendi.
def veri_getir_ve_hazirla(hisse_kodu):
    try:
        data = yf.download(hisse_kodu, period="1y", interval="1d", progress=False)
        if len(data) < 60: return (hisse_kodu, None) # Tek ve doğru dönüş
        
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        data.dropna(inplace=True)
        return (hisse_kodu, data)
    except Exception:
        return (hisse_kodu, None)

def yapay_zeka_tahmin(data):
    data['Target'] = (data['Close'].shift(-1) > data['Close']).astype(int)
    features = ['SMA_20', 'SMA_50', 'RSI', 'Close', 'Volume']
    model = RandomForestClassifier(n_estimators=100, min_samples_split=10, random_state=42)
    
    # Düzeltildi: Eğitim tek bir satırda yapılıyor.
    model.fit(data[features][:-1], data['Target'][:-1])
    
    son_veri = data[features].iloc[[-1]]
    tahmin = model.predict(son_veri)[0]
    
    olasilik_dizi = model.predict_proba(son_veri)[0] 
    olasilik_AL = olasilik_dizi[1] 
    olasilik_SAT = olasilik_dizi[0] 
    rsi_degeri = data['RSI'].iloc[-1].item() if hasattr(data['RSI'].iloc[-1], 'item') else data['RSI'].iloc[-1]
    son_fiyat = data['Close'].iloc[-1].item() if hasattr(data['Close'].iloc[-1], 'item') else data['Close'].iloc[-1]
    
    # Yeni Kontrol Değerleri (Çift Onay İçin)
    sma20_son = data['SMA_20'].iloc[-1].item() if hasattr(data['SMA_20'].iloc[-1], 'item') else data['SMA_20'].iloc[-1]
    sma50_son = data['SMA_50'].iloc[-1].item() if hasattr(data['SMA_50'].iloc[-1], 'item') else data['SMA_50'].iloc[-1]
    
    return tahmin, olasilik_AL, olasilik_SAT, rsi_degeri, son_fiyat, sma20_son, sma50_son

def sheets_rapor_gonder(rapor_df):
    try:
        service_account_info = os.environ.get('G_SERVICE_ACCOUNT')
        if not service_account_info: return
        gc = gspread.service_account_from_dict(eval(service_account_info))
        sh = gc.open(SHEET_ADI)
        worksheet = sh.get_worksheet(0) 
        
        worksheet.delete_rows(2, 1000)
        
        simdi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sutun_sirasi = ['Tarih', 'Hisse', 'EYLEM', 'Güven_%', 'Fiyat', 'HEDEF_FIYAT', 'STOP_LOSS', 'RSI', 'DANIŞMAN_NOTU']
        rapor_df.insert(0, 'Tarih', simdi)
        rapor_df = rapor_df.reindex(columns=sutun_sirasi)
        
        if worksheet.row_count < 1 or worksheet.cell(1, 1).value != 'Tarih':
            worksheet.append_row(rapor_df.columns.tolist(), value_input_option='USER_ENTERED')
        worksheet.append_rows(rapor_df.values.tolist(), value_input_option='USER_ENTERED')
        print(f"✅ Rapor başarıyla Google Sheets'e ({SHEET_ADI}) yazıldı! ({len(rapor_df)} sinyal)")
    except Exception as e:
        print(f"❌ SHEETS YAZMA HATASI: {e}")


# --- ANA ÇALIŞMA BLOĞU (ÇİFT ONAY VE %85 FİLTRE) ---
if __name__ == "__main__":
    
    print(f"Analiz başladı. Toplam {len(HISSE_LISTESI)} hisse paralel olarak inceleniyor...")
    
    sinyal_listesi = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(veri_getir_ve_hazirla, HISSE_LISTESI)
        
        for hisse_kodu, df_tuple in results:
            if df_tuple is None:
                continue

            hisse_kodu, df = df_tuple
            
            if df is not None:
                try:
                    # Düzeltildi: yapay_zeka_tahmin doğru sayıda değer döndürüyor
                    tahmin, olasilik_AL, olasilik_SAT, rsi, fiyat, sma20, sma50 = yapay_zeka_tahmin(df)

                    hisse_kisa = hisse_kodu.replace('.IS', '')
                    
                    hedef_fiyat = 0
                    stop_loss = 0
                    
                    # --- AL SİNYALİ KONTROLÜ ---
                    if tahmin == 1 and olasilik_AL >= 0.85 and fiyat > sma50 and sma20 > sma50: 
                        olasilik = olasilik_AL 

                        stop_loss = fiyat * 0.97 
                        
                        eylem = 'ÇOK GÜÇLÜ AL'
                        hedef_fiyat = fiyat * 1.12 
                        not_metni = f"🔥🔥🔥 ROBOT ALARMI (Çift Onaylı): Güven %85 üzeri. TREND ve MOMENTUM ONAYI alındı. Özel Emir için önerilen kâr marjı: %12."
                        
                        if rsi < 50:
                            not_metni += " (RSI: Fiyat uygun, alım bölgesi)."
                        else:
                            not_metni += " (RSI: Momentum güçlü, trend devam)."

                        sinyal_listesi.append({
                            'Hisse': hisse_kisa,
                            'Fiyat': f"{fiyat:.2f}",
                            'RSI': f"{rsi:.1f}",
                            'Güven_%': f"{int(olasilik * 100)}",
                            'EYLEM': eylem,
                            'HEDEF_FIYAT': f"{hedef_fiyat:.2f}",
                            'STOP_LOSS': f"{stop_loss:.2f}",
                            'DANIŞMAN_NOTU': not_metni 
                        })

                    # --- SAT SİNYALİ KONTROLÜ ---
                    elif tahmin == 0 and olasilik_SAT >= 0.85 and fiyat < sma50 and sma20 < sma50: 
                        olasilik = olasilik_SAT 
                        
                        eylem = 'ACİL SAT'
                        not_metni = "🛑🛑🛑 ACİL DURUM (Çift Onaylı): Robot, %85+ düşüş sinyali veriyor. TREND ve MOMENTUM ONAYI alındı. Eldeki pozisyonlar için hemen SATIŞ emri değerlendirin."
                        
                        if rsi > 70:
                            not_metni += " (RSI 70 üzeri: Aşırı ALIM bölgesinden düşüş onayı güçlü)."

                        sinyal_listesi.append({
                            'Hisse': hisse_kisa,
                            'Fiyat': f"{fiyat:.2f}",
                            'RSI': f"{rsi:.1f}",
                            'Güven_%': f"{int(olasilik * 100)}",
                            'EYLEM': eylem,
                            'HEDEF_FIYAT': "POZ. KAPAT", 
                            'STOP_LOSS': "POZ. KAPAT",
                            'DANIŞMAN_NOTU': not_metni 
                        })


                except Exception as e:
                    print(f"Hata oluştu {hisse_kodu} analizi sırasında: {e}")

    if sinyal_listesi:
        rapor_df = pd.DataFrame(sinyal_listesi)
        sheets_rapor_gonder(rapor_df)
    else:
        bos_df = pd.DataFrame([{'Hisse': '---', 'EYLEM': 'BEKLEME', 'Güven_%': '---', 'RSI': '---', 'Fiyat': '---', 'HEDEF_FIYAT': '---', 'STOP_LOSS': '---', 'DANIŞMAN_NOTU': 'Piyasada robotun ÇİFT ONAY (%85+ güven ve teknik trend) gerektiren bir eylem planı bulunmamaktadır.'}])
        sheets_rapor_gonder(bos_df)
        print("Yüksek güvenli al veya sat sinyali bulunamadı. Sheets'e rapor yazıldı (Bekleme).")
