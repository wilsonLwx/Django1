from django.conf.urls import url

from goods import views

urlpatterns = [
    url(r'^index$', views.IndexView.as_view(), name='index'),  # 商品主页
    url(r'^detail/(?P<sku_id>\d+)$', views.DetailView.as_view(), name='detail'),  # 商品详情页
    url(r'^list/(?P<category_id>\d+)/(?P<page>\d+)$', views.ListView.as_view(), name='list') # 商品列表
]
