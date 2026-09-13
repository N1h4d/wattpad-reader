"""
Wattpad linklərini oxumaq üçün köməkçi funksiyalar.

QEYD: Wattpad öz HTML strukturunu vaxtaşırı dəyişdirir. Əgər bir müddət sonra
oxuma işləməsə, ən çox ehtimal budur ki, aşağıdakı CSS seçiciləri (selectors)
köhnəlib - bu halda sadəcə bu faylı yeniləmək lazımdır, saytın qalan hissəsinə
toxunmağa ehtiyac yoxdur.

Bu scraper YALNIZ açıq/pulsuz oxuna bilən səhifələr üçün nəzərdə tutulub.
Wattpad Premium/pullu fəsillər üçün işləməyəcək (və işləməməlidir).
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
    """Səhifəni çəkərkən və ya parse edərkən baş verən xəta."""


def fetch_html(url: str) -> str:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
    except requests.RequestException as exc:
        raise ScrapeError(f"Səhifəyə qoşulmaq mümkün olmadı: {exc}") from exc

    if resp.status_code != 200:
        raise ScrapeError(
            f"Wattpad {resp.status_code} kodu qaytardı. Link doğrudurmu, "
            "yoxsa fəsil pullu ola bilər."
        )
    return resp.text


def is_story_url(url: str) -> bool:
    return bool(STORY_URL_RE.search(url))


def is_chapter_url(url: str) -> bool:
    """Story linki deyilsə və wattpad.com domenindədirsə, fəsil linki hesab edirik."""
    return "wattpad.com" in url and not is_story_url(url)


def parse_story_page(html: str, story_url: str):
    """
    Story (hekayənin əsas) səhifəsindən başlıq, üz qabığı və fəsillərin
    siyahısını çıxarır.

    Return: dict(title, author, cover_url, chapters=[{"url":..., "title":...}, ...])
    """
    soup = BeautifulSoup(html, "html.parser")

    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else "Naməlum kitab"

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

    # Wattpad TOC (table of contents) üçün bilinən bir neçə mümkün seçici
    candidates = soup.select("ul.table-of-contents li a[href]") or \
        soup.select("a.story-parts__part") or \
        soup.select("a[href*='/'][data-page]")

    if not candidates:
        # Fallback: səhifədəki bütün linklər arasından fəsil linki formasına
        # uyğun olanları tapmağa çalışırıq
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
        chap_title = a.get_text(strip=True) or f"Fəsil {len(chapters) + 1}"
        chapters.append({"url": href, "title": chap_title})

    if not chapters:
        raise ScrapeError(
            "Bu hekayənin fəsil siyahısı tapılmadı. Wattpad öz HTML "
            "strukturunu dəyişmiş ola bilər (scraper.py yenilənməlidir), "
            "ya da bu bir story linki deyil - birbaşa fəsil linkini yoxlayın."
        )

    return {
        "title": title,
        "author": author,
        "cover_url": cover_url,
        "chapters": chapters,
    }


def _extract_chapter_paragraphs(html: str):
    """
    Tək bir fəsil SƏHİFƏSİNDƏN (page 1, 2, 3 ...) paraqrafları çıxarır.
    Wattpad fəsil mətni adətən "panel-reading" class-lı div-lərin içindəki
    <p> teqlərindədir. Struktur dəyişərsə buradakı seçicilər yenilənməlidir.
    """
    soup = BeautifulSoup(html, "html.parser")

    paragraphs = soup.select("div.panel-reading p") or \
        soup.select("div[class*='panel-reading'] p") or \
        soup.select("pre p")

    if not paragraphs:
        # Son fallback: bütün <p> teqlərini götürüb, çox qısa/naviqasiya
        # mətnlərini süzürük
        all_p = soup.find_all("p")
        paragraphs = [p for p in all_p if len(p.get_text(strip=True)) > 30]

    return [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]


def parse_chapter_page(html: str):
    """Tək bir fəsil səhifəsindən (yalnız 1-ci səhifə) başlıq və mətni çıxarır."""
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("h1") or soup.find("h2")
    title = title_tag.get_text(strip=True) if title_tag else ""

    text_parts = _extract_chapter_paragraphs(html)
    if not text_parts:
        raise ScrapeError(
            "Fəsil mətni tapılmadı. Bu fəsil Wattpad Premium (pullu) ola "
            "bilər, ya da Wattpad HTML strukturunu dəyişib."
        )
    return {"title": title, "content": "\n\n".join(text_parts)}


def get_story_chapters(story_url: str):
    html = fetch_html(story_url)
    return parse_story_page(html, story_url)


def normalize_chapter_url(url: str) -> str:
    """
    Wattpad linkindən '/page/2', '/page/3' kimi səhifə şəkilçisini silib
    fəslin əsas (1-ci səhifə) linkini qaytarır. İstifadəçi hansı səhifədən
    linki kopyalayıb yapışdırsa da, eyni fəsli tanımaq üçün istifadə olunur.
    """
    return re.sub(r"/page/\d+/?$", "", url.rstrip("/"))


def _build_page_url(base_url: str, page: int) -> str:
    if page <= 1:
        return base_url
    return f"{base_url.rstrip('/')}/page/{page}"


def get_chapter_content(chapter_url: str):
    """
    Wattpad bir fəsli TƏK bir səhifədə vermir - sən scroll etdikcə link
    özü '/page/2', '/page/3' ... şəklində dəyişir və hər biri fəslin ayrı
    hissəsini göstərir. Burada linkin əsas hissəsini tapıb, page=1-dən
    başlayaraq, artıq yeni məzmun gəlməyənə qədər ardıcıl bütün səhifələri
    çəkib bir mətndə birləşdiririk.
    """
    base_url = normalize_chapter_url(chapter_url)
    title = ""
    all_texts = []
    prev_texts = None
    max_pages = 100  # təhlükəsizlik limiti - sonsuz dövrün qarşısını almaq üçün

    for page in range(1, max_pages + 1):
        url = _build_page_url(base_url, page)

        if page == 1:
            # 1-ci səhifə mövcud olmalıdır - burada xəta olarsa, istifadəçiyə
            # göstərmək üçün ScrapeError-u ötürürük
            html = fetch_html(url)
            title_tag = BeautifulSoup(html, "html.parser").find("h1") or \
                BeautifulSoup(html, "html.parser").find("h2")
            title = title_tag.get_text(strip=True) if title_tag else ""
        else:
            # Növbəti səhifələr üçün 404/xəta = "səhifələr bitdi" deməkdir,
            # ona görə xətanı udub dövrü sakitcə dayandırırıq
            try:
                html = fetch_html(url)
            except ScrapeError:
                break

        page_texts = _extract_chapter_paragraphs(html)
        if not page_texts:
            break

        # Wattpad mövcud olmayan səhifə üçün 200 ilə birinci səhifəni geri
        # qaytara bilər - bunu aşkarlayıb təkrarın qarşısını alırıq
        if page_texts == prev_texts:
            break

        all_texts.extend(page_texts)
        prev_texts = page_texts

    if not all_texts:
        raise ScrapeError(
            "Fəsil mətni tapılmadı. Bu fəsil Wattpad Premium (pullu) ola "
            "bilər, ya da Wattpad HTML strukturunu dəyişib."
        )

    return {"title": title, "content": "\n\n".join(all_texts)}
