from typing import Optional, List, Dict
from pydantic import BaseModel
from enum import Enum


class PriorityEnum(Enum):
    """
    优先级定义
    """
    High = "high"
    Normal = "none"
    Low = "low"


class EmailModel(BaseModel):
    """
    发送邮件消息格式 \n
    subject: 邮件主题 \n
    template_name: 模板名称，需要和html文件名保持一致 \n
    to_users: 接收对象邮箱列表 \n
    cc_users: cc对象邮箱列表 \n
    message: 消息模板 \n
    priority: 优先级（high，none，low）\n
    """
    subject: str
    template_name: str
    to_users: List[str]
    cc_users: Optional[List[str]] = None
    message: Dict
    #priority: Optional[PriorityEnum] = "none"


class SMSModel(BaseModel):
    """
    发送短信消息格式 \n
    template_name: 模板名称，需要和平台注册的保持一致 \n
    to_users: 接收对象手机号列表 \n
    message: 消息模板 \n
    """
    template_name: str
    to_users: List[str]
    message: Dict


class WechatModel(BaseModel):
    """
    发送微信公众号消息格式 \n
    template_id: 模板id，需要和微信提供的模板id保持一致 \n
    to_users: 接收对象邮箱列表 \n
    message: 消息模板 \n
    miniprogram: 关联小程序 \n
    """
    template_id: str
    to_users: List[str]
    message: Dict
    miniprogram: Optional[Dict] = None

