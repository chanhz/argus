import urllib.parse
import requests
import json
import hmac
import hashlib
import base64
import time


# 钉钉机器人 Webhook 地址（替换为你自己的）
DINGTALK_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token="

# 钉钉机器人的 access_token 和 secret（从钉钉群机器人设置中获取）
ACCESS_TOKEN = ""
SECRET = (
    ""  # webhook 签名用的密钥
)


def get_dingtalk_signed_url(access_token, secret):
    timestamp = str(round(time.time() * 1000))
    secret_enc = secret.encode("utf-8")
    string_to_sign = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(
        secret_enc, string_to_sign.encode("utf-8"), digestmod=hashlib.sha256
    ).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code).decode("utf-8"))

    webhook_url = f"https://oapi.dingtalk.com/robot/send?access_token={access_token}&timestamp={timestamp}&sign={sign}"
    return webhook_url


def send_dingtalk_message(msg):
    webhook_url = get_dingtalk_signed_url(ACCESS_TOKEN, SECRET)
    headers = {"Content-Type": "application/json"}
    data = {
        "msgtype": "text",
        "text": {
            "content": msg,
            "mentioned_list": [],  # 可选：提醒特定人，如 ["user123"]
            "isAtAll": False,
        },
    }

    response = requests.post(webhook_url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        print("钉钉消息发送成功")
        return True
    else:
        print(f"钉钉消息发送失败: {response.text}")
        return False

