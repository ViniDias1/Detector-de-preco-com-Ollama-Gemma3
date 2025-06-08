import tkinter as tk
from tkinter import filedialog
import base64
import requests
import json
import os

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma3:4b"  

def converter_imagem_para_base64(caminho):
    with open(caminho, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def enviar_para_ollama(imagem_base64):
    prompt1 = "Extraia todos os preços visíveis na imagem. Liste apenas os valores monetários, como R$ 9,99."
    prompt2 = (
        "Você é um assistente especializado em detectar preços em imagens. "
        "Sua tarefa é identificar e extrair todos os valores monetários visíveis na imagem fornecida, juntamente com o nome do produto, se disponível. "
        "Os valores podem estar em diferentes formatos, como R$ 9,99, 10,00, R$ 15,50, etc. "
        "Certifique-se de extrair todos os valores, mesmo que estejam em diferentes partes da imagem. "
        "Se houver mais de um valor, liste-os separadamente. "
        "Se não houver valores visíveis, responda com 'Nenhum valor encontrado'. "
        
    )

    payload = {
        "model": MODEL,
        "prompt": prompt1,
        "images": [imagem_base64]
    }

    try:
        with requests.post(OLLAMA_URL, json=payload, stream=True) as response:
            response.raise_for_status()
            resposta_final = ''.join(
                json.loads(linha.decode("utf-8")).get("response", "")
                for linha in response.iter_lines() if linha
            )
        return resposta_final.strip()

    except Exception as e:
        return f"Erro ao se comunicar com o modelo: {str(e)}"

def selecionar_imagem():
    pasta_padrao = os.path.join(os.path.dirname(__file__), "imagens")

    caminho = filedialog.askopenfilename(
        initialdir=pasta_padrao,
        filetypes=[("Imagens", "*.png;*.jpg;*.jpeg")]
    )
    if caminho:
        resultado_text.delete("1.0", tk.END)
        resultado_text.insert(tk.END, "Processando...\n")
        janela.update_idletasks()

        with open(caminho, "rb") as f:
            imagem_base64 = base64.b64encode(f.read()).decode("utf-8")
        resultado = enviar_para_ollama(imagem_base64)
        resultado_text.delete("1.0", tk.END)
        resultado_text.insert(tk.END, resultado)


janela = tk.Tk()
janela.title("Detector de Preços com Ollama + Gemma3")
janela.geometry("600x400")

frame = tk.Frame(janela)
frame.pack(pady=20)

btn_selecionar = tk.Button(frame, text="Selecionar Imagem", command=selecionar_imagem)
btn_selecionar.pack()

resultado_text = tk.Text(janela, wrap=tk.WORD, height=15, width=70)
resultado_text.pack(pady=10)

janela.mainloop()
