from django.http import HttpResponse
from .models import Person
from django.shortcuts import render, get_object_or_404
from django.db.models import Q

from .models import Party
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
    ExpressionWrapper
)

from .forms import RegisterForm

from django.contrib.auth import login
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm

from django.shortcuts import redirect
from django.contrib.auth import logout





def home(request):
    query = request.GET.get("q", "")
    sort = request.GET.get("sort")

    people = Person.objects.all()

    if query:
        people = people.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(position__icontains=query) |
            Q(organization__icontains=query)
        )

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
        }
    )

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
        {"person": person}
    )

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
    return render(
        request,
        "ranking_users.html"
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

        form = AuthenticationForm(
            request,
            data=request.POST
        )

        if form.is_valid():

            user = form.get_user()

            login(request, user)

            return redirect("/")

    else:

        form = AuthenticationForm()

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