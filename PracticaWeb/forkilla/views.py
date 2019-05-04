# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse

from .models import Restaurant, ViewedRestaurants, Review

from django import forms
from django.shortcuts import render
from django.http import HttpResponse
from .models import Restaurant
from .forms import ReservationForm, ReviewForm
from .models import Reservation


def index(request):
    return HttpResponse("Hello, world. You're at the forkilla home.")

@login_required
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
    context = {
        'city': city,
        'category': category,
        'restaurants': restaurants_by_city,
        'promoted': promoted
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

                rev = Review(review_message=comment.data, stars=stars.data, user="Anonymous",
                                restaurant=Restaurant.objects.get(restaurant_number=restaurant_number))
                rev.save()
                commented = True
            else:
                return HttpResponse("Te has calentado")

        viewedrestaurants = _check_session(request)
        restaurant = Restaurant.objects.get(restaurant_number=restaurant_number)
        viewedrestaurants.restaurant.add(restaurant)
        comments = Review.objects.all().order_by("id").reverse()\
            .filter(restaurant=Restaurant.objects.get(restaurant_number=restaurant_number))

        context = {
            'restaurant': restaurant,
            'commented': commented,
            'comments': comments,
            'viewedrestaurants': viewedrestaurants,
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


def reservation(request):
    try:
        if request.method == "POST":
            form = ReservationForm(request.POST)
            if form.is_valid():
                resv = form.save(commit=False)
                restaurant_number = request.session["reserved_restaurant"]
                resv.restaurant = Restaurant.objects.get(restaurant_number=restaurant_number)
                #We need to add up the number of people who makes reservation plus the people who
                #has already reserved.
                total_people = 0
                reservations = Reservation.objects.filter(restaurant=resv.restaurant).filter(time_slot=resv.time_slot)

                for r in reservations:
                    total_people += r.num_people

                if (total_people + resv.num_people) <= resv.restaurant.capacity: #We compare it with the total capacity of the restaurant
                    #If there is space we update the values
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
                'form': form
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
                'form': form
            }

    except Restaurant.DoesNotExist:
        return HttpResponse("Restaurant Does not exist")
    return render(request, 'forkilla/review.html', context)

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