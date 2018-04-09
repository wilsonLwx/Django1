import re

import itsdangerous
from django import db
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django_redis import get_redis_connection

from goods.models import GoodsSKU
from users.models import User, Address
from utils.views import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.views.generic import View

# 注册的类视图
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from celery_tasks.tasks import send_active_email


class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        # 获取用户信息
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 校验信息
        if not all([username, password, email]):
            return redirect(reverse('users:register'))

        # 校验邮箱格式
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱错误'})

        # 如果用户勾选同意协议 checkbox会传过来on
        if not allow == 'on':
            return render(request, 'register.html', {'errmsg': '必须同意协议'})

        try:
            # 将数据保存数据库 UserManager提供了一个create_user的方法 创建过程中自动密码加密 加盐值
            user = User.objects.create_user(username=username, email=email, password=password)

        # 如果用户已经注册会报异常IntegrityError
        except db.IntegrityError:
            return render(request, 'register.html', {'errmsg': '用户已经存在'})

        # 注册为默认激活状态不符合要求
        user.is_active = False
        # 保存数据库
        user.save()

        # 生成token
        token = user.generate_active_token()

        # 接收邮件的用户 可以是多个
        recipient_list = ['15000108650@163.com']

        # 发送激活邮件
        send_active_email.delay(recipient_list, user.username, token)

        return HttpResponse('ok')


# 激活视图
class ActiveView(View):
    def get(self, request, token):
        # 解析用户id
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            result = serializer.loads(token)
        except itsdangerous.SignatureExpired:
            return HttpResponse('激活邮件已过期')
        print(result)
        userid = result.get('confirm')
        print(userid)

        # 根据用户id获取用户
        try:
            user = User.objects.get(id=userid)
        except User.DoesNotExist:
            return HttpResponse('用户不存在')

        if user.is_active:
            return HttpResponse('用户已经激活')

        # 激活用户
        user.is_active = True
        user.save()

        # 重定向到登录页
        return redirect(reverse('users:login'))


# 登录的的类视图
class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        # 获取用户登录数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')

        # 校验数据
        # 判断数据是否为空
        if not all([username, password]):
            return redirect(reverse('users:login'))

        # 如果不为空 从数据库获取用户信息
        # user = User.objects.filter(username=username, password=password)
        # django 提供了验证方法 成功了返回user对象 不成功返回None
        user = authenticate(username=username, password=password)
        if user is None:
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})

        # 判断是否激活
        if not user.is_active:
            return render(request, 'login.html', {'errmsg': '用户未激活'})

        # django提供的 用来保存用户信息到session的方法 比如10天不用重复登录
        login(request, user)

        # 获取用户是否勾选记住用户名
        remembered = request.POST.get('remembered')

        # 如果用户勾选 传过来的值就是on
        if remembered != 'on':
            # 设置session过期时间 0表示关闭浏览器就过期 None表示2周
            request.session.set_expiry(0)
        else:
            request.session.set_expiry(None)

        # 如果之前是从用户相关页面重定向到登录页面的 登陆之后就跳转到之前页面
        next = request.GET.get('next')
        if next is None:
            # 去商品主页
            return HttpResponse('去商品主页')
        else:
            return redirect(next)


# 登出类视图
class LogoutView(LoginRequiredMixin, View):
    def get(self, request):
        # 同样django提供了logout()的登出方法
        logout(request)

        return HttpResponse('OK')


# 收货地址
class AddressView(LoginRequiredMixin, View):
    def get(self, request):
        # 获取用信息
        user = request.user
        try:
            # 根据创建用户时间获取最近地址
            address = user.address_set.latest('create_time')
        except Address.DoesNotExist:
            address = None

        context = {"address": address}

        return render(request, 'user_center_site.html', context)

    def post(self, request):
        """修改地址信息"""
        user = request.user
        # 获取用户输入信息
        recv_name = request.POST.get('recv_name')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        recv_mobile = request.POST.get('recv_mobile')
        # 校验完整性 如果都不为空 创建该用户信息 保存到数据库
        if all([recv_name, addr, zip_code, recv_mobile]):
            Address.objects.create(
                user=user,
                receiver_name=recv_name,
                receiver_mobile=recv_mobile,
                detail_addr=addr,
                zip_code=zip_code
            )
        return redirect(reverse('users:address'))


class UserInfoView(LoginRequiredMixin, View):
    def get(self, request):
        # 获取用信息
        user = request.user
        try:
            # 根据创建用户时间获取最近地址
            address = user.address_set.latest('create_time')
        except Address.DoesNotExist:
            address = None

        # 获取浏览历史记录  history_userid : [sku1.id,sku2.id,.....]
        # 使用django_redis源生客户端
        conn = get_redis_connection('default')
        # 获取数据 lrange 0 4 前5个商品的id
        sku_ids = conn.lrange('history_%s' % user.id, 0, 4)
        # 去数据库查对应的商品
        skus = GoodsSKU.objects.filter(id__in=sku_ids)
        context = {
            'address': address,
            'skus': skus
        }

        return render(request, 'user_center_info.html', context)
