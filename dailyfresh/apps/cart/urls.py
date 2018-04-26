from django.conf.urls import url

from cart import views

urlpatterns = [
    url(r'^add$', views.AddCartView.as_view(), name='add'),  # 商品主页
]
