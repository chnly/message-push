
import smtplib
import ssl
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List
from message_push.logconfig import loggers
from message_push.utils import MailConfig

try:
    from .template import TemplateRender
except ImportError:
    from template import TemplateRender


# 邮件模板
class EmailTemplate:
    def __init__(self, subject: str, sender: str, dest: List[str], cc: List[str] = None, content: str = None):
        """
        初始化一个邮件模板
        :param subject: 邮件主题
        :param sender: 邮件发送者
        :param dest: 邮件接收者列表
        :param cc: 邮件抄送列表
        :param content: html内容
        """
        self.subject = Header(subject, 'utf8')
        self.sender = Header(sender)
        self.dest = dest
        self.cc = cc
        self.content = MIMEText(content, 'html', 'utf8')

    def new_mail(self):
        msg = MIMEMultipart()
        msg['Subject'] = self.subject
        msg['TO'] = ",".join(self.dest)
        if self.cc:
            msg['CC'] = ",".join(self.cc)
        msg.attach(self.content)
        return msg


# 邮件服务
class MailBox:
    def __init__(self, username, password, smtp_server="smtp.office365.com", smtp_port=587):
        """
        配置 smtp 服务
        :param username: 用户名
        :param password: 密码
        :param smtp_server: smtp服务器，默认"smtp.office365.com"
        :param smtp_port: smtp服务器端口号，默认587，使能TLS
        """
        self.username = username
        self.password = password
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self._context = ssl.create_default_context()

    # 发送邮件
    def send(self, mail: EmailTemplate):
        """
        发送邮件
        :param mail: 按照邮件格式的内容
        :return:
        """
        loggers.info("prepare to send email")
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.ehlo()
            server.starttls(context=self._context)
            server.login(self.username, self.password)
            server.sendmail(self.username, mail.dest, msg=mail.new_mail().as_string())
        loggers.info("send email successfully")


html_loader = TemplateRender(MailConfig.template_path)
email_sender = MailBox(MailConfig.address, MailConfig.password)


if __name__ == "__main__":
    htmlcontent = TemplateRender('./templates')
    contents = htmlcontent.render('test1.html', title="服务工单", service_no="202999999999",
                                  customer_name="xxx公司")
    new_mail = EmailTemplate("欢迎来我家", MailConfig.address,
                             ['zhaogang@smart-lifestyle.cn', '396276515@qq.com'], content=contents)

    sender = MailBox(MailConfig.address, MailConfig.password)

    sender.send(new_mail)
