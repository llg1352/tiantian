from django.contrib import admin
from goods.models import GoodsType,GoodsSKU,Goods,GoodsImage,IndexGoodsBanner,IndexTypeGoodsBanner,IndexPromotionBanner
# Register your models here.

# 修改数据的时候 就会调用ModelAdmin中的save_model
class IndexPromotionBannerAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        '''新增或更新表中的数据时调用'''
        super.save_model(request, obj, form, change)

        # 发出任务， 让celery worker  重新生成首页静态页
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()
    def delete_model(self, request, obj, form, change):
        '''删除表中的数据时调用'''
        super.delete_model(request, obj, form, change)

        # 发出任务， 让celery worker  重新生成首页静态页
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()



admin.site.register(GoodsType)
admin.site.register(GoodsSKU)
admin.site.register(Goods)
admin.site.register(GoodsImage)
admin.site.register(IndexGoodsBanner)
admin.site.register(IndexTypeGoodsBanner)
admin.site.register(IndexPromotionBanner)

