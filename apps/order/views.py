from django.shortcuts import render, redirect
from django.views.generic import View
from django.urls import reverse
from goods.models import GoodsSKU
from django_redis import get_redis_connection
from user.models import Address
from utils.mixin import LoginRequiredMixin
from django.http import JsonResponse
from order.models import OrderInfo, OrderGoods
from datetime import datetime
from django.db import transaction
from alipay import AliPay

alipay_public_key_string = '''-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAqPz6jsI6O/9MsuN1Vd1As9fZRJvHtcNflkHHmVoxRmgog2/+8mTShGD4hJLJPvzMunSayIvgAngMb9oFDwo1Et/EYbl4t88E5cSWSIROISMezxgzoAGpKqaFjiqMRudobo8DX9wds3WCKm3JArixfudN9dF/dHcSAx7S7EO0RF4ZZ9l80vpV3XQ81fA6MzpkZ6RHIkVdr5T8l8E544Jct1roO7aXKHWWpRjItWSYWOpqW5j+D9gSel95LYTZi+ryn/89nVgvG2am8kpapBiVQb3HrAEbVtp6pD3dlSLY/olidNv2HMsDhGmL0EU/u1aeMpZk06Xt2Lv5hBjcOXkIuQIDAQAB
-----END PUBLIC KEY-----'''

app_private_key_string = '''-----BEGIN RSA PRIVATE KEY-----
MIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQDWhYVKn/EKuU7T
FrELgxe7rPaI2i5SiG3mBrafhoePxH17I4Bhc6IFpdNcu0YvVkr103dfze3nZxRK
4+HCHslt/4mMO+7brnBtzN3P7w2H9VKymqBh3n8zuQlhXgXnBP+Wvp1Tsd0Cf+lr
70l5wsvqfQ2ceLJIaGTOosRCMetQqLjh7U2s+UdLYMzlfJo4asOejhC1GYei8Gbf
ThVpH6noITjBwhV+l2/ws2yTus1JD7+LtaTXsGACXsg+H9kTw7keKm5fyHhUdOKm
OGSUTHVfxEvkWvu780rFwDyRw7cghRCTbKLJuIr1+P+AyF3iFpG+fNXM1DBDIL2q
fJzVh7YZAgMBAAECggEAaaiT8SB74XNJ/rAjfW8RBm/3cYo83IuzzWMrGcFyDX6S
606eEeGZQLzfMMJQnEodW5zPJBHShnH/za8V572wKox9G+P9DpiJaZtI+PxeJsPO
+ocsTWgAMOKHWzyrHZEZrg6ugKWPHIcR2gaeoukt9I2pYZMVBJLea+RBU/UwWKYK
k/dgjUzwVB9ROZvR5Fhwv7hUhzIM63W1NOErNNbMbTHzHcxA0+D8AKOTKxgZN3R8
NZo5w24AVgIKPvraqBMzbIdyHuirDvCSYlubQy7FJYg61ytWtCSdy4Q63W5fg+5q
IqOdpIcnCJ+V3pdQ2rUmHne1Mz3giW0VFBTGrOvXPQKBgQDwpJomzB0e4IrbbQA8
Wosyxlst+cUtSL0R5LH3V+aGIPB8x8PF78+jJj/v4/77R9nLnuVx4o7/KFXNT52y
FFo4tDWHg8UWUaSCNCsHayfs+FrVAbJOFidoX1CDP1u5ygvu3H6ubxZYjHBCYZAM
bzNRfsCjekfHturmMUjNsMriuwKBgQDkNivp8LOylpG6K12niPqT2VsmDXb6Zp2B
QppnWSn3RzMEEer4a5/eesf30MmP4X1daaIubH/gVQgdHQ3FG5VpKauRZtQfh555
JpMIlHBfenV6B+CBLO+EqApNF5znmM6wcBG+hK05ar4eDzK9PqezFzvQhwrL1OZM
lkk1Ye2POwKBgQDdNEGrVkeSgY/C4nCsCgMYunNIUOeql8mM8C+TkU6Ljy3hVfQl
OCsi6t8tEeTqcYLIBRke1cbiz94Ha58m+kRxCV6HYl5CBOx276N6H0tFLoq4cOXJ
l93DuJIXA5+6qfrMKA2fJOhinz32Fx7F/1YqHJzR6W6gLAnDbhxhT5lATwKBgQDd
SuJeYXf/Dx6UhoS0dpF1WOmYBqp+uY61zx3mZYHaNQJ1SeKtrb9Cf5D071Lk4GUu
dcY8eh2uLQZHJOs7XToO1cd2oV3EjT/QfuVJBpfJHfhYstayrB4+ZqxGgUU3Fugm
EyZBtmo7KRTeFSLAe8cmVLs9xBVl/jarwXeP+jvgDQKBgQDjLHxDs39mnTj0U9cd
lmS/wE3yp/qaU/63mgIa955YgCFo9goaQZDBSK0I6lC4kXQGPqhQ4wkUuQK/HYPG
XxYGpTZetu+sN2jDlz3oUjITd8wzWiqFjQNrh1Kt6O5VnxsZXq9ff1QgghHiHdbu
xNE+6H60ZrG+nFRbz4Yp7430dw==
-----END RSA PRIVATE KEY-----'''


# Create your views here.
# /order/place
class OrderPlaceView(LoginRequiredMixin, View):  # LoginRequiredMixin
    '''提交订单页面'''

    def post(self, request):
        '''提交订单页面'''
        # 获取登录的用户
        user = request.user
        # 获取sku_ids
        sku_ids = request.POST.getlist('sku_ids')
        # 校验参数
        if not sku_ids:
            # 跳转到购物车页面
            return redirect(reverse('cart:show'))
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        # 遍历sku_ids获取用户要购买的商品信息
        skus = []
        # 保存商品的总件数和总价格
        total_count = 0
        total_price = 0
        for sku_id in sku_ids:
            # 根据商品id获取商品信息
            sku = GoodsSKU.objects.get(id=sku_id)
            count = conn.hget(cart_key, sku_id)
            # 计算商品小计
            amount = int(count) * sku.price
            # 动态给sku增加属性
            sku.count = int(count)
            sku.amount = amount
            # 追加
            skus.append(sku)
            # 累加计算商品的总件数和总价格
            total_count += int(count)
            total_price += amount
        # 运费：实际开发的时候， 属于一个子系统
        transit_price = 10

        # 实付款
        total_pay = total_price + transit_price
        # 获取用户收件地址
        addrs = Address.objects.filter(user=user)

        # 组织上下文
        sku_ids = ','.join(sku_ids)
        context = {
            'skus': skus,
            'total_price': total_price,
            'total_count': total_count,
            'transit_price': transit_price,
            'total_pay': total_pay,
            'addrs': addrs,
            'sku_ids': sku_ids,
        }
        # 使用模板
        return render(request, 'place_order.html', context)


# 悲观锁
# 前端传递的参数:地址id（addr_id）， 支付方式(pay_method)， 用户要购买的商品id字符串(sku_ids)
class OrderCommitView(LoginRequiredMixin, View):
    '''订单创建'''

    @transaction.atomic
    def post(self, request):
        '''订单创建'''
        # 判断用户是否登录
        user = request.user
        if not user.is_authenticated:
            # 用户未登录
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})
        # 接收参数
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')
        # 校验参数
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '参数不完整'})
        # 校验支付方式
        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res': 2, 'errmsg': '支付方式非法'})
        # 校验地址
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            # 地址不存在
            return JsonResponse({'res': 3, 'errmsg': '地址非法'})
        # todo: 创建订单的核心业务
        # 组织参数
        # 订单id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)
        # 运费
        transit_price = 10
        # 总数目,总金额
        total_count = 0
        total_price = 0
        # 设置事务保存点
        save_id = transaction.savepoint()
        # todo: 向订单信息表中添加记录
        try:
            order = OrderInfo.objects.create(
                order_id=order_id,
                user=user,
                addr=addr,
                pay_method=pay_method,
                total_price=total_price,
                total_count=total_count,
                transit_price=transit_price,
            )
            # todo:  向订单商品表添加记录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id

            sku_ids = sku_ids.split(',')
            for sku_id in sku_ids:
                # 获取商品信息
                try:
                    # select * from df_goods_sku where id=sku_id for update
                    sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
                except Exception as E:
                    print(E)
                    # 商品不存在 回滚保存点
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 4, 'errmsg': '商品不存在'})
                #  从redis中获取用户所要购买的商品的数量
                count = conn.hget(cart_key, sku_id)
                # todo: 判断商品库存
                if int(count) > sku.stock:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 6, 'errmsg': '商品库存不足'})
                # todo: 向订单商品表添加记录
                OrderGoods.objects.create(
                    order=order,
                    sku=sku,
                    count=count,
                    price=sku.price,
                )
                # 更新商品的销量库存
                sku.stock -= int(count)
                sku.sales += int(count)
                sku.save()

                # 累加计算订单商品的的总数量和总价格
                amount = sku.price * int(count)
                total_price += amount
                total_count += int(count)
            # todo:  更新订单信息表中的商品总数量和总价格
            order.total_count = total_count
            order.total_price = total_price
            order.save()
        except Exception as E:
            print(E)
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res': 7, 'errmsg': '下单失败'})
        # 提交事务
        transaction.savepoint_commit(save_id)
        # todo: 清除用户购物车中对应的记录  列表拆包传参 *[]
        conn.hdel(cart_key, *sku_ids)

        # 返回应答
        return JsonResponse({'res': 5, 'errmsg': '创建成功'})


# 乐观锁
class OrderCommitView1(LoginRequiredMixin, View):
    '''订单创建'''

    @transaction.atomic
    def post(self, request):
        '''订单创建'''
        # 判断用户是否登录
        user = request.user
        if not user.is_authenticated:
            # 用户未登录
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})
        # 接收参数
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')
        # 校验参数
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '参数不完整'})
        # 校验支付方式
        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res': 2, 'errmsg': '支付方式非法'})
        # 校验地址
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            # 地址不存在
            return JsonResponse({'res': 3, 'errmsg': '地址非法'})
        # todo: 创建订单的核心业务
        # 组织参数
        # 订单id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)
        # 运费
        transit_price = 10
        # 总数目,总金额
        total_count = 0
        total_price = 0
        # 设置事务保存点
        save_id = transaction.savepoint()
        # todo: 向订单信息表中添加记录
        try:
            order = OrderInfo.objects.create(
                order_id=order_id,
                user=user,
                addr=addr,
                pay_method=pay_method,
                total_price=total_price,
                total_count=total_count,
                transit_price=transit_price,
            )
            # todo:  向订单商品表添加记录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id

            sku_ids = sku_ids.split(',')
            for sku_id in sku_ids:
                for i in range(3):
                    # 获取商品信息
                    try:
                        sku = GoodsSKU.objects.get(id=sku_id)
                    except:
                        # 商品不存在 回滚保存点
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'res': 4, 'errmsg': '商品不存在'})
                    #  从redis中获取用户所要购买的商品的数量
                    count = conn.hget(cart_key, sku_id)
                    # todo: 判断商品库存
                    if int(count) > sku.stock:
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'res': 6, 'errmsg': '商品库存不足'})
                    # todo:更新商品的销量库存
                    orgin_stock = sku.stock
                    new_stock = orgin_stock - int(count)
                    new_sales = sku.sales + int(count)
                    # update df_goods_sku set stock=new_stock, sales=new_sales
                    # where id=sku_id and stock =orgin_stock
                    # 返回受影响的行数
                    res = GoodsSKU.objects.filter(id=sku_id, stock=orgin_stock).update(stock=new_stock, sales=new_sales)
                    if res == 0:
                        if i == 2:
                            transaction.savepoint_rollback(save_id)
                            return JsonResponse({'res': 7, 'errmsg': '下单失败2'})
                        continue
                    # todo: 向订单商品表添加记录
                    OrderGoods.objects.create(
                        order=order,
                        sku=sku,
                        count=count,
                        price=sku.price,
                    )

                    # 累加计算订单商品的的总数量和总价格
                    amount = sku.price * int(count)
                    total_price += amount
                    total_count += int(count)
                    break
            # todo:  更新订单信息表中的商品总数量和总价格
            order.total_count = total_count
            order.total_price = total_price
            order.save()
        except Exception as E:
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res': 7, 'errmsg': '下单失败'})
        # 提交事务
        transaction.savepoint_commit(save_id)
        # todo: 清除用户购物车中对应的记录  列表拆包传参 *[]
        conn.hdel(cart_key, *sku_ids)

        # 返回应答
        return JsonResponse({'res': 5, 'errmsg': '创建成功'})


# ajax post
# 前端传递的数据：订单id（order_id）
# /order/pay
class OrderPayView(LoginRequiredMixin, View):
    '''
    订单支付
    '''

    def post(self, request):
        '''
        订单支付
        '''

        # 用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})
        # 接收参数
        order_id = request.POST.get('order_id')
        # 校验参数
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的订单id'})
        try:
            order = OrderInfo.objects.get(
                order_id=order_id,
                user=user,
                pay_method=3,
                order_status=1
            )
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})
        # 业务处理：使用python sdk 调用支付宝的支付接口
        # 初始化
        alipay = AliPay(
            appid='2021000117625697',  # 应用id
            app_notify_url=None,  # 回调url
            app_private_key_string=app_private_key_string,  # 应用私钥
            alipay_public_key_string=alipay_public_key_string,  # alipay 公钥
            sign_type='RSA2',
            debug=True,
        )
        # 调用支付接口
        # 电脑网站支付， 需要跳转到
        total_pay = order.total_price + order.transit_price  # Decimal类型不能被序列化
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,  # 订单id
            total_amount=str(total_pay),  # 总金额
            subject='天天生鲜%s' % order_id,
            return_url=None,
            notify_url=None,
        )
        print(order_string)
        # 返回应答
        pay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
        return JsonResponse({'res': 3, 'pay_url': pay_url})


# ajax post
# 前端传递的数据：订单id（order_id）
# /order/check
class CheckPayView(LoginRequiredMixin, View):
    '''
    查看订单支付的结果
    '''

    def post(self, request):
        '''
        查询支付结果
        :param request:
        :return:
        '''
        # 用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})
        # 接收参数
        order_id = request.POST.get('order_id')
        # 校验参数
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的订单id'})
        try:
            order = OrderInfo.objects.get(
                order_id=order_id,
                user=user,
                pay_method=3,
                order_status=1,
            )
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})
        # 业务处理：使用python sdk 调用支付宝的支付接口
        # 初始化
        alipay = AliPay(
            appid='2021000117625697',  # 应用id
            app_notify_url=None,  # 回调url
            app_private_key_string=app_private_key_string,  # 应用私钥
            alipay_public_key_string=alipay_public_key_string,  # alipay 公钥
            sign_type='RSA2',
            debug=True,
        )
        # 调用支付宝的交易查询接口
        # response = {
        #         "trade_no": "2017032121001004070200176844",
        #         "code": "10000",
        #         "invoice_amount": "20.00",
        #         "open_id": "20880072506750308812798160715407",
        #         "fund_bill_list": [
        #             {
        #                 "amount": "20.00",
        #                 "fund_channel": "ALIPAYACCOUNT"
        #             }
        #         ],
        #         "buyer_logon_id": "csq***@sandbox.com",
        #         "send_pay_date": "2017-03-21 13:29:17",
        #         "receipt_amount": "20.00",
        #         "out_trade_no": "out_trade_no15",
        #         "buyer_pay_amount": "20.00",
        #         "buyer_user_id": "2088102169481075",
        #         "msg": "Success",
        #         "point_amount": "0.00",
        #         "trade_status": "TRADE_SUCCESS",
        #         "total_amount": "20.00"
        # }
        while True:
            resp = alipay.api_alipay_trade_query(order_id)
            code = resp.get('code')
            if code == '10000' and resp.get('trade_status') == "TRADE_SUCCESS":
                # 支付成功
                # 获取支付宝交易号
                trade_no = resp.get('trade_no')
                # 更新订单状态
                order.trade_no = trade_no
                order.order_status = 4  # 待评价
                order.save()
                # 返回结果
                return JsonResponse({'res': 3, 'message': '支付成功'})
            elif code == '40004' or (code == '10000' and resp.get('trade_status') == "WAIT_BUYER_PAY"):
                # 等待买家付款
                # 业务处理失败, 可能一会成功
                import time
                time.sleep(5)
                continue
            else:
                # 支付出错
                return JsonResponse({'res': 4, 'errmsg': '支付失败'})


class CommentView(LoginRequiredMixin, View):
    """订单评论"""

    def get(self, request, order_id):
        """提供评论页面"""
        user = request.user

        # 校验数据
        if not order_id:
            return redirect(reverse('user:order'))

        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse("user:order"))

        # 根据订单的状态获取订单的状态标题
        order.status_name = OrderInfo.ORDER_STATUS[order.order_status]

        # 获取订单商品信息
        order_skus = OrderGoods.objects.filter(order_id=order_id)
        for order_sku in order_skus:
            # 计算商品的小计
            amount = order_sku.count * order_sku.price
            # 动态给order_sku增加属性amount,保存商品小计
            order_sku.amount = amount
        # 动态给order增加属性order_skus, 保存订单商品信息
        order.order_skus = order_skus

        # 使用模板
        return render(request, "order_comment.html", {"order": order})

    def post(self, request, order_id):
        """处理评论内容"""
        user = request.user
        # 校验数据
        if not order_id:
            return redirect(reverse('user:order'))

        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse("user:order"))

        # 获取评论条数
        total_count = request.POST.get("total_count")
        total_count = int(total_count)

        # 循环获取订单中商品的评论内容
        for i in range(1, total_count + 1):
            # 获取评论的商品的id
            sku_id = request.POST.get("sku_%d" % i)  # sku_1 sku_2
            # 获取评论的商品的内容
            content = request.POST.get('content_%d' % i, '')  # cotent_1 content_2 content_3
            try:
                order_goods = OrderGoods.objects.get(order=order, sku_id=sku_id)
            except OrderGoods.DoesNotExist:
                continue

            order_goods.comment = content
            order_goods.save()

        order.order_status = 5  # 已完成
        order.save()

        return redirect(reverse("user:order", kwargs={"page": 1}))
