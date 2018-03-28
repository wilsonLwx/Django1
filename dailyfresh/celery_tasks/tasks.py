# import os
# # 添加环境变量
# os.environ['DJANGO_SETTINGS_MODULE']='dailyfresh.settings'
# # 放到Celery服务器上添加的代码
# import django
# django.setup()

from celery import Celery
from django.conf import settings
from django.core.mail import send_mail

# 实例化celery对象  参1为celery任务所在文件路径 参2为broker的redis地址 redis://:密码@ip地址:端口
app = Celery('celery_tasks.tasks', broker='redis://192.168.17.147:6379/3')


@app.task
def send_active_email(recipient_list, user_name, token):
    html_body = '<h1>尊敬的用户 %s, 感谢您注册天天生鲜！</h1>' \
                '<br/><p>请点击此链接激活您的帐号<a href="http://127.0.0.1:8000/users/active/%s">' \
                'http://127.0.0.1:8000/users/active/%s</a></p>' % (user_name, token, token)
    # 发送激活邮件
    send_mail('天天生鲜激活', '', settings.EMAIL_FROM, recipient_list, html_message=html_body)
