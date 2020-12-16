from fastapi.security.http import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import FastAPI, Response, status, Header, Depends, HTTPException
import datetime
import httpx
import json
from jose import jwt
from jose import exceptions as JoseExceptions
from logconfig import loggers

auth = HTTPBearer()

jwks_url = "https://login.chinacloudapi.cn/common/discovery/v2.0/keys"
appid = "41ebb163-adc1-4068-9087-eb79c718b633"
clientid = "09e38b75-8747-450f-a40e-9612ead4228c"


def has_access(token_property: HTTPAuthorizationCredentials = Depends(auth)):
    """
    用了解析token是否正确，auth已经保证了Authorization为 bearer token形式
    :param token_property:     scheme/credentials:
    :return: always True
    """
    authz.verify_token(token=token_property.credentials)
    return True


class AzureAuthorization:
    """
    校验 Azure B2C token，使用client credential 流，仅校验APP权限
    """

    def __init__(self, appid: str, clientid: str, jwks_url_config: str = jwks_url):
        self.clientid = clientid
        self.jwks_url = jwks_url_config
        self.appid = appid
        self._signing_algorithms = []
        self._jwks_last_updated = datetime.datetime(2000, 1, 1, 1, 0, 0)
        # jwks 3600s 更新一次
        self._jwks_cache_seconds = 3600
        self._jwks = {}

    def _refresh_jwks_cache(self):
        """
        刷新Azure B2c token公钥
        :return:
        """
        response = httpx.get(
            url=self.jwks_url,
            params={
                "appid": self.appid,
            },
        )
        loggers.info('Response HTTP Status Code: {status_code}'.format(
            status_code=response.status_code))
        # print('Response HTTP Response Body: {content}'.format(
        #     content=response.content))
        jwks = json.loads(response.content.decode('utf8'))
        for key in jwks['keys']:
            self._jwks[key['kid']] = key
        # 每次获取到公钥后，刷新时间，24小时候过期
        self._jwks_last_updated = datetime.datetime.now()

    def verify_token(self, token=None):
        """
        校验token，仅校验app权限
        :param token: Azure AD b2c token
        :return:
        """
        try:
            # 获取 type， alg， kid
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header['kid']
            alg = unverified_header['alg']
            loggers.info(unverified_header)
            now = datetime.datetime.now()

            if not (0 < (now - self._jwks_last_updated).total_seconds() < self._jwks_cache_seconds):
                loggers.info(f"jwks config is out of date (last updated at {self._jwks_last_updated})")
                self._refresh_jwks_cache()

            public_key = self._jwks.get(kid, None)
            if not public_key:
                loggers.error('could not found the kid')
                raise HTTPException(
                    status_code=401,
                    detail="Authorization token is not belong to this APP"
                )
            payload = jwt.decode(token, key=public_key, algorithms=alg, audience=self.clientid)
            # 成功后解析token
            loggers.info(f"client info: {payload}")
            # process payload
        except JoseExceptions.ExpiredSignatureError:
            loggers.error('Authorization token expired')
            raise HTTPException(
                status_code=401,
                detail="Authorization token expired"
            )
        except JoseExceptions.JWTClaimsError:
            loggers.error('Invalid audience')
            raise HTTPException(
                status_code=401,
                detail="Invalid audience"
            )
        except JoseExceptions.JWTError as e:
            loggers.error(f'Unable to decode authorization token as {e}')
            raise HTTPException(
                status_code=401,
                detail=f"{e}"
            )


authz = AzureAuthorization(appid=appid, clientid=clientid)

if __name__ == '__main__':
    auths = AzureAuthorization(appid=appid, clientid=clientid)
    # auths._refresh_jwks_cache()
    auths.verify_token()
