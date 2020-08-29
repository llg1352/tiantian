from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings

class FDFSStorage(Storage):
    '''FDFS文件存储类'''

    def __init__(self, client_conf=None, Base_url=None):
        '''初始化'''
        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf
        if Base_url is None:
            Base_url = settings.FDFS_URL
        self.Base_url = Base_url

    def _open(self, name, mode=''):
        '''打开文件时使用'''
        pass

    def _save(self, name, content):
        '''保存文件时使用'''
        # name:你选择的上传文件的名字
        # content: 包含你上传文件内容的File对象
        # 创建一个Fdfs_client对象
        client = Fdfs_client(self.client_conf)
        '''return dict
        {
            'Group name': group_name,
            'Remote file_id': remote_file_id,
            'Status': 'Upload successed.',
            'Local file name': '',
            'Uploaded size': upload_size,
            'Storage IP': storage_ip
        } if success else None'''
        # 上传文件到fdfs文件系统中
        res = client.upload_by_buffer(content.read())
        print(res.get('Status'))
        if res.get('Status') != 'Upload successed.':
            # 上传失败
            print(res)
            print(11111)
            raise Exception('上传文件到fastdfs失败')
        # 获取返回的Remote file_id
        file_name = res.get('Remote file_id')
        return file_name

    def exists(self, name):
        '''Django判断文件名是否可用'''
        return False

    def url(self, name):
        '''返回访问文件的URl路径'''
        return self.Base_url + name
