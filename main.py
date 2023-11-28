# coding=UTF-8
import os
import argparse
import socket
import sys
import time
from ctypes import cdll

import IAT.iat_ws_python3 as IAT
import NLP.test as NLP
import TTS.tts_ws_python3_demo as TTS
import ATF.train.step1_LPC as LPC
import ATF.train.step5_inference as ATF

if __name__ == "__main__":

    # START 在命令行中接收初始wave的路径
    parser = argparse.ArgumentParser()
    parser.add_argument('--wavPath', type=str, default=None)
    args = parser.parse_args()

    # step1--IAR 语音识别
    step1 = IAT.Ws_Param(APPID='17ff8185',APIKey='26b6a2ddb94aac20783f88c7700d0e8a',
                          APISecret='NDdlYTcxZjRkMzlkMThjZGUwMTAyNzIx',AudioFile=args.wavPath,SavePath="./IAT/")
    IAT.wsParam = step1
    IAT.OnTake(step1)

    with open('./IAT/result.txt', 'r', encoding='utf-8') as f:
        step1_result = f.read()

    # step2--NLP 应单独开辟线程，每当处理完音轨后触发对话
    # 此处暂且先处理一句
    print(step1_result)
    step2 = NLP.Ws_Param(APPID='17ff8185',APIKey='26b6a2ddb94aac20783f88c7700d0e8a',APISecret='NDdlYTcxZjRkMzlkMThjZGUwMTAyNzIx',
                    Text=step1_result,SavePath="./NLP/")
    NLP.wsParam = step2
    NLP.OnTake(step2)

    with open('./NLP/Answer.txt', 'r', encoding='utf-8') as f:
        step2_result = f.read()

    # step3--TTS 文本转语音
    print(step2_result)
    step3 = TTS.Ws_Param(APPID='17ff8185', APISecret='NDdlYTcxZjRkMzlkMThjZGUwMTAyNzIx',APIKey='26b6a2ddb94aac20783f88c7700d0e8a',
                       Text=step2_result,SavePath="./TTS/")
    TTS.wsParam = step3
    TTS.OnTake(step3)

    step3_result = r'./TTS/demo.wav'

    # step4--ATF 语音转脸型
    # Ⅰ. LPC编码wav
    step4_LPC = LPC.Ws_Param(WavePath=step3_result ,SavePath="./ATF/train/lpc/",Project_dir="./ATF/train/")
    LPC.wsParam = step4_LPC
    LPC.dll = cdll.LoadLibrary(os.path.join(step4_LPC.Project_dir, 'LPC.dll'))  # 加载 LPC.dll
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

    with open('Log.txt', 'w', encoding='utf-8') as f:
        f.write(f'{args.wavPath} running successfully!')
    print(f'{args.wavPath} running successfully!')
