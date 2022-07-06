from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'tags', views.TagViewSet)

urlpatterns = [

]

urlpatterns += router.urls
