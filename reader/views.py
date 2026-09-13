from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import Book, Chapter
from . import scraper


@login_required
def home(request):
    """Kitap listesi + yeni kitap ekleme formu (sadece isim)."""
    if request.method == "POST":
        title = request.POST.get("book_title", "").strip()
        if not title:
            messages.error(request, "Lütfen bir kitap adı yaz.")
            return redirect("home")

        book = Book.objects.create(title=title)
        messages.success(request, f'"{title}" eklendi. Şimdi bölüm linklerini ekleyebilirsin.')
        return redirect("chapter_list", book_id=book.id)

    books = Book.objects.all()
    return render(request, "reader/home.html", {"books": books})


@login_required
def chapter_list(request, book_id):
    """Bir kitabın bölüm listesi + yeni bölüm (Wattpad linki) ekleme formu."""
    book = get_object_or_404(Book, id=book_id)

    if request.method == "POST":
        url = request.POST.get("chapter_url", "").strip()

        if not url or "wattpad.com" not in url:
            messages.error(request, "Lütfen geçerli bir Wattpad bölüm linki gir.")
            return redirect("chapter_list", book_id=book.id)

        url = scraper.normalize_chapter_url(url)

        if book.chapters.filter(url=url).exists():
            messages.error(request, "Bu bölüm zaten bu kitaba eklenmiş.")
            return redirect("chapter_list", book_id=book.id)

        try:
            data = scraper.get_chapter_content(url)
        except scraper.ScrapeError as exc:
            messages.error(request, str(exc))
            return redirect("chapter_list", book_id=book.id)

        next_order = (book.chapters.count())
        Chapter.objects.create(
            book=book,
            url=url,
            title=data["title"],
            content=data["content"],
            order=next_order,
            fetched_at=timezone.now(),
        )
        messages.success(request, "Bölüm eklendi.")
        return redirect("chapter_list", book_id=book.id)

    return render(request, "reader/chapter_list.html", {"book": book})


@login_required
def chapter_detail(request, chapter_id):
    chapter = get_object_or_404(Chapter, id=chapter_id)

    # Metin henüz çekilmemişse şimdi çekip veritabanında saklıyoruz
    if not chapter.content:
        try:
            data = scraper.get_chapter_content(chapter.url)
            chapter.content = data["content"]
            if not chapter.title:
                chapter.title = data["title"]
            chapter.fetched_at = timezone.now()
            chapter.save()
        except scraper.ScrapeError as exc:
            messages.error(request, str(exc))

    siblings = list(chapter.book.chapters.all())
    idx = siblings.index(chapter) if chapter in siblings else -1
    prev_chapter = siblings[idx - 1] if idx > 0 else None
    next_chapter = siblings[idx + 1] if 0 <= idx < len(siblings) - 1 else None

    return render(request, "reader/chapter_detail.html", {
        "chapter": chapter,
        "prev_chapter": prev_chapter,
        "next_chapter": next_chapter,
    })


@login_required
def refresh_chapter(request, chapter_id):
    """Bölümü yeniden çekmek (örn. ilk seferde hata olduysa)."""
    chapter = get_object_or_404(Chapter, id=chapter_id)
    try:
        data = scraper.get_chapter_content(chapter.url)
        chapter.content = data["content"]
        chapter.title = data["title"] or chapter.title
        chapter.fetched_at = timezone.now()
        chapter.save()
        messages.success(request, "Bölüm güncellendi.")
    except scraper.ScrapeError as exc:
        messages.error(request, str(exc))
    return redirect("chapter_detail", chapter_id=chapter.id)
