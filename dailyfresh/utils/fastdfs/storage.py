from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client


class FastDFSStorage(Storage):
    def _open(self):
        # 访问文件的时候访问
        pass

    def _save(self, name, content):
        # 上传文件的时候访问
        # 把图片上传到fastdfs
        # 生成fdfs客户端对象 用来访问fdfs服务器
        client = Fdfs_client('./client.con')
        # 读取图片二进制信息
        file_data = content.read()
        # 上传到fdfs
        ret = client.upload_by_buffer(file_data)

        if ret.get('Status') == 'Upload successed.':
            # 判断上传是否成功 成功获取文件的真实路径
            file_id = ret.get('Remote file_id')
            return file_id
        else:
            raise Exception('上传文件到fdfs失败')

    # django不存储图片 直接返回False 引导存到FastFDS
    def exists(self, name):
        return False
