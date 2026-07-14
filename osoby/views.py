from django.http import HttpResponse
from .models import Person
from django.shortcuts import render, get_object_or_404
from django.db.models import Q

from .models import Party, PartyMembership
from django.db.models import Count

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import PersonVote
from django.db.models import Sum

from django.db.models import F, Value
from django.db.models.functions import Coalesce
from django.db.models import ExpressionWrapper, FloatField

from django.db.models import (
    F,
    Case,
    When,
    DecimalField,
    ExpressionWrapper,
    OuterRef,
    Subquery,
)

from .forms import RegisterForm, PersonSubmissionForm, PersonForm, LoginForm
from .models import PersonSubmission, PersonSource
from .share_card import generate_share_card
from django.contrib.auth.models import User

from django.contrib.auth import login
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.views.decorators.http import require_POST

from django.shortcuts import redirect
from django.contrib.auth import logout


def is_superuser(user):
    return user.is_superuser





def home(request):
    query = request.GET.get("q", "")
    sort = request.GET.get("sort")
    selected_parties = request.GET.getlist("party")

    latest_membership_party = PartyMembership.objects.filter(
        person=OuterRef("pk")
    ).order_by("-start_year", "-id").values("party__name")[:1]

    people = Person.objects.annotate(
        current_party_name=Subquery(latest_membership_party)
    )

    if query:
        people = people.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(position__icontains=query) |
            Q(organization__icontains=query)
        )

    if selected_parties:
        people = people.filter(current_party_name__in=selected_parties)

    if sort == "salary":

        people = people.annotate(

            salary_sort=Case(

                When(
                    annual_salary__isnull=False,
                    then=F("annual_salary")
                ),

                default=ExpressionWrapper(
                    (F("salary_min") + F("salary_max")) / 2,
                    output_field=DecimalField()
                ),

                output_field=DecimalField()

            )

        ).order_by("-salary_sort")


    elif sort == "az":

        people = people.order_by("last_name", "first_name")


    elif sort == "za":

        people = people.order_by("-last_name", "-first_name")

    elif sort == "controversial":

        people = people.annotate(
            downvote_count=Count("votes", filter=Q(votes__vote=-1))
        ).order_by("-downvote_count")

    salary_sum = Person.objects.annotate(
        effective_salary=Coalesce(
            "annual_salary",
            ExpressionWrapper(
                (F("salary_min") + F("salary_max")) / Value(2),
                output_field=DecimalField(
                    max_digits=15,
                    decimal_places=2
                )
            )
        )
    ).aggregate(
        total=Sum("effective_salary")
    )["total"] or 0

    return render(
        request,
        "home.html",
        {
            "people": people,
            "query": query,
            "count": people.count(),
            "salary_sum": salary_sum,
            "sort": sort,
            "all_parties": Party.objects.order_by("name"),
            "selected_parties": selected_parties,
        }
    )

def person_share_card(request, person_id):

    person = get_object_or_404(Person, id=person_id)

    image_bytes = generate_share_card(person)

    return HttpResponse(image_bytes, content_type="image/png")


def person_detail(request, person_id):

    person = get_object_or_404(
        Person,
        id=person_id
    )

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render(
            request,
            "components/person_modal_content.html",
            {"person": person}
        )

    return render(
        request,
        "person_detail.html",
        {"person": person, "show_reroll": True}
    )

def losowy_koles(request):

    people = Person.objects.all()

    exclude_id = request.GET.get("exclude")
    if exclude_id:
        people = people.exclude(id=exclude_id)

    person = people.order_by("?").first() or Person.objects.order_by("?").first()

    if not person:
        return redirect("/")

    return redirect("person_detail", person_id=person.id)


def parties_ranking(request):

    parties = Party.objects.annotate(
        people_count=Count(
            "partymembership__person",
            distinct=True
        )
    ).order_by("-people_count")

    top_party = parties.first()

    total_people = sum(
        party.people_count
        for party in parties
    )

    return render(
        request,
        "parties.html",
        {
            "parties": parties,
            "top_party": top_party,
            "total_people": total_people,
        }
    )

def search(request):
    query = request.GET.get("q", "")

    people = Person.objects.all()

    if query:
        people = people.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(position__icontains=query) |
            Q(organization__icontains=query)
        )

    return render(
        request,
        "home.html",
        {
            "people": people,
            "query": query,
            "count": people.count(),
        }
    )


def mapa(request):

    people = Person.objects.exclude(
        latitude__isnull=True
    ).exclude(
        longitude__isnull=True
    )

    return render(
        request,
        "mapa.html",
        {
            "people": people
        }
    )



def ranking_users(request):

    users = User.objects.annotate(
        approved_count=Count(
            "submissions",
            filter=Q(submissions__status="approved")
        )
    ).filter(approved_count__gt=0).order_by("-approved_count")

    ranking = [
        {
            "user": u,
            "count": u.approved_count,
        }
        for u in users
    ]

    total_caught = sum(entry["count"] for entry in ranking)

    return render(
        request,
        "ranking_users.html",
        {
            "ranking": ranking,
            "total_caught": total_caught,
        }
    )


@login_required
def zglos_kolesia(request):

    success = False

    if request.method == "POST":
        form = PersonSubmissionForm(request.POST, request.FILES)

        if form.is_valid():
            submission = form.save(commit=False)
            submission.submitted_by = request.user
            submission.save()

            form = PersonSubmissionForm()
            success = True

    else:
        form = PersonSubmissionForm()

    return render(
        request,
        "zglos_kolesia.html",
        {
            "form": form,
            "success": success,
        }
    )


def register(request):

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save()

            login(request, user)

            return redirect("/")

    else:

        form = RegisterForm()

    return render(
        request,
        "register.html",
        {
            "form": form
        }
    )


def login_view(request):

    if request.method == "POST":

        form = LoginForm(
            request,
            data=request.POST
        )

        if form.is_valid():

            user = form.get_user()

            login(request, user)

            return redirect("/")

    else:

        form = LoginForm()

    return render(
        request,
        "login.html",
        {
            "form": form
        }
    )

def logout_view(request):

    logout(request)

    return redirect("/")

def faq(request):
    return render(
        request,
        "faq.html"
    )

def about(request):
    return render(
        request,
        "about.html"
    )


def contact(request):
    return render(
        request,
        "contact.html"
    )

def support(request):
    return render(
        request,
        "support.html"
    )
def vote_person(request, person_id, vote):

    if not request.user.is_authenticated:
        return JsonResponse(
            {
                "error": "login_required"
            },
            status=403
        )

    vote = int(vote)

    person = get_object_or_404(
        Person,
        id=person_id
    )

    PersonVote.objects.update_or_create(
        person=person,
        user=request.user,
        defaults={
            "vote": vote
        }
    )

    return JsonResponse({
        "upvotes": person.upvotes,
        "downvotes": person.downvotes,
        "approval": person.approval_percent,
    })


@user_passes_test(is_superuser, login_url="/")
def dodaj_kolesia(request):

    if request.method == "POST":
        form = PersonForm(request.POST, request.FILES)

        if form.is_valid():
            person = form.save()

            source_url = form.cleaned_data.get("source_url")

            if source_url:
                PersonSource.objects.create(
                    person=person,
                    title=form.cleaned_data.get("source_title") or source_url,
                    url=source_url,
                )

            messages.success(
                request,
                f"Dodano {person.first_name} {person.last_name}."
            )
            return redirect("edytuj_kolesia", person_id=person.id)

    else:
        form = PersonForm()

    return render(
        request,
        "kolesia_form.html",
        {
            "form": form,
            "is_edit": False,
        }
    )


@user_passes_test(is_superuser, login_url="/")
def edytuj_kolesia(request, person_id):

    person = get_object_or_404(Person, id=person_id)

    if request.method == "POST":
        form = PersonForm(request.POST, request.FILES, instance=person)

        if form.is_valid():
            form.save()

            source_url = form.cleaned_data.get("source_url")

            if source_url:
                PersonSource.objects.get_or_create(
                    person=person,
                    url=source_url,
                    defaults={
                        "title": form.cleaned_data.get("source_title") or source_url
                    },
                )

            messages.success(
                request,
                f"Zaktualizowano {person.first_name} {person.last_name}."
            )
            return redirect("edytuj_kolesia", person_id=person.id)

    else:
        form = PersonForm(instance=person)

    return render(
        request,
        "kolesia_form.html",
        {
            "form": form,
            "is_edit": True,
            "person": person,
        }
    )


@user_passes_test(is_superuser, login_url="/")
@require_POST
def usun_kolesia(request, person_id):

    person = get_object_or_404(Person, id=person_id)
    name = f"{person.first_name} {person.last_name}"
    person.delete()

    messages.success(request, f"Usunięto {name}.")
    return redirect("/")


@user_passes_test(is_superuser, login_url="/")
def panel_zgloszenia(request):

    if request.method == "POST":
        submission = get_object_or_404(
            PersonSubmission,
            id=request.POST.get("submission_id")
        )

        if request.POST.get("action") == "approve":
            submission.approve()
            messages.success(
                request,
                f"Zaakceptowano {submission.first_name} {submission.last_name}."
            )
        elif request.POST.get("action") == "reject":
            submission.reject()
            messages.info(
                request,
                f"Odrzucono {submission.first_name} {submission.last_name}."
            )

        return redirect("panel_zgloszenia")

    return render(
        request,
        "panel_zgloszenia.html",
        {
            "pending": PersonSubmission.objects.filter(status="pending"),
            "recent": PersonSubmission.objects.exclude(status="pending")[:10],
        }
    )