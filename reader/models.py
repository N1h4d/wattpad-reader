from django.db import models


class Book(models.Model):
    """Kullanıcının kendi eklediği kitap (sadece isim - link gerekmiyor)."""
    title = models.CharField("Kitap adı", max_length=500)
    author = models.CharField("Yazar", max_length=255, blank=True)
    created_at = models.DateTimeField("Eklenme tarihi", auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Kitap"
        verbose_name_plural = "Kitaplar"

    def __str__(self):
        return self.title


class Chapter(models.Model):
    """Kitabın bir bölümü (chapter) - bir Wattpad linkine bağlıdır."""
    book = models.ForeignKey(Book, related_name='chapters', on_delete=models.CASCADE, verbose_name="Kitap")
    url = models.URLField("Wattpad linki", unique=True, help_text="Wattpad bölüm linki")
    title = models.CharField("Bölüm başlığı", max_length=500, blank=True)
    order = models.PositiveIntegerField("Sıra", default=0)
    content = models.TextField("Metin", blank=True, help_text="Çekilmiş bölüm metni")
    fetched_at = models.DateTimeField("Çekilme zamanı", null=True, blank=True)
    added_at = models.DateTimeField("Eklenme tarihi", auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Bölüm"
        verbose_name_plural = "Bölümler"

    def __str__(self):
        return f"{self.book.title} - {self.title or self.url}"

    @property
    def is_fetched(self):
        return bool(self.content)
