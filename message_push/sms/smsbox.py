import httpx
import json
import re
from typing import List, Dict, Optional
from message_push.logconfig import loggers
from message_push.utils import config


class SMSConfig:
    account: str = config['sms']['account']
    auth_key: str = config['sms']['auth_key']
    api_server: str = config['sms']['api_server']
    api_version: str = config['sms']['api_version']


# 短信模板
class SMSTemplate:
    def __init__(self, to_users: List[str], content: Optional[dict]):
        """
        短信模板
        :param to_users: 手机号列表
        :param content: 根据模板名称获取短信模板中变量，并赋值
        例如：模板为：
        {
          "templateName": "事件推送",
          "signature": "xxxxx",
          "tplType": 1,
          "message": "设备：$(name)  于 $(date)发生故障，故障内容：$(content)，请及时处理。",
          "state": "Active"
        },
        content 为 {"name": "xxx", "date": "2020-02-02", "content": "xxxxx"}
        """
        self.to_users = to_users
        self.content = content


# 短信服务
class SMSBox:
    def __init__(self, account: str, auth_key: str, server: str):
        """
        :param server: 短信服务器地址
        :param account: sms账户名
        :param auth_key: authorization信息
        """
        self.account = account
        self.auth_key = auth_key
        self.server = server

    def get_template_detail(self, template_name: str):
        pass

    def send(self, template_name: str, sms: SMSTemplate):
        """
        发送短信
        :param template_name: 短信模板名称，需要在短信平台添加并审核
        :param sms: 短信内容
        :return:
        """
        loggers.info("prepare to send sms message")
        with httpx.Client() as client:
            resp = client.post(
                url=self.server,
                params={
                    "api-version": SMSConfig.api_version,
                },
                headers={
                    "Account": self.account,
                    "Authorization": self.auth_key,
                    "Content-Type": "application/json"
                },
                json={
                    "extend": "10",
                    "messageBody": {
                        "templateParam": sms.content,
                        "templateName": template_name
                    },
                    "phoneNumber": sms.to_users

                }
            )
            if resp.status_code == 200:
                loggers.info(f"send sms message successfully, with content: {resp.content.decode('utf8')}")
            else:
                loggers.error(f"send sms message error, with code: {resp.status_code}, "
                              f"content: {resp.content.decode('utf8')}")
            loggers.info("send sms message successfully")


sms_sender = SMSBox(
    account=SMSConfig.account,
    auth_key=SMSConfig.auth_key,
    server=SMSConfig.api_server
)

if __name__ == '__main__':
    data = {
        'url': 'a.cn',
        'name': 'zhaogang',
        'date': '2020-09-01'
    }
    template_name = '预约成功通知'
    account = SMSConfig.account
    to_users = ["15011330721"]
    auth_key = SMSConfig.auth_key
    server = SMSConfig.api_server
    sender = SMSBox(account, auth_key, server)
    sms_template = SMSTemplate(
        to_users=to_users,
        content=data
    )
    sender.send(template_name, sms_template)
