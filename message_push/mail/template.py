from jinja2 import Environment, select_autoescape
from jinja2 import BaseLoader, TemplateNotFound,Template
from os.path import join, exists, getmtime
from tempfile import NamedTemporaryFile
from azure.storage.blob import BlobClient
from azure.storage.blob import ContainerClient
import os
from fastapi import HTTPException


class CustomLoader(BaseLoader):
    """
    自定义模板加载器，可以从任意位置加载模板
    """
    def __init__(self, path):
        self.path = path

    def get_source(self, environment, template):

        path = join(self.path, template)
        if not exists(path):
            raise TemplateNotFound(template)
        mtime = getmtime(path)
        with open(path, encoding='utf8') as f:
            source = f.read()
        return source, path, lambda: mtime == getmtime(path)


class TemplateRender:
    """
    从指定位置加载模板，并装载变量
    """
    def __init__(self, path):
        self.path = path
        self.env = Environment(
            loader=CustomLoader(path),
            autoescape=select_autoescape(['html', 'xml'])
        )

    def render(self, template_name, **content):
        """

        :param template_name: 模板名字（html文件名字）
        :param content: 模板内变量{{var}}
        :return: 加载变量后的html 文本文件
        """
        template = self.env.get_template(template_name)
        return template.render(**content)

class TemplateAzure:
    """
    从指定位置加载模板，并装载变量
    """
    def __init__(self,conn_str,container_name):
        # Get container client by connection string
        self.container = ContainerClient.from_connection_string(
            conn_str=conn_str,
            container_name=container_name)

    def is_teplate_exist(self,filename):
        # try:
        # 遍历容器下的blob (获取blob列表)
        template_list = []
        blob_list = self.container.list_blobs()
        for blob in blob_list:
            template_list.append(blob.name)
        if filename in template_list:
            print("Template is existed on azure.")
            return True
        else:
            print("Template is not existed on azure.")
            #raise TemplateNotFound(self.filename)
            raise HTTPException(
                status_code=404,
                detail="Template is not existed on azure."
            )

    def get_template_content(self, filename,**content):
        try:
            # 获取"index.html" blob的client
            blob_client = self.container.get_blob_client(filename)
            # 读取blob内容为文本并打印
            text_strings = blob_client.download_blob().content_as_text()
            print(text_strings)
            template_azure = Template(text_strings)
            return template_azure.render(**content)
            template_save_local(filename, text_strings)
            return "success"
        except Exception as e:
            message = "Find template in azure blob error"
            return "error"


if __name__ == '__main__':
    templates = TemplateRender('./templates')
    print(templates.render('test1.html', title="服务工单", service_no="202009090999999999"))
