import re

import itsdangerous
from django import db
from django.conf import settings
from django.contrib.auth import authenticate

from users.models import User
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

        # 去商品主页
        return HttpResponse('去商品主页')