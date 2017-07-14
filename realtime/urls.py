from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.login, name='logout'),
    url(r'^project/$', views.project, name='project'),
    url(r'^device/$', views.device, name='device'),
    url(r'^registerdevice/$', views.registerDevice, name='registerdevice'),
]