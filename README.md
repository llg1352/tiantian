README.md
django框架搭建的电商商城demo

网站效果： http://49.234.122.69

## 功能模块
- 用户模块：注册、登录、激活、退出、个人中心、地址
- 商品模块：首页、详情、列表、搜索（haystack+whoosh）
- 购物车： 增加、删除、修改、查询
- 订单模块：确认订单页面、提交订单（下单）、请求支付、查询支付结果、评论

## 技术使用
- Django 自带的后台管理系统，方便网站内容管理
- django默认的认证系统 AbstractUser
- itsdangerous  生成签名的token （序列化工具 dumps  loads）
- celery异步发送邮件 （django提供邮件支持 配置参数  send_mail）
- 页面静态化 （缓解压力  celery  nginx）
- 缓存（缓解压力， 保存的位置、有效期、与数据库的一致性问题）
- FastDFS (分布式的图片存储服务， 修改了django的默认文件存储系统)
- 搜索（ whoosh  索引  分词）
- 购物车redis 哈希 历史记录redis list
- 订单支付与高并发的库存问题 （事务，悲观锁、乐观锁）
- nginx （负载均衡  提供静态文件）
