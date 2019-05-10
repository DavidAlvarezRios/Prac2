# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from datetime import datetime

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

# Create your models here.
from django.db import models


class Restaurant(models.Model):
    CATEGORIES = (
        ("Rice", "Rice"),
        ("Fusi", "Fusion"),
        ("BBQ", "Barbecue"),
        ("Chin", "Chinese"),
        ("Medi", "Mediterranean"),
        ("Crep", "Creperie"),
        ("Hind", "Hindu"),
        ("Japa", "Japanese"),
        ("Ital", "Italian"),
        ("Mexi", "Mexican"),
        ("Peru", "Peruvian"),
        ("Russ", "Russian"),
        ("Turk", "Turkish"),
        ("Basq", "Basque"),
        ("Vegy", "Vegetarian"),
        ("Afri", "African"),
        ("Egyp", "Egyptian"),
        ("Grek", "Greek")
    )
    _d_categories = dict(CATEGORIES)

    restaurant_number = models.CharField(max_length=8, unique=True)
    name = models.CharField(max_length=50)
    menu_description = models.TextField()
    price_average = models.DecimalField(max_digits=5, decimal_places=2)
    is_promot = models.BooleanField()
    rate = models.DecimalField(max_digits=3, decimal_places=1)
    address = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    featured_photo = models.ImageField(upload_to="restaurant_imgs")
    category = models.CharField(max_length=5, choices=CATEGORIES)
    capacity = models.PositiveIntegerField()

    def get_human_category(self):
        return self._d_categories[self.category]

    def __str__(self):
        return ('[**Promoted**]' if self.is_promot else '') + "[" + self.category + "] " \
                                                                                    "[" + self.restaurant_number + "] " + self.name + " - " + self.menu_description + " (" + str(
            self.rate) + ")" \
                         ": " + str(self.price_average) + u" €"


class Reservation(models.Model):
    SLOTS = (
        ("morning_first", "12h00"),
        ("morning_second", "13h00"),
        ("morning_third", "14h00"),
        ("morning_fourth", "15h00"),
        ("evening_first", "20h00"),
        ("evening_second", "21h00"),
        ("evening_third", "22h00"),
    )
    _d_slots = dict(SLOTS)
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User)
    restaurant = models.ForeignKey(Restaurant)
    day = models.DateField(default=datetime.now)
    time_slot = models.CharField(max_length=15, choices=SLOTS)
    num_people = models.PositiveIntegerField(default=1, validators=[MinValueValidator(0)])

    def get_human_slot(self):
        return self._d_slots[self.time_slot]


class ViewedRestaurants(models.Model):
    id_vr = models.AutoField(primary_key=True)
    restaurant = models.ManyToManyField(Restaurant)


class Review(models.Model):
    id = models.AutoField(primary_key=True)
    restaurant = models.ForeignKey(Restaurant)
    #user = models.ForeignKey(User)
    review_message = models.CharField(max_length=500)
    # stars = IntegerRangeField(min_value=0, max_value=5)
    # stars = models.PositiveIntegerField(default=1, validators=[MinValueValidator(0), MaxValueValidator(5)])
    stars = models.IntegerField()
    user = models.CharField(max_length=100, default="Anonymous")

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save()

        reviews = Review.objects.filter(restaurant=self.restaurant)

        contador = 0
        for r in reviews:
            contador += r.stars

        contador /= len(reviews)

        self.restaurant.rate = contador
        self.restaurant.save()
