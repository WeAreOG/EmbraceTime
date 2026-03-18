import socket
import requests
import os
import threading
import time
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Ze Manel está online e a tentar a PTNet!"

# --- CONFIGURAÇÃO DA IA ---
HF_TOKEN = os.getenv("HF_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"

# --- CONFIGURAÇÃO IRC (PTNET) ---
SERVIDORES = ["irc.ptnet.org", "portugal.ptnet.org", "62.28.161.4"]
PORTA = 6667
NICK_BASE = "Ze_Manel"
CHANNEL = "#TheOG"

def ask_ai(message, author):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    prompt = f"<|begin_of_text|>Tu és o {NICK_BASE}, um português engraçado. Responde curto em PT-PT a {author}: {message}<|eot_id|>"
    try:
        r = requests.post(API_URL, headers=headers, json={"inputs": prompt, "parameters": {"max_new_tokens": 50}}, timeout=10)
        return r.json()[0]['generated_text'].split("<|eot_id|>")[-1].strip()
    except:
        return "Agora não posso, estou a comer um prego!"

def run_irc():
    srv_idx = 0
    while True:
        server = SERVIDORES[srv_idx % len(SERVIDORES)]
        current_nick = f"{NICK_BASE}_{int(time.time()) % 100}"
        try:
            print(f">>> A TENTAR PTNET: {server} como {current_nick}")
            irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            irc.settimeout(30)
            irc.connect((server, PORTA))
            time.sleep(5)
            irc.send(f"NICK {current_nick}\r\n".encode('utf-8'))
            time.sleep(2)
            irc.send(f"USER {current_nick} 8 * :Utilizador PT\r\n".encode('utf-8'))
            irc.settimeout(None)
            while True:
                data = irc.recv(4096).decode("utf-8", errors="ignore")
                if not data: break
                if data.startswith("PING"):
                    irc.send(f"PONG {data.split()[1]}\r\n".encode('utf-8'))
                if any(x in data for x in [" 001 ", " 376 "]):
                    irc.send(f"JOIN {CHANNEL}\r\n".encode('utf-8'))
                if " PRIVMSG " in data:
                    user = data.split('!')[0][1:]
                    msg = data.split(" :", 1)[1] if " :" in data else ""
                    if NICK_BASE.lower() in msg.lower():
                        res = ask_ai(msg, user)
                        irc.send(f"PRIVMSG {CHANNEL} :{user}: {res}\r\n".encode('utf-8'))
        except Exception as e:
            print(f"Erro: {e}")
            srv_idx += 1
            time.sleep(30)

if __name__ == "__main__":
    # O Railway passa a porta na variável de ambiente PORT
    port = int(os.environ.get("PORT", 7860))
    threading.Thread(target=run_irc, daemon=True).start()
    app.run(host='0.0.0.0', port=port)
