import datetime
from NLP import SparkApi

#以下密钥信息从控制台获取
appid = "17ff8185"     #填写控制台中获取的 APPID 信息
api_secret = "NDdlYTcxZjRkMzlkMThjZGUwMTAyNzIx"   #填写控制台中获取的 APISecret 信息
api_key ="26b6a2ddb94aac20783f88c7700d0e8a"    #填写控制台中获取的 APIKey 信息

#用于配置大模型版本，默认“general/generalv2”
domain = "generalv3"   # v3版本
# domain = "generalv2"    # v2.0版本
#云端环境的服务地址
Spark_url = "ws://spark-api.xf-yun.com/v3.1/chat"  # v3环境的地址
# Spark_url = "ws://spark-api.xf-yun.com/v1.1/chat"  # v1.5环境的地址
# Spark_url = "ws://spark-api.xf-yun.com/v2.1/chat"  # v2.0环境的地址


text =[]

# length = 0
class Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret,Text,Domain = "generalv3",Spark_url= "ws://spark-api.xf-yun.com/v3.1/chat",SavePath = "./"):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.Domain = Domain
        self.Spark_url = Spark_url
        self.Text = Text
        self.SavePath = SavePath

        # 公共参数(common)
        self.CommonArgs = {"app_id": self.APPID}
        # 业务参数(business)，更多个性化参数可在官网查看
        self.BusinessArgs = {"domain": "iat", "language": "zh_cn", "accent": "mandarin", "vinfo":1,"vad_eos":10000}



def getText(role,content):
    jsoncon = {}
    jsoncon["role"] = role
    jsoncon["content"] = content
    text.append(jsoncon)
    return text

def getlength(text):
    length = 0
    for content in text:
        temp = content["content"]
        leng = len(temp)
        length += leng
    return length

def checklen(text):
    while (getlength(text) > 8000):
        del text[0]
    return text
    
def OnTake(thisWS):
    with open(wsParam.SavePath + 'Answer.txt', 'a+', encoding='utf-8') as a:
        a.truncate(0)
    with open(wsParam.SavePath + 'Dialog' + datetime.datetime.now().strftime('%Y-%m-%d') + '.txt','a+',encoding='utf-8') as f:
        f.truncate(0)
        question = checklen(getText("user", wsParam.Text))
        f.write("我:" + text[0]["content"] + '\n')
        SparkApi.answer = ""
        print("星火:", end="")
        SparkApi.main(appid, api_key, api_secret, Spark_url, domain, question)
        getText("assistant", SparkApi.answer)
        f.write("星火:" + text[0]["content"] + '\n')
        print(text)
        with open(wsParam.SavePath + 'Answer.txt', 'a+',encoding='utf-8') as a:
            a.write(text[1]["content"] + '\n')
        print("文件关闭")

if __name__ == '__main__':
    text.clear

    wsParam = Ws_Param(APPID='17ff8185', APISecret='NDdlYTcxZjRkMzlkMThjZGUwMTAyNzIx',
                       APIKey='26b6a2ddb94aac20783f88c7700d0e8a',
                       Text="你好,介绍一下你自己吧",SavePath="./")

    with open('Dialog' + datetime.datetime.now().strftime('%Y-%m-%d') + '.txt','a+',encoding='utf-8') as f:
        f.truncate(0)
        while(1):
            Input = input("\n" +"我:")
            question = checklen(getText("user",Input))
            f.write("我:" + text[0]["content"] + '\n')
            SparkApi.answer =""
            print("星火:",end = "")
            SparkApi.main(appid,api_key,api_secret,Spark_url,domain,question)
            getText("assistant",SparkApi.answer)
            print(text)
            f.write("星火:" + text[1]["content"] + '\n')
        print("文件关闭")

