import smtplib
import os

# GitHub Secrets'tan bilgileri çek
kullanici = os.environ.get('GMAIL_USER')
sifre = os.environ.get('GMAIL_PASS')

print("--- BAĞLANTI TESTİ BAŞLIYOR ---")

# 1. Bilgiler kodun eline ulaşıyor mu?
if not kullanici:
    print("HATA: Mail adresi (GMAIL_USER) boş geliyor! Secrets ayarı okunamadı.")
elif not sifre:
    print("HATA: Şifre (GMAIL_PASS) boş geliyor! Secrets ayarı okunamadı.")
else:
    print(f"Mail Adresi Algılandı: {kullanici}")
    print(f"Şifre Karakter Sayısı: {len(sifre)} (Olması gereken: 16)")

    # 2. Boşluk kontrolü
    if " " in sifre:
        print("UYARI: Şifrenin içinde BOŞLUK var! Google boşluklu şifreyi kabul etmez.")
        print("Lütfen Secrets kısmından şifreyi silip boşluksuz yapıştır.")
        # Otomatik düzeltmeyi dener
        sifre = sifre.replace(" ", "")
        print("Otomatik düzeltme denendi, boşluklar silindi...")

    # 3. Google'a Bağlanmayı Dene
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(kullanici, sifre)
        print("✅ BAŞARILI: Google şifreyi kabul etti! Giriş yapıldı.")
        server.quit()
    except Exception as e:
        print(f"❌ BAŞARISIZ: Google yine reddetti. Hata detayı:\n{e}")

print("--- TEST BİTTİ ---")
