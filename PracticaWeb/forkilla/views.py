# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse
# Create your views here.
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic import DeleteView

from .forms import ReservationForm, ReviewForm
from .models import Reservation
from .models import Restaurant
from .models import ViewedRestaurants, Review

from datetime import date


def index(request):
    return HttpResponse("Hello, world. You're at the forkilla home.")


def restaurants(request, city="", category=""):
    promoted = False

    if city and category:
        restaurants_by_city = Restaurant.objects.filter(city__iexact=city, category__iexact=category)
    elif city:
        restaurants_by_city = Restaurant.objects.filter(city__iexact=city)

    else:

        restaurants_by_city = Restaurant.objects.filter(is_promot="True")
        promoted = True
    if request.GET:
        restaurants_by_city = Restaurant.objects.filter(city__iexact=request.GET['searching'])

    viewedrestaurants = _check_session(request)

    context = {
        'city': city,
        'category': category,
        'restaurants': restaurants_by_city,
        'promoted': promoted,
        'user': request.user,
        'viewedrestaurants': viewedrestaurants
    }
    return render(request, 'forkilla/restaurants.html', context)


def details_view(request, restaurant_number=""):
    try:
        commented = False
        if request.method == "POST":

            form = ReviewForm(request.POST)
            if form.is_valid():

                comment = form['review_message']
                stars = form['stars']

                rev = Review(review_message=comment.data, stars=stars.data, user=request.user.get_username(),
                             restaurant=Restaurant.objects.get(restaurant_number=restaurant_number))
                rev.user = request.user.get_username()
                rev.save()
                commented = True
            else:
                return HttpResponse("Te has calentado")

        viewedrestaurants = _check_session(request)
        restaurant = Restaurant.objects.get(restaurant_number=restaurant_number)
        viewedrestaurants.restaurant.add(restaurant)
        comments = Review.objects.all().order_by("id").reverse() \
            .filter(restaurant=Restaurant.objects.get(restaurant_number=restaurant_number))

        context = {
            'restaurant': restaurant,
            'commented': commented,
            'comments': comments,
            'viewedrestaurants': viewedrestaurants,
            'user': request.user
        }
    except Restaurant.DoesNotExist:
        return HttpResponse("Hi ha hagut un error")

    return render(request, 'forkilla/details.html', context)


def checkout(request):
    correcte = request.session["result"] == "OK"
    context = {
        'resultat': correcte
    }

    return render(request, 'forkilla/checkout.html', context)


@login_required
def reservation(request):
    try:
        if request.method == "POST":
            form = ReservationForm(request.POST)
            if form.is_valid():
                resv = form.save(commit=False)
                restaurant_number = request.session["reserved_restaurant"]
                resv.restaurant = Restaurant.objects.get(restaurant_number=restaurant_number)
                resv.user = request.user
                # We need to add up the number of people who makes reservation plus the people who
                # has already reserved.
                total_people = 0
                reservations = Reservation.objects.filter(restaurant=resv.restaurant).filter(time_slot=resv.time_slot)

                for r in reservations:
                    total_people += r.num_people

                if (
                        total_people + resv.num_people) <= resv.restaurant.capacity:  # We compare it with the total capacity of the restaurant
                    # If there is space we update the values
                    resv.save()
                    request.session["reservation"] = resv.id
                    request.session["result"] = "OK"
                else:
                    request.session["result"] = "NOT OK"

            else:
                request.session["result"] = form.errors
            return HttpResponseRedirect(reverse('checkout'))

        elif request.method == "GET":
            viewedrestaurants = _check_session(request)
            restaurant_number = request.GET["reservation"]
            restaurant = Restaurant.objects.get(restaurant_number=restaurant_number)
            request.session["reserved_restaurant"] = restaurant_number

            form = ReservationForm()
            context = {
                'restaurant': restaurant,
                'viewedrestaurants': viewedrestaurants,
                'form': form,
                'logged': request.user.is_authenticated()
            }
    except Restaurant.DoesNotExist:
        return HttpResponse("Restaurant Does not exists")
    return render(request, 'forkilla/reservation.html', context)


def _check_session(request):
    if "viewedrestaurants" not in request.session:
        viewedrestaurants = ViewedRestaurants()
        viewedrestaurants.save()
        request.session["viewedrestaurants"] = viewedrestaurants.id_vr
    else:
        viewedrestaurants = ViewedRestaurants.objects.get(id_vr=request.session["viewedrestaurants"])
    return viewedrestaurants


def _check_session_review(request):
    if "reviewedrestaurant" not in request.session:
        review = Review()
        review.save()
        request.session["reviewedrestaurant"] = review.id
    else:
        review = Review.objects.get(id=request.session["reviewedrestaurant"])
    return review


def review(request):
    try:
        if request.method == "POST":
            form = ReviewForm(request.POST)
            if form.is_valid():
                review = form.save(commit=False)
                restaurant_number = request.session["reviewedrestaurant"]
                review.restaurant = Restaurant.objects.get(restaurant_number__iexact=restaurant_number)
                review.user = request.user
                review.save()
                review.session["review"] = review.id
                review.session["review_message"] = review.review_message
                review.session["stars"] = review.stars
                review.session["result"] = "OK"
            else:
                request.session["result"] = form.errors
            return HttpResponseRedirect(reverse('checkout'))

        elif request.method == "GET":
            reviewedrestaurants = _check_session_review(request)
            restaurant_number = request.GET["review"]
            restaurant = Restaurant.objects.get(restaurant_number=restaurant_number)
            request.session["reviewedrestaurant"] = restaurant_number
            form = ReviewForm()
            context = {
                'restaurant': restaurant,
                'viewedrestaurants': reviewedrestaurants,
                'form': form,
                'user': request.user
            }

    except Restaurant.DoesNotExist:
        return HttpResponse("Restaurant Does not exist")
    return render(request, 'forkilla/review.html', context)


@login_required
def reservationlist(request, username=""):
    if request.method == "GET":
        reserved_restaurants = Reservation.objects.filter(user=request.user).order_by('-day')
        past_date = []
        reviewed = []
        future_date = []

        for reserv in reserved_restaurants:
            if reserv.day < date.today():
                past_date.append((reserv, been_reviewed(request, reserv.restaurant)))
                # reviewed.append(been_reviewed(request, reserv.restaurant))

            else:
                future_date.append(reserv)

        context = {'reserved_restaurants': reserved_restaurants,
                   'past': past_date,
                   'future': future_date,
                   'user': request.user,
                   'username': username
                   }
    return render(request, "forkilla/reservationlist.html", context)


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            return HttpResponseRedirect(reverse("index"))
    else:
        form = UserCreationForm()
    return render(request, "registration/register.html", {
        'form': form,
    })


def login_user(request):
    if request.method == 'POST':
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(username=username, password=password)

        if user is None:
            if user.is_active:
                login(request, user)

    return ""


class DeleteView(SuccessMessageMixin, DeleteView):
    model = Reservation
    success_message = "deleted..."

    def get_success_url(self):
        username = self.object.user.get_username()
        return reverse_lazy('reservationlist', kwargs={'username': username})


def delete(self, request, *args, **kwargs):
    self.object = self.get_object()
    name = self.object.id
    request.session['name'] = str(name)  # name will be change according to your need
    message = request.session['name'] + ' deleted successfully'
    message.success(self.request, message)
    return super(DeleteView, self).delete(request, *args, **kwargs)


def been_reviewed(request, restaurant):
    reviewed_restaurants = Review.objects.all().filter(restaurant=Restaurant.objects.get(restaurant_number=restaurant.restaurant_number), user=request.user)

    if reviewed_restaurants:
        return True
    return False

