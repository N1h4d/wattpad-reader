from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("book/<int:book_id>/", views.chapter_list, name="chapter_list"),
    path("chapter/<int:chapter_id>/", views.chapter_detail, name="chapter_detail"),
    path("chapter/<int:chapter_id>/refresh/",
         views.refresh_chapter, name="refresh_chapter"),
    path("chapter/<int:chapter_id>/progress/",
         views.save_progress, name="save_progress"),
]
