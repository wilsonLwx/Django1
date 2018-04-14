from django.contrib import admin

# Register your models here.
from django.core.cache import cache

from goods.models import GoodsCategory, Goods, GoodsSKU, IndexCategoryGoodsBanner, IndexPromotionBanner
from celery_tasks.tasks import generate_static_index_html


class BaseAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        """运营人员修改数据要走的方法"""
        obj.save()
        # 数据一旦改变 需要执行celery_tasks 里的generate_static_index_html()方法生成静态页面
        generate_static_index_html.delay()
        # 删除缓存
        cache.delete('index_page_static_cache')

    def delete_model(self, request, obj):
        """运营人员删除数据要走的方法"""
        obj.delete()
        generate_static_index_html.delay()
        # 删除缓存
        cache.delete('index_page_static_cache')


class GoodsCategoryAdmin(BaseAdmin):
    pass


class GoodsAdmin(BaseAdmin):
    pass


class GoodsSKUAdmin(BaseAdmin):
    pass


class IndexCategoryGoodsBannerAdmin(BaseAdmin):
    pass


class IndexPromotionBannerAdmin(BaseAdmin):
    pass


admin.site.register(GoodsCategory, GoodsCategoryAdmin)
admin.site.register(Goods, GoodsAdmin)
admin.site.register(GoodsSKU, GoodsSKUAdmin)
admin.site.register(IndexCategoryGoodsBanner, IndexCategoryGoodsBannerAdmin)
admin.site.register(IndexPromotionBanner, IndexPromotionBannerAdmin)
