from django.contrib import admin
from .models import Book, Chapter


class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 0
    fields = ("order", "title", "url", "is_fetched", "fetched_at")
    readonly_fields = ("is_fetched", "fetched_at")


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "created_at")
    search_fields = ("title", "author")
    inlines = [ChapterInline]


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ("title", "book", "order", "is_fetched", "fetched_at")
    list_filter = ("book",)
    search_fields = ("title", "url")
