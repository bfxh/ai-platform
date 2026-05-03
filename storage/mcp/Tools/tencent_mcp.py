#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tencent_mcp.py - 腾讯云 + 微信全量 MCP 工具
统一入口: python /python\ai.py tencent <action> [args]

覆盖范围:
  腾讯云: COS / CVM / SCF / NLP / OCR / SMS / TTS / ASR / VPC / CDB / CDN
  微信:   小程序登录 / 支付 / 云开发(数据库/存储/云函数) / 公众号

配置 (/python\tencent_config.json):
{
  "secret_id":  "your_secret_id",
  "secret_key": "your_secret_key",
  "region":     "ap-guangzhou",
  "wx": {
    "appid":        "wx_appid",
    "appsecret":    "wx_appsecret",
    "mch_id":       "mch_id",
    "pay_key":      "pay_key",
    "cloudbase_env": "your_env_id"
  }
}
"""

import sys
import os
import json
import argparse
import traceback
import subprocess


CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tencent_config.json")

# ─────────────────────────────────────────────
# 配置加载
# ─────────────────────────────────────────────
def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_credential():
    cfg = load_config()
    secret_id  = cfg.get("secret_id")  or os.environ.get("TENCENTCLOUD_SECRET_ID", "")
    secret_key = cfg.get("secret_key") or os.environ.get("TENCENTCLOUD_SECRET_KEY", "")
    region     = cfg.get("region", "ap-guangzhou")
    return secret_id, secret_key, region

# ─────────────────────────────────────────────
# 依赖检查 & 安装
# ─────────────────────────────────────────────
def ensure_pkg(pkg_name, import_name=None):
    import importlib
    import subprocess
    import_name = import_name or pkg_name
    try:
        importlib.import_module(import_name)
    except ImportError:
        print(f"[tencent] 安装 {pkg_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg_name, "-q"])

# ─────────────────────────────────────────────
# ══════════════ 腾讯云 API ══════════════
# ─────────────────────────────────────────────

# ---------- COS 对象存储 ----------
def cos_action(args):
    """
    动作: upload / download / list / delete / url
    例:
      tencent cos upload ./file.png my-bucket ap-guangzhou output/file.png
      tencent cos list my-bucket ap-guangzhou [prefix]
      tencent cos download my-bucket key ./local.png
      tencent cos delete my-bucket key
      tencent cos url my-bucket key [expires=3600]
    """
    ensure_pkg("cos-python-sdk-v5", "qcloud_cos")
    try:
        from qcloud_cos import CosConfig, CosS3Client
    except ImportError:
        pass  # pip install tencentcloud-sdk-python qcloud-cos-sdk
    secret_id, secret_key, default_region = get_credential()

    action = args[0] if args else "help"

    if action == "upload":
        # upload local_path bucket [region] [cos_key]
        local_path = args[1]
        bucket     = args[2]
        region     = args[3] if len(args) > 3 else default_region
        cos_key    = args[4] if len(args) > 4 else os.path.basename(local_path)
        cfg = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
        client = CosS3Client(cfg)
        with open(local_path, "rb") as fp:
            resp = client.put_object(Bucket=bucket, Body=fp, Key=cos_key)
        print(json.dumps({"status": "ok", "etag": resp.get("ETag"), "key": cos_key}))

    elif action == "download":
        bucket = args[1]; cos_key = args[2]; local_path = args[3]
        region = args[4] if len(args) > 4 else default_region
        cfg = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
        client = CosS3Client(cfg)
        resp = client.get_object(Bucket=bucket, Key=cos_key)
        resp["Body"].get_stream_to_file(local_path)
        print(json.dumps({"status": "ok", "saved": local_path}))

    elif action == "list":
        bucket = args[1]
        region = args[2] if len(args) > 2 else default_region
        prefix = args[3] if len(args) > 3 else ""
        cfg = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
        client = CosS3Client(cfg)
        resp = client.list_objects(Bucket=bucket, Prefix=prefix)
        items = [c["Key"] for c in resp.get("Contents", [])]
        print(json.dumps({"status": "ok", "count": len(items), "keys": items}))

    elif action == "delete":
        bucket = args[1]; cos_key = args[2]
        region = args[3] if len(args) > 3 else default_region
        cfg = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
        client = CosS3Client(cfg)
        client.delete_object(Bucket=bucket, Key=cos_key)
        print(json.dumps({"status": "ok", "deleted": cos_key}))

    elif action == "url":
        bucket = args[1]; cos_key = args[2]
        expires = int(args[3]) if len(args) > 3 else 3600
        region  = args[4] if len(args) > 4 else default_region
        cfg = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
        client = CosS3Client(cfg)
        url = client.get_presigned_download_url(Bucket=bucket, Key=cos_key, Expired=expires)
        print(json.dumps({"status": "ok", "url": url, "expires": expires}))

    else:
        print("cos 动作: upload / download / list / delete / url")


# ---------- CVM 云服务器 ----------
def cvm_action(args):
    """
    动作: list / start / stop / reboot / describe
    例:
      tencent cvm list [region]
      tencent cvm start ins-xxxxxx [region]
      tencent cvm stop  ins-xxxxxx [region]
    """
    ensure_pkg("tencentcloud-sdk-python", "tencentcloud")
    try:
        from tencentcloud.common import credential as tc_cred
    except ImportError:
        tc_cred = None
    try:
        from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
    except ImportError:
        TencentCloudSDKException = None
    try:
        from tencentcloud.cvm.v20170312 import cvm_client, models
    except ImportError:
        cvm_client = None; models = None

    secret_id, secret_key, default_region = get_credential()
    action = args[0] if args else "list"
    region = args[2] if len(args) > 2 else default_region

    cred   = tc_cred.Credential(secret_id, secret_key)
    client = cvm_client.CvmClient(cred, region)

    if action == "list":
        req  = models.DescribeInstancesRequest()
        resp = client.DescribeInstances(req)
        instances = [{"id": i.InstanceId, "name": i.InstanceName, "state": i.InstanceState,
                      "ip": i.PublicIpAddresses} for i in resp.InstanceSet]
        print(json.dumps({"status": "ok", "instances": instances}, ensure_ascii=False))

    elif action in ("start", "stop", "reboot"):
        instance_id = args[1]
        if action == "start":
            req = models.StartInstancesRequest(); req.InstanceIds = [instance_id]
            client.StartInstances(req)
        elif action == "stop":
            req = models.StopInstancesRequest(); req.InstanceIds = [instance_id]
            client.StopInstances(req)
        else:
            req = models.RebootInstancesRequest(); req.InstanceIds = [instance_id]
            client.RebootInstances(req)
        print(json.dumps({"status": "ok", "action": action, "instance": instance_id}))

    else:
        print("cvm 动作: list / start ins-xxx / stop ins-xxx / reboot ins-xxx")


# ---------- SCF 云函数 ----------
def scf_action(args):
    """
    动作: list / invoke / log
    例:
      tencent scf list [namespace] [region]
      tencent scf invoke MyFunc '{"key":"val"}' [region]
      tencent scf log MyFunc [region]
    """
    ensure_pkg("tencentcloud-sdk-python", "tencentcloud")
    try:
        from tencentcloud.common import credential as tc_cred
    except ImportError:
        tc_cred = None
    try:
        from tencentcloud.scf.v20180416 import scf_client, models
    except ImportError:
        scf_client = None; models = None

    secret_id, secret_key, default_region = get_credential()
    action = args[0] if args else "list"
    region = default_region

    cred   = tc_cred.Credential(secret_id, secret_key)
    client = scf_client.ScfClient(cred, region)

    if action == "list":
        namespace = args[1] if len(args) > 1 else "default"
        req = models.ListFunctionsRequest(); req.Namespace = namespace
        resp = client.ListFunctions(req)
        fns = [{"name": f.FunctionName, "runtime": f.Runtime, "status": f.Status}
               for f in (resp.Functions or [])]
        print(json.dumps({"status": "ok", "functions": fns}, ensure_ascii=False))

    elif action == "invoke":
        func_name  = args[1]
        event_data = args[2] if len(args) > 2 else "{}"
        req = models.InvokeRequest()
        req.FunctionName = func_name
        req.ClientContext = event_data
        resp = client.Invoke(req)
        print(json.dumps({"status": "ok", "result": resp.Result.RetMsg}, ensure_ascii=False))

    else:
        print("scf 动作: list [ns] / invoke FuncName '{json}' / log FuncName")


# ---------- NLP 自然语言处理 ----------
def nlp_action(args):
    """
    动作: sentiment / keywords / classify / similar
    例:
      tencent nlp sentiment "这个产品真的很好用"
      tencent nlp keywords "腾讯云NLP支持多种文本分析功能"
    """
    ensure_pkg("tencentcloud-sdk-python", "tencentcloud")
    try:
        from tencentcloud.common import credential as tc_cred
    except ImportError:
        tc_cred = None
    try:
        from tencentcloud.nlp.v20190408 import nlp_client, models
    except ImportError:
        nlp_client = None; models = None

    secret_id, secret_key, _ = get_credential()
    action = args[0] if args else "sentiment"
    text   = args[1] if len(args) > 1 else ""

    cred   = tc_cred.Credential(secret_id, secret_key)
    client = nlp_client.NlpClient(cred, "ap-guangzhou")

    if action == "sentiment":
        req = models.SentimentAnalysisRequest(); req.Text = text; req.Mode = "2class"
        resp = client.SentimentAnalysis(req)
        print(json.dumps({"positive": resp.Positive, "negative": resp.Negative,
                          "sentiment": resp.Sentiment}, ensure_ascii=False))

    elif action == "keywords":
        req = models.KeywordsExtractionRequest(); req.Text = text; req.Num = 5
        resp = client.KeywordsExtraction(req)
        kws = [{"word": k.Word, "score": k.Score} for k in (resp.Keywords or [])]
        print(json.dumps({"keywords": kws}, ensure_ascii=False))

    elif action == "classify":
        req = models.TextClassificationRequest(); req.Text = text; req.Flag = 2
        resp = client.TextClassification(req)
        classes = [{"label": c.FirstClassName, "confidence": c.FirstClassProbability}
                   for c in (resp.Classes or [])]
        print(json.dumps({"classes": classes}, ensure_ascii=False))

    else:
        print("nlp 动作: sentiment / keywords / classify")


# ---------- OCR 文字识别 ----------
def ocr_action(args):
    """
    动作: general / id_card / bank_card / handwrite / table / formula
    例:
      tencent ocr general ./image.png
      tencent ocr id_card ./id.jpg
    """
    ensure_pkg("tencentcloud-sdk-python", "tencentcloud")
    import base64
    try:
        from tencentcloud.common import credential as tc_cred
    except ImportError:
        tc_cred = None
    try:
        from tencentcloud.ocr.v20181119 import ocr_client, models
    except ImportError:
        ocr_client = None; models = None

    secret_id, secret_key, _ = get_credential()
    action    = args[0] if args else "general"
    img_path  = args[1] if len(args) > 1 else ""

    cred   = tc_cred.Credential(secret_id, secret_key)
    client = ocr_client.OcrClient(cred, "ap-guangzhou")

    # 图片转 base64
    def to_b64(path):
        if path.startswith("http"):
            return None, path
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode(), None

    b64, url = to_b64(img_path)

    if action == "general":
        req = models.GeneralAccurateOCRRequest()
        if b64: req.ImageBase64 = b64
        else:   req.ImageUrl    = url
        resp = client.GeneralAccurateOCR(req)
        texts = [t.DetectedText for t in (resp.TextDetections or [])]
        print(json.dumps({"texts": texts, "full": "\n".join(texts)}, ensure_ascii=False))

    elif action == "id_card":
        req = models.IDCardOCRRequest()
        if b64: req.ImageBase64 = b64
        else:   req.ImageUrl    = url
        resp = client.IDCardOCR(req)
        print(json.dumps({"name": resp.Name, "sex": resp.Sex, "nation": resp.Nation,
                          "birth": resp.Birth, "address": resp.Address,
                          "id_num": resp.IdNum}, ensure_ascii=False))

    elif action == "bank_card":
        req = models.BankCardOCRRequest()
        if b64: req.ImageBase64 = b64
        else:   req.ImageUrl    = url
        resp = client.BankCardOCR(req)
        print(json.dumps({"card_no": resp.CardNo, "bank": resp.BankInfo,
                          "type": resp.CardType}, ensure_ascii=False))

    else:
        print("ocr 动作: general / id_card / bank_card / handwrite / table / formula")


# ---------- SMS 短信 ----------
def sms_action(args):
    """
    动作: send
    例:
      tencent sms send 1300000000 SMS_123456 '["code","123456"]' sdk_appid sign_name
    """
    ensure_pkg("tencentcloud-sdk-python", "tencentcloud")
    try:
        from tencentcloud.common import credential as tc_cred
    except ImportError:
        tc_cred = None
    try:
        from tencentcloud.sms.v20210111 import sms_client, models
    except ImportError:
        sms_client = None; models = None

    secret_id, secret_key, _ = get_credential()
    action = args[0] if args else "send"

    if action == "send":
        phone      = "+86" + args[1].lstrip("+86").lstrip("86")
        tpl_id     = args[2]
        tpl_params = json.loads(args[3]) if len(args) > 3 else []
        sdk_appid  = args[4] if len(args) > 4 else ""
        sign_name  = args[5] if len(args) > 5 else ""

        cred   = tc_cred.Credential(secret_id, secret_key)
        client = sms_client.SmsClient(cred, "ap-guangzhou")
        req = models.SendSmsRequest()
        req.SmsSdkAppId     = sdk_appid
        req.SignName        = sign_name
        req.TemplateId      = tpl_id
        req.TemplateParamSet = tpl_params
        req.PhoneNumberSet  = [phone]
        resp = client.SendSms(req)
        results = [{"phone": r.PhoneNumber, "code": r.Code, "message": r.Message}
                   for r in (resp.SendStatusSet or [])]
        print(json.dumps({"status": "ok", "results": results}, ensure_ascii=False))
    else:
        print("sms 动作: send phone tpl_id '[\"p1\",\"p2\"]' sdk_appid sign_name")


# ---------- TTS 语音合成 ----------
def tts_action(args):
    """
    动作: synth
    例:
      tencent tts synth "你好，欢迎使用腾讯云" ./output.mp3
    """
    ensure_pkg("tencentcloud-sdk-python", "tencentcloud")
    import base64
    try:
        from tencentcloud.common import credential as tc_cred
    except ImportError:
        tc_cred = None
    try:
        from tencentcloud.tts.v20190823 import tts_client, models
    except ImportError:
        tts_client = None; models = None

    secret_id, secret_key, _ = get_credential()
    action    = args[0] if args else "synth"
    text      = args[1] if len(args) > 1 else "你好"
    out_file  = args[2] if len(args) > 2 else "output.mp3"

    if action == "synth":
        cred   = tc_cred.Credential(secret_id, secret_key)
        client = tts_client.TtsClient(cred, "ap-guangzhou")
        req = models.TextToVoiceRequest()
        req.Text      = text
        req.SessionId = "tencent_mcp_tts"
        req.Volume    = 5
        req.Speed     = 0
        req.VoiceType = 101001  # 标准女声
        req.Codec     = "mp3"
        resp = client.TextToVoice(req)
        audio_bytes = base64.b64decode(resp.Audio)
        with open(out_file, "wb") as f:
            f.write(audio_bytes)
        print(json.dumps({"status": "ok", "saved": out_file, "size": len(audio_bytes)}))
    else:
        print("tts 动作: synth '文本' output.mp3")


# ---------- ASR 语音识别 ----------
def asr_action(args):
    """
    动作: file
    例:
      tencent asr file ./audio.mp3
      tencent asr file https://example.com/audio.wav
    """
    ensure_pkg("tencentcloud-sdk-python", "tencentcloud")
    import base64
    try:
        from tencentcloud.common import credential as tc_cred
    except ImportError:
        tc_cred = None
    try:
        from tencentcloud.asr.v20190614 import asr_client, models
    except ImportError:
        asr_client = None; models = None

    secret_id, secret_key, _ = get_credential()
    action   = args[0] if args else "file"
    src      = args[1] if len(args) > 1 else ""

    if action == "file":
        cred   = tc_cred.Credential(secret_id, secret_key)
        client = asr_client.AsrClient(cred, "ap-guangzhou")
        req = models.SentenceRecognitionRequest()
        req.EngSerViceType = "16k_zh"
        req.SourceType     = 0 if src.startswith("http") else 1
        if src.startswith("http"):
            req.Url = src
        else:
            with open(src, "rb") as f:
                req.Data = base64.b64encode(f.read()).decode()
            req.DataLen = os.path.getsize(src)
        resp = client.SentenceRecognition(req)
        print(json.dumps({"status": "ok", "text": resp.Result}, ensure_ascii=False))
    else:
        print("asr 动作: file <path_or_url>")


# ─────────────────────────────────────────────
# ══════════════ 微信 API ══════════════
# ─────────────────────────────────────────────

def _wx_cfg():
    cfg = load_config()
    return cfg.get("wx", {})

def _wx_access_token():
    """获取微信 access_token（自动缓存 1h）"""
    import time
    import urllib.request
    wx = _wx_cfg()
    cache_file = os.path.join(os.path.dirname(CONFIG_PATH), ".wx_token_cache.json")
    if os.path.exists(cache_file):
        with open(cache_file, encoding="utf-8") as f:
            cache = json.load(f)
        if cache.get("expires_at", 0) > time.time() + 300:
            return cache["access_token"]
    url = ("https://api.weixin.qq.com/cgi-bin/token"
           "?grant_type=client_credential"
           f"&appid={wx.get('appid','')}&secret={wx.get('appsecret','')}")
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read().decode('utf-8'))
    data["expires_at"] = time.time() + data.get("expires_in", 7200)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return data.get("access_token", "")


# ---------- 微信小程序 ----------
def wx_action(args):
    """
    动作: login / userinfo / qrcode / msg_send / template_send
    例:
      tencent wx login js_code
      tencent wx qrcode pages/index page=1 ./qr.jpg
      tencent wx msg_send openid tpl_id '{"key1":{"value":"val"}}'
    """
    import urllib.request
    import urllib.parse
    action = args[0] if args else "help"
    wx = _wx_cfg()

    if action == "login":
        js_code = args[1]
        url = ("https://api.weixin.qq.com/sns/jscode2session"
               f"?appid={wx.get('appid','')}&secret={wx.get('appsecret','')}"
               f"&js_code={js_code}&grant_type=authorization_code")
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode('utf-8'))
        print(json.dumps(data, ensure_ascii=False))

    elif action == "qrcode":
        # qrcode page scene ./output.jpg
        page    = args[1] if len(args) > 1 else "pages/index"
        scene   = args[2] if len(args) > 2 else ""
        out_jpg = args[3] if len(args) > 3 else "qrcode.jpg"
        token   = _wx_access_token()
        api_url = f"https://api.weixin.qq.com/wxa/getwxacodeunlimit?access_token={token}"
        body = json.dumps({"scene": scene, "page": page, "width": 430}).encode()
        req  = urllib.request.Request(api_url, data=body, method="POST",
                                      headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as r:
            content = r.read()
        if content[:4] == b'\xff\xd8\xff\xe0' or content[:4] == b'\xff\xd8\xff\xe1':
            with open(out_jpg, "wb") as f: f.write(content)
            print(json.dumps({"status": "ok", "saved": out_jpg}))
        else:
            print(json.dumps(json.loads(content), ensure_ascii=False))

    elif action == "template_send":
        # template_send openid tpl_id '{data_json}' [page]
        openid  = args[1]
        tpl_id  = args[2]
        data    = json.loads(args[3]) if len(args) > 3 else {}
        page    = args[4] if len(args) > 4 else ""
        token   = _wx_access_token()
        api_url = f"https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={token}"
        body = json.dumps({"touser": openid, "template_id": tpl_id,
                           "page": page, "data": data}).encode()
        req = urllib.request.Request(api_url, data=body, method="POST",
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode('utf-8'))
        print(json.dumps(data, ensure_ascii=False))

    elif action == "userinfo":
        # userinfo openid
        openid = args[1]
        token  = _wx_access_token()
        url    = (f"https://api.weixin.qq.com/cgi-bin/user/info"
                  f"?access_token={token}&openid={openid}&lang=zh_CN")
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode('utf-8'))
        print(json.dumps(data, ensure_ascii=False))

    else:
        print("wx 动作: login js_code / qrcode page scene out.jpg / "
              "template_send openid tpl_id '{data}' / userinfo openid")


# ---------- 微信支付 ----------
def wxpay_action(args):
    """
    动作: unified_order / query / refund / close
    例:
      tencent wxpay unified_order openid "商品名" 100 ORDER001
      tencent wxpay query ORDER001
      tencent wxpay refund ORDER001 REFUND001 100 100
    """
    import hashlib
    import random
    import string
    import urllib.request
    import xml.etree.ElementTree as ET

    def _defused_fromstring(xml_str):
        import io
        if '<!ENTITY' in xml_str or '<!DOCTYPE' in xml_str:
            raise ValueError("XML with entity declarations rejected for security")
        return ET.fromstring(xml_str)

    wx  = _wx_cfg()
    mch_id  = wx.get("mch_id", "")
    pay_key = wx.get("pay_key", "")
    appid   = wx.get("appid", "")
    action  = args[0] if args else "help"

    def dict_to_xml(d):
        xml = "<xml>"
        for k, v in d.items():
            xml += f"<{k}><![CDATA[{v}]]></{k}>"
        xml += "</xml>"
        return xml.encode()

    def xml_to_dict(xml_str):
        root = _defused_fromstring(xml_str)
        return {child.tag: child.text for child in root}

    def sign(params):
        items = sorted(params.items())
        s = "&".join(f"{k}={v}" for k, v in items if v) + f"&key={pay_key}"
        return hashlib.sha256(s.encode()).hexdigest().upper()

    def nonce_str(n=16):
        import secrets
        return "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(n))

    def wx_post(url, params):
        params["sign"] = sign(params)
        data = dict_to_xml(params)
        req  = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            return xml_to_dict(r.read().decode('utf-8'))

    if action == "unified_order":
        openid = args[1]; body = args[2]
        total_fee = args[3]; out_trade_no = args[4]
        notify_url = args[5] if len(args) > 5 else "https://example.com/notify"
        params = {
            "appid": appid, "mch_id": mch_id, "nonce_str": nonce_str(),
            "body": body, "out_trade_no": out_trade_no,
            "total_fee": str(total_fee), "spbill_create_ip": "127.0.0.1",
            "notify_url": notify_url, "trade_type": "JSAPI", "openid": openid,
        }
        result = wx_post("https://api.mch.weixin.qq.com/pay/unifiedorder", params)
        print(json.dumps(result, ensure_ascii=False))

    elif action == "query":
        out_trade_no = args[1]
        params = {"appid": appid, "mch_id": mch_id, "nonce_str": nonce_str(),
                  "out_trade_no": out_trade_no}
        result = wx_post("https://api.mch.weixin.qq.com/pay/orderquery", params)
        print(json.dumps(result, ensure_ascii=False))

    elif action == "refund":
        out_trade_no = args[1]; out_refund_no = args[2]
        total_fee = args[3]; refund_fee = args[4]
        params = {
            "appid": appid, "mch_id": mch_id, "nonce_str": nonce_str(),
            "out_trade_no": out_trade_no, "out_refund_no": out_refund_no,
            "total_fee": str(total_fee), "refund_fee": str(refund_fee),
        }
        result = wx_post("https://api.mch.weixin.qq.com/secapi/pay/refund", params)
        print(json.dumps(result, ensure_ascii=False))

    elif action == "close":
        out_trade_no = args[1]
        params = {"appid": appid, "mch_id": mch_id, "nonce_str": nonce_str(),
                  "out_trade_no": out_trade_no}
        result = wx_post("https://api.mch.weixin.qq.com/pay/closeorder", params)
        print(json.dumps(result, ensure_ascii=False))

    else:
        print("wxpay 动作: unified_order / query / refund / close")


# ---------- 微信云开发 CloudBase ----------
def cloudbase_action(args):
    """
    动作: call_func / db_get / db_add / db_update / db_delete / file_upload / file_download
    例:
      tencent cloudbase call_func myFunc '{"a":1}'
      tencent cloudbase db_get todos '{"done":false}'
      tencent cloudbase db_add todos '{"text":"buy milk","done":false}'
      tencent cloudbase file_upload ./local.png cloud://env-id/path/file.png
    """
    ensure_pkg("cloudbase", "cloudbase")
    import cloudbase.app as tcb

    wx      = _wx_cfg()
    env_id  = wx.get("cloudbase_env", "")
    action  = args[0] if args else "help"

    secret_id, secret_key, _ = get_credential()
    app = tcb.CloudBase(env_id, secret_id=secret_id, secret_key=secret_key)

    if action == "call_func":
        func_name = args[1]
        data      = json.loads(args[2]) if len(args) > 2 else {}
        result    = app.callFunction(func_name, data)
        print(json.dumps({"status": "ok", "result": result}, ensure_ascii=False, default=str))

    elif action == "db_get":
        collection = args[1]
        query      = json.loads(args[2]) if len(args) > 2 else {}
        db     = app.database()
        result = db.collection(collection).where(query).get()
        print(json.dumps({"status": "ok", "data": result}, ensure_ascii=False, default=str))

    elif action == "db_add":
        collection = args[1]
        doc        = json.loads(args[2])
        db     = app.database()
        result = db.collection(collection).add(doc)
        print(json.dumps({"status": "ok", "id": result}, ensure_ascii=False, default=str))

    elif action == "db_update":
        collection = args[1]
        query      = json.loads(args[2])
        update     = json.loads(args[3])
        db     = app.database()
        result = db.collection(collection).where(query).update(update)
        print(json.dumps({"status": "ok", "updated": result}, ensure_ascii=False, default=str))

    elif action == "db_delete":
        collection = args[1]
        query      = json.loads(args[2])
        db     = app.database()
        result = db.collection(collection).where(query).remove()
        print(json.dumps({"status": "ok", "deleted": result}, ensure_ascii=False, default=str))

    elif action == "file_upload":
        local_path  = args[1]
        cloud_path  = args[2]
        storage = app.storage()
        result  = storage.uploadFile({"localPath": local_path, "cloudPath": cloud_path})
        print(json.dumps({"status": "ok", "fileID": result}, ensure_ascii=False, default=str))

    elif action == "file_download":
        cloud_path = args[1]
        local_path = args[2]
        storage = app.storage()
        storage.downloadFile({"fileID": cloud_path, "tempFilePath": local_path})
        print(json.dumps({"status": "ok", "saved": local_path}))

    else:
        print("cloudbase 动作: call_func / db_get / db_add / db_update / db_delete / "
              "file_upload / file_download")


# ---------- 公众号 ----------
def mp_action(args):
    """
    动作: send_text / send_image / get_fans / create_tag / get_menu
    例:
      tencent mp send_text openid "Hello"
      tencent mp get_fans
      tencent mp get_menu
    """
    import urllib.request
    action = args[0] if args else "help"
    token  = _wx_access_token()

    def post_json(url, body_dict):
        data = json.dumps(body_dict, ensure_ascii=False).encode()
        req  = urllib.request.Request(url, data=data, method="POST",
                                      headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode('utf-8'))

    if action == "send_text":
        openid = args[1]; content = args[2]
        result = post_json(
            f"https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token={token}",
            {"touser": openid, "msgtype": "text", "text": {"content": content}}
        )
        print(json.dumps(result, ensure_ascii=False))

    elif action == "get_fans":
        req = urllib.request.Request(
            f"https://api.weixin.qq.com/cgi-bin/user/get?access_token={token}"
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            print(json.dumps(json.loads(r.read().decode('utf-8')), ensure_ascii=False))

    elif action == "get_menu":
        req = urllib.request.Request(
            f"https://api.weixin.qq.com/cgi-bin/get_current_selfmenu_info?access_token={token}"
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            print(json.dumps(json.loads(r.read().decode('utf-8')), ensure_ascii=False))

    elif action == "create_tag":
        tag_name = args[1]
        result   = post_json(
            f"https://api.weixin.qq.com/cgi-bin/tags/create?access_token={token}",
            {"tag": {"name": tag_name}}
        )
        print(json.dumps(result, ensure_ascii=False))

    else:
        print("mp 动作: send_text openid '文本' / get_fans / get_menu / create_tag name")


# ─────────────────────────────────────────────
# 工具: 配置向导
# ─────────────────────────────────────────────
def config_action(args):
    """初始化 / 查看 / 编辑 tencent_config.json"""
    action = args[0] if args else "show"

    if action == "show":
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, encoding="utf-8") as f:
                cfg = json.load(f)
            # 脱敏显示
            if cfg.get("secret_key"):
                cfg["secret_key"] = cfg["secret_key"][:4] + "****"
            if cfg.get("wx", {}).get("appsecret"):
                cfg["wx"]["appsecret"] = cfg["wx"]["appsecret"][:4] + "****"
            print(json.dumps(cfg, ensure_ascii=False, indent=2))
        else:
            print(f"配置文件不存在: {CONFIG_PATH}")
            print("运行: tencent config init  来创建初始配置")

    elif action == "init":
        template = {
            "secret_id": "your_secret_id",
            "secret_key": "your_secret_key",
            "region": "ap-guangzhou",
            "wx": {
                "appid": "wx_appid",
                "appsecret": "wx_appsecret",
                "mch_id": "mch_id",
                "pay_key": "pay_key",
                "cloudbase_env": "your_env_id"
            }
        }
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        print(f"已创建模板配置: {CONFIG_PATH}")
        print("请编辑填入真实的 SecretId/SecretKey 和微信配置")

    else:
        print("config 动作: show / init")


def docs_action(args):
    """离线腾讯文档: init / crawl / search / status"""
    script = os.path.join(os.path.dirname(__file__), "tencent_docs.py")
    cmd = [sys.executable, script] + args
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore", env=env)


    def _safe_write(stream, text):
        if not text:
            return
        try:
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="ignore")
            stream.write(text)
            stream.flush()
            return
        except Exception:
            pass
        enc = getattr(stream, "encoding", None) or "utf-8"
        clean = text.encode(enc, errors="ignore").decode(enc, errors="ignore")
        stream.write(clean)
        stream.flush()


    _safe_write(sys.stdout, result.stdout)
    _safe_write(sys.stderr, result.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"docs 子命令失败: {result.returncode}")



# ─────────────────────────────────────────────
# 帮助
# ─────────────────────────────────────────────

HELP = """
tencent_mcp.py - 腾讯云 + 微信全量工具

用法: python /python\\ai.py tencent <子命令> [参数]

━━ 腾讯云 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  cos        对象存储    upload/download/list/delete/url
  cvm        云服务器    list/start/stop/reboot
  scf        云函数      list/invoke
  nlp        NLP分析     sentiment/keywords/classify
  ocr        文字识别    general/id_card/bank_card
  sms        短信发送    send
  tts        语音合成    synth
  asr        语音识别    file

━━ 微信 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  wx         小程序      login/qrcode/template_send/userinfo
  wxpay      微信支付    unified_order/query/refund/close
  cloudbase  云开发      call_func/db_get/db_add/db_update/db_delete/file_upload
  mp         公众号      send_text/get_fans/get_menu/create_tag

━━ 工具 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  config     配置管理    show/init
  docs       离线文档    init/crawl/search/status

示例:
  python /python\\ai.py tencent config init
  python /python\\ai.py tencent docs init
  python /python\\ai.py tencent docs crawl --max-pages 1200 --per-product 220
  python /python\\ai.py tencent docs search 微信支付 回调签名
  python /python\\ai.py tencent cos list my-bucket
  python /python\\ai.py tencent ocr general ./image.png
  python /python\\ai.py tencent wx login js_code_here
  python /python\\ai.py tencent cloudbase db_get todos '{}'

"""

# ─────────────────────────────────────────────
# 主路由
# ─────────────────────────────────────────────
ACTIONS = {
    "cos":        cos_action,
    "cvm":        cvm_action,
    "scf":        scf_action,
    "nlp":        nlp_action,
    "ocr":        ocr_action,
    "sms":        sms_action,
    "tts":        tts_action,
    "asr":        asr_action,
    "wx":         wx_action,
    "wxpay":      wxpay_action,
    "cloudbase":  cloudbase_action,
    "mp":         mp_action,
    "config":     config_action,
    "docs":       docs_action,
}

def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(HELP)
        return
    sub = argv[0].lower()
    rest = argv[1:]
    if sub not in ACTIONS:
        print(f"未知子命令: {sub}")
        print("可用: " + " / ".join(ACTIONS))
        sys.exit(1)
    try:
        ACTIONS[sub](rest)
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(1)

if __name__ == "__main__":
    main()
