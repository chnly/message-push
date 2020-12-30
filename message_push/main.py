from typing import List, Optional
from fastapi import FastAPI, Response, status, Header, Depends, BackgroundTasks
from message_push.models import EmailModel, SMSModel, WechatModel
import uvicorn
from fastapi.security.oauth2 import get_authorization_scheme_param
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
from message_push.authorize import has_access
from mail.mailbox import email_sender, EmailTemplate,html_loader
from sms.smsbox import sms_sender, SMSTemplate
from wechat.wxbox import wx_sender, WXTemplate


app = FastAPI()


@app.get("/")
def read_root():
    return {"hello": "FastAPI"}


@app.post("/api/v1/services/sms/messages", dependencies=[Depends(has_access)])
async def push_sms_message(params: SMSModel, response: Response, background_tasks: BackgroundTasks):
    params_dict = params.dict()
    template_name = params_dict['template_name']
    to_users = params_dict['to_users']
    template_params = params_dict['message']
    new_sms = SMSTemplate(to_users, template_params)
    background_tasks.add_task(sms_sender.send, template_name, new_sms)
    return "success"


@app.post("/api/v1/services/email/messages", dependencies=[Depends(has_access)])
async def push_email_message(params: EmailModel, response: Response, background_tasks: BackgroundTasks):
    params_dict = params.dict()
    template_name = params_dict['template_name']
    subject = params_dict['subject']
    to_users = params_dict['to_users']
    cc_users = params_dict['cc_users']
    #priority = params_dict['priority']
    template_params = params_dict['message']
    html_file = template_name + ".html"
    if not html_loader.is_teplate_exist(html_file):
        return "error"
    else:
        content = html_loader.get_template_content(html_file, **template_params)
        #content = html_loader.render(html_file, **template_params)
        sender = "digital.service@cn.abb.com"
        new_email = EmailTemplate(subject, sender, to_users, cc_users, content)
        background_tasks.add_task(email_sender.send, new_email)

    return "success"


@app.post("/api/v1/services/wechat/messages", dependencies=[Depends(has_access)])
async def push_wechat_message(params: WechatModel, response: Response, background_tasks: BackgroundTasks):
    params_dict = params.dict()
    template_id = params_dict['template_id']
    to_users = params_dict['to_users']
    message = params_dict['message']
    miniprogram = params_dict['miniprogram']
    new_wx_messages = WXTemplate(message=message, miniprogram=miniprogram)
    background_tasks.add_task(wx_sender.send, to_users, template_id, new_wx_messages)
    return "success"


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
