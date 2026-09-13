from django.db import models


class Book(models.Model):
    """Kullanıcının kendi eklediği kitap (sadece isim - link gerekmiyor)."""
    title = models.CharField("Kitap adı", max_length=500)
    author = models.CharField("Yazar", max_length=255, blank=True)
    created_at = models.DateTimeField("Eklenme tarihi", auto_now_add=True)

    # --- Okuma ilerlemesi (nereden devam edileceği) ---
    last_chapter = models.ForeignKey(
        'Chapter', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='+', verbose_name="Kaldığın bölüm",
    )
    last_read_at = models.DateTimeField(
        "Son okuma zamanı", null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Kitap"
        verbose_name_plural = "Kitaplar"

    def __str__(self):
        return self.title


class Chapter(models.Model):
    """Kitabın bir bölümü (chapter) - bir Wattpad linkine bağlıdır."""
    book = models.ForeignKey(
        Book, related_name='chapters', on_delete=models.CASCADE, verbose_name="Kitap")
    url = models.URLField("Wattpad linki", unique=True,
                          help_text="Wattpad bölüm linki")
    title = models.CharField("Bölüm başlığı", max_length=500, blank=True)
    order = models.PositiveIntegerField("Sıra", default=0)
    content = models.TextField(
        "Metin", blank=True, help_text="Çekilmiş bölüm metni")
    fetched_at = models.DateTimeField("Çekilme zamanı", null=True, blank=True)
    added_at = models.DateTimeField("Eklenme tarihi", auto_now_add=True)

    # --- Bu bölümün içinde kullanıcının elle bıraktığı işaret ---
    # Her bölümün kendi işareti vardır; hangi bölümde olduğundan bağımsız
    # olarak her bölüme girdiğinde o bölümün işaretine ulaşabilirsin.
    # NOT: İşaret, sayfa kaydırma yüzdesi (scroll %) yerine metnin kendi
    # PARAGRAF numarasına göre tutulur. Böylece ekran boyutu, tarayıcı,
    # adres çubuğu gibi şeylerden tamamen bağımsız, her zaman doğru
    # paragrafa gider.
    mark_paragraph = models.PositiveIntegerField(
        "İşaretlediğin paragraf", null=True, blank=True,
        help_text="Bu bölüm içinde elle bırakılan işaretin paragraf sırası (0'dan başlar)")
    marked_at = models.DateTimeField(
        "İşaretleme zamanı", null=True, blank=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Bölüm"
        verbose_name_plural = "Bölümler"

    def __str__(self):
        return f"{self.book.title} - {self.title or self.url}"

    @property
    def is_fetched(self):
        return bool(self.content)

    def get_paragraphs(self):
        """Bölüm metnini paragraflara böler. İşaret sistemi bu paragraf
        sırasına göre çalışır (scroll yüzdesi yerine)."""
        if not self.content:
            return []
        return [p for p in self.content.split("\n\n") if p.strip()]
