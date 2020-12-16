from jinja2 import Environment, select_autoescape
from jinja2 import BaseLoader, TemplateNotFound
from os.path import join, exists, getmtime


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


if __name__ == '__main__':
    templates = TemplateRender('./templates')
    print(templates.render('test1.html', title="服务工单", service_no="202009090999999999"))
