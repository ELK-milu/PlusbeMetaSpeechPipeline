# coding=UTF-8
import io
import os
import argparse
import queue
import socket
import sys
import time
from ctypes import cdll

import IAT.iat_ws_python3 as IAT
import NLP.test as NLP
import TTS.tts_ws_python3_demo as TTS
import ATF.train.step1_LPC as LPC
import ATF.train.step5_inference as ATF

# 测试用暂存变量
step1_result = ""
step2_result = ""
step3_result = ""
step4_result = ""

# 计数器
i = 0
j = 0
k = 0
l = 0

# 消费者锁
IATLock = False
NLPLock = False
TTSLock = False
LPCLock = False
ATFLock = False

# 使用消息队列来接收流式信息
step2_result_Queue = queue.Queue()
step3_result_Queue = queue.Queue()
step4_LPC_result_Queue = queue.Queue()
step4_ATF_result_Queue = queue.Queue()
# 有时NLP流式传输返回值只有几个字，需要等待拼接
step2_resultTemp = []


# 使用callback获取ws在On_message时的流式信息回调
# 本质上视为一个两两相连的生产者消费者问题，上一个流程的消费者生产给下一个流程的生产者



def IAT_CallBack(response):
    # 由于讯飞的IAT流式传输是动态修正的，所以还是选择等待最终结果
    print("+++++++" + response + "+++++++")
    Step2_NLP(response)


def NLP_CallBack(response):
    global i
    global step2_resultTemp

    '''
    global NLPLock
    while NLPLock:
        NLP_CallBack(response)
        return
    '''

    if ('。' in response):
        if(response.index("。") != (len(response)-1)):
            head = response[0:response.index('。') + 1]
            tail = response[response.index('。') + 1:]
            response = ""
            for words in step2_resultTemp:
                response += words
            response += head
            step2_resultTemp.clear()
            step2_resultTemp.append(tail)
        else:
            tail = response
            response = ""
            for words in step2_resultTemp:
                response += words
            response += tail
            step2_resultTemp.clear()
        # 设定存取阻塞
        step2_result_Queue.put(response, timeout=10)
        while step2_result_Queue.qsize() > 0:
            i += 1
            print("start=====" + response + "======End")
            # 获取NLP回调信息后调用TTS
            Step3_TTS(step2_result_Queue.get(timeout=10), i)
    else:
        step2_resultTemp.append(response)
        print("RES=====" + response + "======RES")


def TTS_CallBack(response):
    global j
    '''
    global NLPLock
    NLPLock = False
    while TTSLock:
        TTS_CallBack(response)
        return
    '''

    # 设定存取阻塞
    step3_result_Queue.put(response, timeout=10)
    while step3_result_Queue.qsize() > 0:
        j += 1
        # 获取TTS回调信息后调用LPC
        Step4_LPC(step3_result_Queue.get(timeout=10), j)


def LPC_CallBack(response):
    global k
    '''
    global TTSLock
    TTSLock = False
    while LPCLock:
        LPC_CallBack(response)
        return
    '''
    # 设定存取阻塞
    step4_LPC_result_Queue.put(response, timeout=10)
    while step4_LPC_result_Queue.qsize() > 0:
        k += 1
        # 获取LPC回调信息后调用ATF
        Step4_ATF(step4_LPC_result_Queue.get(timeout=10), k)


def ATF_CallBack(response):

    '''
    global LPCLock
    LPCLock = False
    while ATFLock:
        ATF_CallBack(response)
        return
    '''
    # 设定存取阻塞
    step4_ATF_result_Queue.put(response, timeout=10)
    while step4_ATF_result_Queue.qsize() > 0:
        # 获取ATF回调信息后调用UDP
        Final(step4_ATF_result_Queue.get(timeout=10))


# 流水线逐步调用
def Step1_IAR(wavPath):
    # step1--IAR 语音识别
    step1 = IAT.Ws_Param(APPID='17ff8185', APIKey='26b6a2ddb94aac20783f88c7700d0e8a',
                         APISecret='NDdlYTcxZjRkMzlkMThjZGUwMTAyNzIx', AudioFile=wavPath, SavePath="./IAT/")
    IAT.wsParam = step1
    IAT.OnTake(step1, IAT_CallBack)


def Step2_NLP(s1_result):
    step2 = NLP.Ws_Param(APPID='17ff8185', APIKey='26b6a2ddb94aac20783f88c7700d0e8a',
                         APISecret='NDdlYTcxZjRkMzlkMThjZGUwMTAyNzIx',
                         Text=s1_result, SavePath="./NLP/")
    NLP.wsParam = step2
    NLP.OnTake(step2, NLP_CallBack)


def Step3_TTS(s2_result, index):
    step3 = TTS.Ws_Param(APPID='17ff8185', APISecret='NDdlYTcxZjRkMzlkMThjZGUwMTAyNzIx',
                         APIKey='26b6a2ddb94aac20783f88c7700d0e8a',
                         Text=s2_result, SavePath="./TTS/sequence/", Index=index, OnRecvCallback=TTS_CallBack)
    TTS.wsParam = step3
    TTS.OnTake(step3)



def Step4_LPC(s3_result, index):
    # 模拟base64解码为python二进制字符串
    #memory_wav = io.BytesIO(s3_result)
    # step4--ATF 语音转脸型
    # Ⅰ. LPC编码wav
    step4_LPC = LPC.Ws_Param(Wave=None,WavePath=s3_result, Index=index, SavePath="./ATF/train/lpc/", Project_dir="./ATF/train/")
    LPC.wsParam = step4_LPC
    LPC.OnTake(thisWS= step4_LPC, _callback= LPC_CallBack)


def Step4_ATF(s4_LPC_result, index):
    # Ⅱ. ATF模型正向推理
    step4_ATF = ATF.tfliteInference(model_path='./ATF/AiSpeech/best_model/Audio2Face.tflite',
                                    pb_model_path='./ATF/AiSpeech/best_model/Audio2Face',
                                    NpyPath='./ATF/train/lpc/', Index=index, SavePath='./ATF/train/save/')
    ATF.OnTake(thisTF = step4_ATF,data= s4_LPC_result, _callback=ATF_CallBack)


def Final(s4_ATF_result):
    '''
    global ATFLock
    ATFLock = False
    '''
    try:
        msg = s4_ATF_result.encode('utf-8')
        sent = sock.sendto(msg, ('localhost', 9008))
    finally:
        print(f'socket send successfully!')


if __name__ == "__main__":
    # START 在命令行中接收初始wave的路径
    parser = argparse.ArgumentParser()
    parser.add_argument('--wavPath', type=str, default=None)
    args = parser.parse_args()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    LPC.dll = cdll.LoadLibrary("./ATF/train/LPC.dll")  # 加载 LPC.dll

    # step1--IAR 语音识别
    Step1_IAR(args.wavPath)
    #Step3_TTS("是的，语音听写是一种将人类语音转换为文字的技术。")

    #NLP_CallBack("是的，语音听写是一种将人类语音转换为文字的技术。")
    '''
    # step3--TTS 文本转语音
    step3 = TTS.Ws_Param(APPID='17ff8185', APISecret='NDdlYTcxZjRkMzlkMThjZGUwMTAyNzIx',APIKey='26b6a2ddb94aac20783f88c7700d0e8a',
                       Text="你好",SavePath="./TTS/sequence/",Index= 1,OnRecvCallback= TTS_CallBack)
    TTS.wsParam = step3
    TTS.OnTake(step3)

    step3_result = r'./TTS/demo.wav'

    # step4--ATF 语音转脸型
    # Ⅰ. LPC编码wav
    step4_LPC = LPC.Ws_Param(WavePath=step3_result ,SavePath="./ATF/train/lpc/",Project_dir="./ATF/train/")
    LPC.wsParam = step4_LPC
    LPC.OnTake(step4_LPC)

    step4_LPC_result = r'./ATF/train/lpc/demo.npy'

    # Ⅱ. ATF模型正向推理
    step4_ATF = ATF.tfliteInference(model_path='./ATF/AiSpeech/best_model/Audio2Face.tflite',pb_model_path='./ATF/AiSpeech/best_model/Audio2Face',
                        NpyPath=step4_LPC_result,SavePath='./ATF/train/save/')
    ATF.OnTake(step4_ATF)


    # FINAL 使用UDP通知程序处理权值
    FinalBlenderShape ='./ATF/train/save/weight.txt'
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        msg = "sender".encode('utf-8')
        sent = sock.sendto(msg, ('localhost', 9008))
        sock.close()
    finally:
        print(f'socket send successfully!')
        
    '''
    sock.close()
    with open('Log.txt', 'w', encoding='utf-8') as f:
        f.write(f'{args.wavPath} running successfully!')
    print(f'{args.wavPath} running successfully!')
