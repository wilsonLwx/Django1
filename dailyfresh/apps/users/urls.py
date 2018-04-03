from django.conf.urls import url
from users import views

urlpatterns = [
    url(r'^register$', views.RegisterView.as_view(), name='register'),  # 注册
    url(r'^active/(?P<token>.+)$', views.ActiveView.as_view(), name='active'),  # 激活
    url(r'^login$', views.LoginView.as_view(), name='login'),  # 登录
    url(r'^logout$', views.LogoutView.as_view(), name='logout'),  # 登出
    url(r'^address$', views.AddressView.as_view(), name='address'),  # 收货地址
]
