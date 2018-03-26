from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from django.views.generic import View


# 注册的类视图
class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        return HttpResponse('ok')
