from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic import TemplateView
from app.views import *

urlpatterns = [
    url(r'^$', CallbackView.as_view()),
    url(r'^admin/', admin.site.urls),
    url(r'^init$', LiveagentInit.as_view()),
    url(r'^register$', LiveagentRegister.as_view()),
    url(r'^register/complete$', LiveagentRegisterComplete.as_view()),
    url(r'^django-rq/', include('django_rq.urls')),
    url(r'^favicon.ico$', TemplateView.as_view(template_name='favicon.ico')),
]

handler500 = AppricationError.as_view()
