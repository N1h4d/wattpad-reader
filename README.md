# Okuma Sitem — Wattpad Reader (Django)

Kişisel kullanım için: sadece giriş (kayıt olma yok), giriş yaptıktan sonra
önce bir kitap adı ekliyorsun, sonra o kitabın içine bölüm bölüm Wattpad
linkleri ekleyip kendi tasarımında okuyorsun.

## Nasıl çalışır
- Sitede kayıt (sign up) yok. Kullanıcıları **sadece sen** `/admin/`
  panelinden oluşturursun.
- Giriş yaptıktan sonra anasayfada bir kitap adı yazıyorsun (örn. "Cehennem").
- Kitaba tıklayınca içine girip Wattpad bölüm linklerini tek tek ekliyorsun -
  her link otomatik olarak o kitabın altına, sırayla ekleniyor.
- Bölüme tıklayınca metni okuyorsun. Altında **Önceki Bölüm / Sonraki Bölüm**
  butonları ve ortada **Kitap Kataloğuna Dön** butonu var - anasayfaya geri
  dönmene gerek kalmadan bölümler arası geçiş yapabilirsin.
- Çekilen bölüm metinleri veritabanında saklanır, tekrar internete gitmez.
- Wattpad bir bölümü tek sayfada değil, `/page/2`, `/page/3`... şeklinde
  parça parça verdiği için, scraper bu sayfaların hepsini otomatik olarak
  gezip birleştirir.

## Kurulum

```bash
# 1) Virtual environment (önerilir)
python3 -m venv venv
source venv/bin/activate        # Windows'ta: venv\Scripts\activate

# 2) Paketleri kur
pip install -r requirements.txt

# 3) Veritabanını oluştur
python manage.py migrate

# 4) Kendin için kullanıcı oluştur (sitedeki TEK giriş yolu bu olacak)
python manage.py createsuperuser
# Kullanıcı adı ve şifre soracak

# 5) Sunucuyu başlat
python manage.py runserver
```

Sonra tarayıcıda: `http://127.0.0.1:8000/` — seni otomatik `/login/`-a yönlendirecek.

`/admin/` adresinden (oluşturduğun superuser ile) yeni kullanıcılar
ekleyebilirsin (Users → Add user). Sadece giriş yapabilecek bir kullanıcı
için "staff status" işaretlemene gerek yok, sadece login yeterli.

## Önemli notlar

- **Sadece açık/ücretsiz okunan Wattpad sayfaları için çalışır.** Wattpad
  Premium (ücretli) bölümler için metin çekilmeyecek - bu bilerek böyle.
- Wattpad kendi site yapısını (HTML class isimlerini) zaman zaman değiştirir.
  Bir gün "Bölüm metni bulunamadı" hatası görürsen, sorun `reader/scraper.py`
  dosyasındaki CSS seçicilerinin (selectors) eskimesindedir - tarayıcıda
  "Inspect element" ile yeni yapıya bakıp o dosyayı güncellemek yeterli.
  Kodun geri kalanına dokunmana gerek yok.
- `DEBUG = True` ve `SECRET_KEY` şu anki haliyle geliştirme (development)
  içindir. Siteyi kendi sunucuna/domainine çıkarıp internetten erişilebilir
  yapacaksan:
  - `settings.py`'da `DEBUG = False` yap,
  - `ALLOWED_HOSTS`'a kendi domainini/IP'ni ekle,
  - `SECRET_KEY`'i değiştir ve gizli tut (örn. environment variable ile),
  - HTTPS arkasında çalıştır (örn. Nginx + Let's Encrypt).
- Bu proje tamamen kişisel kullanım içindir; başkasının içeriğini toplu
  şekilde indirip paylaşmak için kullanılmamalıdır.

## Dosya yapısı

```
wattpad_reader/
├── manage.py
├── requirements.txt
├── wattpad_reader/        # proje ayarları (settings, urls)
└── reader/                # ana app
    ├── models.py          # Book, Chapter modelleri
    ├── scraper.py         # Wattpad'dan metin çeken fonksiyonlar
    ├── views.py           # login_required görünümler
    ├── urls.py
    ├── admin.py
    └── templates/reader/  # login, anasayfa, bölüm listesi, okuma sayfası
```

