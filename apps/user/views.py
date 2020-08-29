from django.shortcuts import render, redirect
import re
from user.models import User, Address
from order.models import OrderInfo, OrderGoods
from django.urls import reverse
from django.views.generic import View
from itsdangerous import TimedJSONWebSignatureSerializer as Ts  # 加密token
from django.conf import settings
from itsdangerous import SignatureExpired  # 过期异常
from django.http import HttpResponse
from django.core.mail import send_mail  # 发送邮件
from django.contrib.auth import authenticate, login, logout  # 用户认证
from utils.mixin import LoginRequiredMixin
from django_redis import get_redis_connection
from goods.models import GoodsSKU
from celery_tasks.tasks import send_register_active_email
from django.core.paginator import Paginator


# Create your views here.

# /user/register
def register(request):
    '''显示注册页面'''
    if request.method == 'GET':
        # 显示注册页面
        return render(request, 'register.html')
    else:
        '''进行注册处理'''
        # 接收数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # 进行数据校验  all()方法，如果传入的可迭代对象的每个值都为真 返回真 否则为假
        if not all([username, password, email]):
            # 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})
        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})
        # 校验用户名是否重复 查不到会抛出异常
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None
        if user == None:

            # 进行业务处理:进行用户注册
            user = User.objects.create_user(username, email, password)
            user.is_active = 0
            user.save()

            # 返回应答,跳转到首页
            return redirect(reverse('goods:index'))
        else:
            return render(request, 'register.html', {'errmsg': '用户名已存在'})


# /user/register
class RegisterView(View):
    '''注册类'''

    def get(self, request):
        '''显示注册页面'''
        return render(request, 'register.html')

    def post(self, request):
        '''进行注册处理'''
        # 接收数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # 进行数据校验  all()方法，如果传入的可迭代对象的每个值都为真 返回真 否则为假
        if not all([username, password, email]):
            # 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})
        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})
        # 校验用户名是否重复 查不到会抛出异常
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None
        if user is None:

            # 进行业务处理:进行用户注册
            user = User.objects.create_user(username, email, password)
            user.is_active = 0
            user.save()
            # 发送激活邮件，包含激活链接：http://127.0.0.1:8000/user/active/3
            # 激活链接中需要包含用户的信息,并且把身份信息进行加密处理
            # 加密用户的身份信息，生成激活的token
            ts = Ts(settings.SECRET_KEY, 3600)
            info = {'confirm': user.id}
            token = ts.dumps(info)  # 字节流需要解码成字符串
            token = token.decode()
            # 发邮件  subject 为发送主题 如果message有html标签 要通过 html_message 来传
            send_register_active_email.delay(email, username, token)
            # 返回应答,跳转到首页
            return redirect(reverse('goods:index'))
        else:
            return render(request, 'register.html', {'errmsg': '用户名已存在'})


# /user/active/***
class ActiveView(View):
    '''用户激活'''

    def get(self, request, token):
        ts = Ts(settings.SECRET_KEY, 3600)
        try:
            info = ts.loads(token)
            user_id = info['confirm']
            # 根据id获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()
            # 用户激活成功，跳转到登录页面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            # 激活链接已过期
            return HttpResponse('激活链接已过期')


# /user/login/
class LoginView(View):
    '''登录'''

    def get(self, request):
        '''显示登录页面'''
        # 判断是否记住了用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES['username']
            checked = 'checked'
        else:
            username = ''
            checked = ''
        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        '''登录校验'''
        # 接收数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        remember = request.POST.get('remember')
        # 校验数据 完整性
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '数据不完整'})
        # 业务处理:登录校验
        user = authenticate(username=username, password=password)  # 返回user对象
        print(user)
        if user is not None:
            # 用户名密码正确
            if user.is_active:
                # 用户名已激活
                # 记录用户的状态
                login(request, user)
                # 获取登录后所要跳转的地址
                next_url = request.GET.get('next', reverse('goods:index'))  # None
                # 判断是否需要记住用户名
                response = redirect(next_url)  # HttpResponse的子类, 用来设置cookie再返回
                if remember == 'on':
                    # 记住用户名
                    response.set_cookie('username', username, max_age=7 * 24 * 3600)
                else:
                    response.delete_cookie('username')
                return response
                # return redirect(reverse('goods:index'))
            else:
                # 用户名未激活
                return render(request, 'login.html', {'errmsg': '账户未激活'})
        else:
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})


# /user/logout
class LogoutView(View):
    '''退出登录'''

    def get(self, request):
        '''退出登录'''
        # 清除用户的session信息
        logout(request)

        # 跳转到首页
        return redirect(reverse('goods:index'))


# /user
class UserInfoView(LoginRequiredMixin, View):
    '''用户中心-信息页'''

    def get(self, request):
        '''显示'''
        # request.user.is_authenticated
        # 获取用户个人信息
        user = request.user
        address, l = Address.objects.get_address(user)
        # 获取用户历史浏览记录
        # from redis import StrictRedis
        # sr = StrictRedis(host='loaclhost, port='6379', db=0)
        con = get_redis_connection('default')
        history_key = 'history_%d' % user.id
        # 获取用户最新浏览的5个商品id
        sku_ids = con.lrange(history_key, 0, 4)
        # 从数据库中查询用户浏览的商品的具体信息
        # goods_li = GoodsSKU.objects.filter(id__in=sku_ids).order
        goods_li = list()
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)
        # 组织上下文
        context = {
            'page': 'user',
            'address': address,
            'goods_li': goods_li,
        }
        # 除了你给模板文件传递的模板变量外，django框架会把request.user也传过去
        return render(request, 'user_center_info.html', context)


# /user/order
class UserOrderView(LoginRequiredMixin, View):
    '''用户中心-订单页'''

    def get(self, request, page):
        '''显示'''
        # 获取用户的订单信息
        user = request.user
        orders = OrderInfo.objects.filter(user=user).order_by('-create_time')

        # 遍历获取订单商品的信息
        for order in orders:
            # 根据order_id查询订单商品信息
            order_skus = OrderGoods.objects.filter(order_id=order.order_id)
            # 遍历order_skus计算商品的小计
            for order_sku in order_skus:
                # 计算小计
                amount = order_sku.count*order_sku.price
                # 动态给order_sku增加属性amount，保存订单商品的小计
                order_sku.amount = amount
            # 动态给order增加属性，保存订单状态标题
            order.status_name = OrderInfo.ORDER_STATUS[order.order_status]
            # 动态给order增加属性，保存订单商品的信息
            order.order_skus = order_skus
        # 分页
        paginator = Paginator(orders, 4)

        # 处理页码
        # 获取对应页码内容
        try:
            page = int(page)
        except Exception as e:
            page = 1
        if page > paginator.num_pages:
            page = 1
        # 获取第page页的Page实例对象
        order_page = paginator.page(page)
        # todo: 进行页码的控制， 页面上最多显示5个页码
        # 1.总页数小于5页 页面上显示所有页码
        # 2.如果当前页是前3页，显示前五页的页码
        # 3.如果当前页是后3页， 显示后5页的页码
        # 4.其他情况，显示当前页的前两页,当前页，当前页的后两页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        # 组织模板上下文
        context = {
            'order_page': order_page,
            'pages': pages,
            'page': 'order',
        }
        # 使用模板
        return render(request, 'user_center_order.html', context)


# /user/address
class AddressView(LoginRequiredMixin, View):
    '''用户中心-地址页'''

    def get(self, request):
        '''显示'''
        # 获取用户默认的收货地址
        user = request.user
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        #     try:
        #         address_list = Address.objects.filter(user=user, is_default=False)
        #     except Address.DoesNotExist:
        #         # 不存在默认收货地址
        #         address_list = None
        # except Address.DoesNotExist:
        #     # 不存在默认收货地址
        #     address = None
        address, address_list = Address.objects.get_address(user)
        return render(request, 'user_center_site.html',
                      {'page': 'address', 'address': address, 'address_list': address_list})

    def post(self, request):
        '''添加收货地址'''
        # 接收数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')
        # 校验数据 完整性
        if not all([receiver, addr, phone]):
            return redirect(reverse('user:address'), {'page': 'address', 'errmsg': '数据不完整'})
            # return render(request, 'user_center_site.html', {'page': 'address', 'errmsg': '数据不完整'})
        # 校验手机号
        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
            return redirect(reverse('user:address'), {'page': 'address', 'errmsg': '手机格式不正确'})
            # return render(request, 'user_center_site.html', {'page': 'address', 'errmsg': '手机格式不正确'})
        # 业务处理: 添加收货地址
        # 如果用户已存在默认收货地址， 添加的地址不作为默认收货地址， 否则作为默认收货地址
        # 获取登录用户对应的User对象
        user = request.user
        address, address_list = Address.objects.get_address(user)
        if address:
            is_default = False
        else:
            is_default = True
        # 添加地址
        Address.objects.create(
            user=user,
            addr=addr,
            receiver=receiver,
            is_default=is_default,
            phone=phone,
            zip_code=zip_code,
        )

        # 返回应答 刷新地址页面
        return redirect(reverse('user:address'))  # get请求方式
