from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^restaurants/$', views.restaurants, name='restaurants'),
    url(r'^restaurants/(?P<city>.*)/$', views.restaurants, name='restaurants'),
    url(r'^reservation/$', views.reservation, name='reservation'),
    url(r'^review/$', views.review, name='review'),
    url(r'^restaurant/checkout', views.checkout, name='checkout'),
    url(r'^restaurant/(?P<restaurant_number>.*)/', views.details_view, name='details'),
    url(r'^restaurants/(?P<city>.*)/(?P<category>.*)$', views.restaurants, name='filterestaurants'),
    url(r'^register/$', views.register, name='register'),
    url(r'^reservationlist/(?P<username>.*)/$', views.reservationlist, name='reservationlist')
]
