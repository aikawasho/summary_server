# -*- coding: utf-8 -*-
import socket
import threading
import wave
import time
from BertSum.src.bert_summary import Bertsum_pred
from tools.speech_t import speech_text
import os

# コマンドの定義
SET = 0
SUM = 1
WAV = 2
PLAY = 3


class StreamServer():
    def __init__(self, server_host, server_port):
        self.SERVER_HOST = server_host
        self.SERVER_PORT = int(server_port)
        self.CHUNK = 4048
        self.FORMAT = 8 # 16bit
        self.CHANNELS = 1             # monaural
        self.fs = 16000
        self.RATE = 2
        self.cla_dir = dict()

    def run(self):

        global addr

        # ソケットを生成しバインド
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.SERVER_HOST, self.SERVER_PORT))

        # コネクションの上限を5に設定し、リスニング開始
        server.listen(5)

        print('Server started on %s:%d' % (self.SERVER_HOST, self.SERVER_PORT))

        while True:
            # クライアント接続の認識
            client, addr = server.accept()
                
            if client:

                print('Connection received from %s:%d' % (addr[0], addr[1]))
                # client.send("")

                # クライアントのコネクションをハンドリングするスレッドの生成と実行
                client_handle_thread = threading.Thread(
                    target=self.client_handler,
                    args=(client,)
                ).start()


    def client_handler(self,client):
        global addr
        buff_list = bytes()
        r_packet = bytes()

    # パケットの受信
        while True:
            tmp = client.recv(4096)
            r_packet += tmp
            if len(tmp) < 4096:
                break
                
                
        r_cmd = int.from_bytes(r_packet[0:2], 'big')
        print(r_cmd)
        # WAV保存の処理
        if r_cmd == WAV:
            wav_id = int(time.time())
            output_path =  self.cla_dir[client.getpeername()[0]] +str(wav_id)+ ".wav"
            wf = wave.open(output_path, 'wb')
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.RATE)
            wf.setframerate(self.fs)
            wf.writeframes(r_packet[2:])
            wf.close()
            text = speech_text(output_path)
            if text:
                text += "。"
            print('テキスト化')
            print(text)
            pac = wav_id.to_bytes(4, 'big')
            pac += text.encode()
            client.sendall(pac)
            print('sending text complete')
            client.close()
            
        # WAV再生の処理
        elif r_cmd == PLAY:
            wav_id = int.from_bytes(r_packet[2:], byteorder = "big")
            input_path =  self.cla_dir[client.getpeername()[0]]  + str(wav_id)+ ".wav"
            print(input_path)
            waveFile = wave.open(input_path, 'r')
            data = waveFile.readframes(-1)
            waveFile.close()
            print('send wav')
            client.sendall(data)
            client.close()
            
        # 要約の処理
        elif r_cmd == SUM:
            text = r_packet[2:].decode()
            suma = Bertsum_pred(text)
            print('summary complete')
            suma = ''.join(suma)
            data = suma.encode()
            client.sendall(data)
            client.close()
            
        # スタートの処理
        elif r_cmd == SET:
            dir_path =  "./wav_file/" +str(int(time.time()))+"/"
            os.mkdir(dir_path)
            self.cla_dir[client.getpeername()[0]] = dir_path
            
        else:
            print('a')
            client.close()

        
       # パケットをもどす
    def decode_packet(self,pac):
        
        #r_cmd = int.from_bytes(settings_list[0:1], 'big')
        FORMAT = int.from_bytes(pac[1:3],'big')
        CHANNELS = int.from_bytes(pac[3:5],'big')
        fs = int.from_bytes(pac[5:7],'big')
        RATE = int.from_bytes(pac[7:9],'big')
        CHUNK = int.from_bytes(pac[9:13],'big')

        return FORMAT,CHANNELS,fs,RATE,CHUNK


if __name__ == '__main__':
    mss_server = StreamServer("127.0.0.1", 50005)
    mss_server.run()