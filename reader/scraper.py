"""
Wattpad linklerini okumak icin yardimci fonksiyonlar.

NOT: Wattpad kendi HTML yapisini zaman zaman degistirir. Eger bir sure sonra
okuma calismazsa, en cok ihtimal asagidaki CSS seciciler (selectors)
eskimistir - bu durumda sadece bu dosyayi guncellemek yeterlidir, sitenin
geri kalanina dokunmaya gerek yoktur.

Bu scraper SADECE acik/ucretsiz okunabilen sayfalar icin tasarlanmistir.
Wattpad Premium/ucretli bolumler icin calismayacaktir (ve calismamalidir).
"""
import re
import requests
from bs4 import BeautifulSoup
from django.conf import settings

HEADERS = {
    "User-Agent": getattr(
        settings,
        "SCRAPER_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

STORY_URL_RE = re.compile(r"wattpad\.com/story/(\d+)")
CHAPTER_URL_RE = re.compile(r"wattpad\.com/(\d+)-")


class ScrapeError(Exception):
    """Sayfa cekilirken ya da parse edilirken olusan hata."""


def fetch_html(url: str) -> str:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
    except requests.RequestException as exc:
        raise ScrapeError(f"Sayfaya bağlanılamadı: {exc}") from exc

    if resp.status_code != 200:
        raise ScrapeError(
            f"Wattpad {resp.status_code} kodu döndürdü. Link doğru mu, "
            "yoksa bölüm ücretli (Premium) olabilir."
        )
    return resp.text


def is_story_url(url: str) -> bool:
    return bool(STORY_URL_RE.search(url))


def is_chapter_url(url: str) -> bool:
    """Story linki değilse ve wattpad.com alan adındaysa, bölüm linki kabul ederiz."""
    return "wattpad.com" in url and not is_story_url(url)


def parse_story_page(html: str, story_url: str):
    """
    Story (hikayenin ana) sayfasından başlık, kapak ve bölüm listesini
    çıkarır.

    Return: dict(title, author, cover_url, chapters=[{"url":..., "title":...}, ...])
    """
    soup = BeautifulSoup(html, "html.parser")

    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else "Bilinmeyen kitap"

    author = ""
    author_tag = soup.select_one("a[href*='/user/']")
    if author_tag:
        author = author_tag.get_text(strip=True)

    cover_url = ""
    og_image = soup.find("meta", property="og:image")
    if og_image and og_image.get("content"):
        cover_url = og_image["content"]

    chapters = []
    seen = set()

    # Wattpad TOC (içindekiler) için bilinen birkaç olası seçici
    candidates = soup.select("ul.table-of-contents li a[href]") or \
        soup.select("a.story-parts__part") or \
        soup.select("a[href*='/'][data-page]")

    if not candidates:
        # Fallback: sayfadaki tüm linkler arasından bölüm linki formasına
        # uygun olanları bulmaya çalışırız
        candidates = soup.find_all("a", href=True)

    for a in candidates:
        href = a.get("href", "")
        if not href:
            continue
        if href.startswith("/"):
            href = "https://www.wattpad.com" + href
        if not CHAPTER_URL_RE.search(href):
            continue
        if href in seen:
            continue
        seen.add(href)
        chap_title = a.get_text(strip=True) or f"Bölüm {len(chapters) + 1}"
        chapters.append({"url": href, "title": chap_title})

    if not chapters:
        raise ScrapeError(
            "Bu hikayenin bölüm listesi bulunamadı. Wattpad kendi HTML "
            "yapısını değiştirmiş olabilir (scraper.py güncellenmeli), "
            "ya da bu bir hikaye (story) linki değil - doğrudan bölüm linkini kontrol et."
        )

    return {
        "title": title,
        "author": author,
        "cover_url": cover_url,
        "chapters": chapters,
    }


def _extract_chapter_paragraphs(html: str):
    """
    Tek bir bölüm SAYFASINDAN (page 1, 2, 3 ...) paragrafları çıkarır.
    Wattpad bölüm metni genellikle "panel-reading" class'lı div'lerin
    içindeki <p> etiketlerindedir. Yapı değişirse buradaki seçiciler
    güncellenmelidir.
    """
    soup = BeautifulSoup(html, "html.parser")

    paragraphs = soup.select("div.panel-reading p") or \
        soup.select("div[class*='panel-reading'] p") or \
        soup.select("pre p")

    if not paragraphs:
        # Son fallback: tüm <p> etiketlerini alıp, çok kısa/navigasyon
        # metinlerini filtreleriz
        all_p = soup.find_all("p")
        paragraphs = [p for p in all_p if len(p.get_text(strip=True)) > 30]

    return [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]


def parse_chapter_page(html: str):
    """Tek bir bölüm sayfasından (sadece 1. sayfa) başlık ve metni çıkarır."""
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("h1") or soup.find("h2")
    title = title_tag.get_text(strip=True) if title_tag else ""

    text_parts = _extract_chapter_paragraphs(html)
    if not text_parts:
        raise ScrapeError(
            "Bölüm metni bulunamadı. Bu bölüm Wattpad Premium (ücretli) "
            "olabilir, ya da Wattpad HTML yapısını değiştirmiş olabilir."
        )
    return {"title": title, "content": "\n\n".join(text_parts)}


def get_story_chapters(story_url: str):
    html = fetch_html(story_url)
    return parse_story_page(html, story_url)


def normalize_chapter_url(url: str) -> str:
    """
    Wattpad linkinden '/page/2', '/page/3' gibi sayfa ekini silip bölümün
    ana (1. sayfa) linkini döndürür. Kullanıcı hangi sayfadan linki
    kopyalayıp yapıştırırsa yapıştırsın, aynı bölümü tanımak için kullanılır.
    """
    return re.sub(r"/page/\d+/?$", "", url.rstrip("/"))


def _build_page_url(base_url: str, page: int) -> str:
    if page <= 1:
        return base_url
    return f"{base_url.rstrip('/')}/page/{page}"


def get_chapter_content(chapter_url: str):
    """
    Wattpad bir bölümü TEK bir sayfada vermez - scroll ettikçe link kendisi
    '/page/2', '/page/3' ... şeklinde değişir ve her biri bölümün ayrı bir
    kısmını gösterir. Burada linkin ana kısmını bulup, page=1'den başlayarak,
    artık yeni içerik gelmeyene kadar sırayla tüm sayfaları çekip tek bir
    metinde birleştiriyoruz.
    """
    base_url = normalize_chapter_url(chapter_url)
    title = ""
    all_texts = []
    prev_texts = None
    max_pages = 100  # güvenlik limiti - sonsuz döngünün önüne geçmek için

    for page in range(1, max_pages + 1):
        url = _build_page_url(base_url, page)

        if page == 1:
            # 1. sayfa mevcut olmalı - burada hata olursa, kullanıcıya
            # göstermek için ScrapeError'u yukarı aktarıyoruz
            html = fetch_html(url)
            title_tag = BeautifulSoup(html, "html.parser").find("h1") or \
                BeautifulSoup(html, "html.parser").find("h2")
            title = title_tag.get_text(strip=True) if title_tag else ""
        else:
            # Sonraki sayfalar için 404/hata = "sayfalar bitti" demektir,
            # bu yüzden hatayı yutup döngüyü sessizce durduruyoruz
            try:
                html = fetch_html(url)
            except ScrapeError:
                break

        page_texts = _extract_chapter_paragraphs(html)
        if not page_texts:
            break

        # Wattpad mevcut olmayan bir sayfa için 200 ile ilk sayfayı geri
        # döndürebilir - bunu tespit edip tekrarın önüne geçiyoruz
        if page_texts == prev_texts:
            break

        all_texts.extend(page_texts)
        prev_texts = page_texts

    if not all_texts:
        raise ScrapeError(
            "Bölüm metni bulunamadı. Bu bölüm Wattpad Premium (ücretli) "
            "olabilir, ya da Wattpad HTML yapısını değiştirmiş olabilir."
        )

    return {"title": title, "content": "\n\n".join(all_texts)}
