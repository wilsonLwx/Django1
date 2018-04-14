import os
# # 添加环境变量
# os.environ['DJANGO_SETTINGS_MODULE']='dailyfresh.settings'
# # 放到Celery服务器上添加的代码
# import django
# django.setup()

from celery import Celery
from django.conf import settings
from django.core.mail import send_mail

# 实例化celery对象  参1为celery任务所在文件路径 参2为broker的redis地址 redis://:密码@ip地址:端口
from django.template import loader

from goods.models import GoodsCategory, IndexGoodsBanner, IndexPromotionBanner, IndexCategoryGoodsBanner

app = Celery('celery_tasks.tasks', broker='redis://192.168.17.147:6379/3')


@app.task
def send_active_email(recipient_list, user_name, token):
    html_body = '<h1>尊敬的用户 %s, 感谢您注册天天生鲜！</h1>' \
                '<br/><p>请点击此链接激活您的帐号<a href="http://127.0.0.1:8000/users/active/%s">' \
                'http://127.0.0.1:8000/users/active/%s</a></p>' % (user_name, token, token)
    # 发送激活邮件
    send_mail('天天生鲜激活', '', settings.EMAIL_FROM, recipient_list, html_message=html_body)


# 生成主页静态文件
@app.task
def generate_static_index_html():
    # 显示首页
    # 商品分类的全部数据
    categorys = GoodsCategory.objects.all()
    # 幻灯片
    banners = IndexGoodsBanner.objects.all()
    # 活动
    promotion_banners = IndexPromotionBanner.objects.all()
    # # 首页所有的分类商品数据
    # goodsbanners = IndexCategoryGoodsBanner.objects.all()
    #

    for category in categorys:
        # 查询对应类别下的数据
        # display_type = 0 是标题类商品  1是图片类商品 按照index排序
        title_banners = IndexCategoryGoodsBanner.objects.filter(
            category=category, display_type=0).order_by('index')
        # 把数据以属性的形式存到category对象中
        category.title_banners = title_banners

        image_banners = IndexCategoryGoodsBanner.objects.filter(
            category=category, display_type=1).order_by('index')
        category.image_banners = image_banners

    context = {
        'categorys': categorys,
        'banners': banners,
        'promotion_banners': promotion_banners
    }
    # content 是数据渲染好的最终html代码 是根据render方法内部源码实现的
    # 文件流 耗时操作 celery 异步执行
    content = loader.render_to_string('static_index.html', context)

    # 将content保存成静态文件
    file_path = os.path.join(settings.STATICFILES_DIRS[0], 'index.html')

    with open(file_path, 'w') as f:
        f.write(content)
