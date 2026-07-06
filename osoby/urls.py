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
    logout_view,
    zglos_kolesia,
    dodaj_kolesia,
    edytuj_kolesia,
    usun_kolesia,
    panel_zgloszenia,
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
        register,
        name="rejestracja"
    ),
    path(
    "logowanie/",
    login_view,
    name="logowanie"),
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
path(
    "zglos-kolesia/",
    zglos_kolesia,
    name="zglos_kolesia"
),
path(
    "dodaj-kolesia/",
    dodaj_kolesia,
    name="dodaj_kolesia"
),
path(
    "edytuj-kolesia/<int:person_id>/",
    edytuj_kolesia,
    name="edytuj_kolesia"
),
path(
    "usun-kolesia/<int:person_id>/",
    usun_kolesia,
    name="usun_kolesia"
),
path(
    "panel/zgloszenia/",
    panel_zgloszenia,
    name="panel_zgloszenia"
),




]