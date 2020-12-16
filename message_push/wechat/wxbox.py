import httpx
import msal
import json
from typing import List, Optional, Mapping, Union
import threading
from message_push.logconfig import loggers

# try:
#     from ..caches import WxOpenIDCache
# except ImportError:
from message_push.caches import WxOpenIDCache
from message_push.utils import config


class WechatConfig:
    wx_token_center_url: str = config['wechat']['wx_token_center_url']
    default_color: str = config['wechat']['default_color']


class AzureB2CConfig:
    b2c_scope: str = config['azure']['b2c']['scope']
    b2c_client_id: str = config['azure']['b2c']['client_id']
    b2c_client_credential: str = config['azure']['b2c']['client_credential']
    b2c_authority: str = config['azure']['b2c']['authority']


class ParameterStruct:
    value: str
    color = "#0c74da"

    def __dict__(self):
        return {"value": self.value, "color": self.color}


# 微信公众号模板
class WXTemplate:
    """
    微信公众号模板
    参考：https://developers.weixin.qq.com/doc/offiaccount/Message_Management/Template_Message_Interface.html
    """

    def __init__(self, message: Mapping[str, Mapping[str, Union[str, int]]], miniprogram: Optional[dict] = None):
        """
        初始化模板

        :param message: 根据模板id查看具体需要的字段信息
        {
            "keyword1": {
                "value": "Company",
            },
            # 设备信息
            "keyword2": {
                "value": "Device",
            },
            # 发生时间
            "keyword3": {
                "value": "2020-02-02",
            },
            # 告警描述
            "keyword4": {
                "value": "alarm",
                "color": "#ff0000"
            },
            # remark
            "remark": {
                "value": "remark",
            }
        }
        :param miniprogram: 如果关联小程序，需要填写完整信息
        {
            "appid": 'wxid',
            'pagepath': 'page/xx/xx'
        }
        """
        self.message = message
        self.miniprogram = miniprogram


class WXBox:
    def __init__(self):
        self.azure_authz = AzureClientAuthorization()
        self.wx_token_url = WechatConfig.wx_token_center_url
        self.wx_openid_cache = WxOpenIDCache()

    def send(self, to_users: List[str], template_id: str, msg: WXTemplate):
        """
        发送模板消息
        :param to_users: 微信开放平台unionid list
        :param template_id: 微信模板id
        :param msg: 微信模板消息内容
        :return:
        """
        loggers.info(f"prepare to send weixin message")
        task = []
        # 同一次消息使用获取一次token
        wx_token = self._get_wx_token()
        # 微信接口每次只能发送给一个用户
        for user in to_users:
            # 将微信unionid转化为公众号openid
            openid = self._get_wx_openid(to_user=user)
            if openid:
                # bytes to str
                openid = openid.decode('utf8')
                task.append(threading.Thread(target=self._send_wx_template_message,
                                             args=(openid, template_id, msg, wx_token),
                                             name=f"Thread_send_wx_message"))
        for t in task:
            t.start()
        for t in task:
            t.join()
        loggers.info(f"send wechat message successfully")

    def _get_wx_token(self):
        """
        从中控服务器获取token，中控服务器鉴权使用Azure B2C 客户端流
        :return: 获取到返回access_token, 失败返回None
        """
        _token = self.azure_authz.get_token()
        access_token = _token['token_type'] + ' ' + _token['access_token']
        with httpx.Client() as client:
            resp = client.get(
                url=self.wx_token_url,
                headers={
                    "Authorization": access_token,
                },

            )
            if resp.status_code == 200:
                loggers.info(f"get weixin token successfully")
                content = json.loads(resp.content.decode('utf8'))
                return content['access_token']

            else:
                loggers.error(f"get weixin token error, with code: {resp.status_code}, "
                              f"content: {resp.content.decode('utf8')}")

        return None

    def _get_wx_openid(self, to_user: str):
        """
        通过redis获取用户openid
        :param to_user: 用户union id
        :return: openid or None
        """
        openid = self.wx_openid_cache.read(to_user)
        if not openid:
            loggers.error(f"could not find the user@{to_user}'s openid")
        return openid

    @staticmethod
    def _send_wx_template_message(to_user: str, template_id: str, msg: WXTemplate, wx_token: None):
        """
        调用微信接口，发送模板消息
        :param to_user: openid
        :param template_id: 模板id
        :param msg: 模板内容
        :param wx_token: token
        :return:
        """
        # 默认字体颜色为绿色
        default_color = WechatConfig.default_color
        if not wx_token:
            loggers.error(f'could not get weixin token')
        else:
            template_data = {
                "touser": to_user,
                "data": {
                },
                "template_id": template_id
            }
            # 如果模板消息需要关联微信小程序
            if msg.miniprogram:
                template_data.update({
                    "miniprogram": msg.miniprogram
                })
            # 自定义颜色
            for keyword in msg.message:
                if "color" not in msg.message[keyword]:
                    msg.message[keyword]['color'] = default_color
            template_data.update({
                "data": msg.message
            })
            with httpx.Client() as client:

                resp = client.post(
                    url="https://api.weixin.qq.com/cgi-bin/message/template/send",
                    headers={
                        "Content-Type": "application/json; charset=utf-8",
                    },
                    params={
                        "access_token": wx_token
                    },
                    json=template_data
                )
                loggers.info(f"response from wechat, code: {resp.status_code}, content:{resp.content}, "
                             f"request data:{template_data}")


# 通过azure b2c获取 client credential相关信息
class AzureClientAuthorization:
    """
    使用Azure msal库获取client credential token
    """
    # TODO scope支持多个
    scope = [AzureB2CConfig.b2c_scope]
    client_id = AzureB2CConfig.b2c_client_id
    client_credential = AzureB2CConfig.b2c_client_credential
    authority = AzureB2CConfig.b2c_authority

    def __init__(self):
        self.app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_credential,
            authority=self.authority
        )
        # get new token
        self._access_token = self.app.acquire_token_for_client(scopes=self.scope)
        # self._access_token = None

    def get_token(self):
        """
        刷新token，msal库会根据token是否过期，进行获取token
        :return: {'token_type': 'Bearer', 'expires_in': 3599, 'ext_expires_in': 3599, 'access_token': 'ey*****.***.**'}
        """
        # get access token
        # self._access_token = self.app.acquire_token_for_client(scopes=self.scope)
        temp = self.app.acquire_token_silent(scopes=self.scope, account=None)
        if not temp:
            loggers.info("No suitable token exists in cache. Let's get a new one from AAD.")
            temp = self.app.acquire_token_for_client(scopes=self.scope)

        self._access_token = temp
        return self._access_token


wx_sender = WXBox()

if __name__ == '__main__':
    import time

    authz = AzureClientAuthorization()
    token = authz.get_token()
    wx_box = WXBox()
    to_users = ['oGTnct0FO7uoNsqhEBrwDsj66GAA']
    template_id = 'fqeg3t58XdEB21bz9XFcEONxwvjBz77C7NkzgP8cy9Y'
    data = {
        "keyword1": {
            "value": "公司名称",
        },
        # 设备信息
        "keyword2": {
            "value": "设备名称",
        },
        # 发生时间
        "keyword3": {
            "value": "2020-02-02",
        },
        # 告警描述
        "keyword4": {
            "value": "故障啦",
            "color": "#ff0000"
        },
        # remark
        "remark": {
            "value": "remark",
        }
    }
    T = WXTemplate(message=data, miniprogram={
        "appid": 'wx5a817da31dd98049',
        'pagepath': 'pages/event/event'
    })
    wx_box.send(to_users=to_users, template_id=template_id, msg=T)
    loggers.info('send wechat message successfully')

