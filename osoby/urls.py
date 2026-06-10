from django.urls import path
from .views import (
    home,
    person_detail,
    parties_ranking,
    search,
    mapa,
    ranking_users,
    register,
    login_view,
    faq,
    about,
    contact,
    support,
    vote_person,
logout_view
)

urlpatterns = [
    path("", home),
    path("szukaj/", search),
    path(
        "osoba/<int:person_id>/",
        person_detail,
        name="person_detail"
    ),
    path("partie/", parties_ranking),
    path("mapa/", mapa),
    path(
    "ranking-uzytkownikow/",
    ranking_users),
    path(
    "rejestracja/",
    register),
    path(
    "logowanie/",
    login_view),
    path("faq/",faq),
    path("o-nas/", about),
    path("kontakt/", contact),
    path("wspieraj/", support),
path(
    "vote/<int:person_id>/<str:vote>/",
    vote_person,
    name="vote_person"
),
path(
    "wylogowanie/",
    logout_view
),



]