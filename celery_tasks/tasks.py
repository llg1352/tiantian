# 使用celery
from django.conf import settings
from celery import Celery
from django.core.mail import send_mail
from django.template import loader, RequestContext

# 加载用户处理者一端
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tiantian.settings')
django.setup()

from goods.models import IndexGoodsBanner, IndexPromotionBanner, GoodsType, IndexTypeGoodsBanner

# 创建一个Celery类的实例对象
app = Celery('celery_tasks.tasks', broker='redis://:lyr520@127.0.0.1:6379/8')
celery_conf = {'CELERYD_CONCURRENCY': 1}
app.config_from_object(celery_conf)


# 定义任务函数
@app.task
def send_register_active_email(to_email, username, token):
    '''发送激活邮件'''
    # 组织邮件信息
    subject = '天天生鲜欢迎信息'
    message = ''
    html_message = ('<h1>%s, 欢迎您成为天天生鲜注册会员</h1>请点击下面链接激活账号</br><a href="http://127.0.0.1:8000/user/active/%s" >'
                    'http://127.0.0.1:8000/user/active/%s</a>' % (
                    username, token, token))
    sender = settings.EMAIL_FROM  # 发件人
    receiver = [to_email]
    send_mail(subject, message, sender, receiver, html_message=html_message)


# 首页页面的静态化
# 当管理员后台修改首页信息对应的表格中的数据的时候，需要重新生成首页静态页面
@app.task
def generate_static_index_html():
    '''产生首页静态页面'''
    # 获取商品种类信息

    types = GoodsType.objects.all()

    # 获取首页轮播商品信息
    goods_banners = IndexGoodsBanner.objects.all().order_by('index')
    # 获取首页促销活动信息
    promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

    # 获取首页分类商品展示信息
    for type in types:
        # 获取type种类首页分类商品的图片展示信息
        image_banners = IndexTypeGoodsBanner.objects.all(type=type, display=1).order_by('index')
        # 获取type种类首页分类商品的文字展示信息
        title_banners = IndexTypeGoodsBanner.objects.all(type=type, display=0).order_by('index')

        # 动态的给type加属性，分别保存
        type.image_banners = image_banners
        type.title_banners = title_banners

    # 组织模板上下文
    context = {
        'types': types,
        'goods_banners': goods_banners,
        'promotion_banners': promotion_banners,
    }
    # 使用模板
    # 1.加载模板文件
    temp = loader.get_template('static_index.html')
    # # 2.定义模板上下文
    # context = RequestContext(request, context)
    # 3.模板渲染
    static_index_html = temp.render(context)
    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')
    with open(save_path, 'w') as f:
        f.write(static_index_html)
