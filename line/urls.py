from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic import TemplateView
from app.views import *

urlpatterns = [
    url(r'^$', CallbackView.as_view()),
    url(r'^admin/', admin.site.urls),
    url(r'^init$', ContactInit.as_view()),
    url(r'^register$', ContactRegister.as_view()),
    url(r'^register/complete$', ContactRegisterComplete.as_view()),
    url(r'^django-rq/', include('django_rq.urls')),
    url(r'^favicon.ico$', TemplateView.as_view(template_name='favicon.ico')),
]

handler500 = AppricationError.as_view()
