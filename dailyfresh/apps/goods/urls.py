from django.conf.urls import url

from goods import views

urlpatterns = [
    url(r'^index$', views.IndexView.as_view(), name='index'),  # 商品主页
    url(r'^detail/(?P<sku_id>\d+)$', views.DetailView.as_view(), name='detail'),  # 商品详情页
]
