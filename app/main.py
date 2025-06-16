import tkinter as tk
from tkinter import filedialog
import base64
import requests
import json
import os
from PIL import Image, ImageTk

OLLAMA_URL = "http://ollama:11434/api/generate"
MODEL = "gemma3:4b"
referencias_imagens = []

def converter_imagem_para_base64(caminho):
    with open(caminho, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def enviar_para_ollama(imagem_base64):
    prompt1 = "Extraia todos os preços visíveis na imagem. Liste apenas os valores monetários, como R$ 9,99."

    prompt2 = """ Your task is to work and the job of an professional OCR tool, analyzing an image containing
a price tag and one or more products. You should extract
the product’s NAME, NORMAL PRICE, DISCOUNTED PRICE, UNIT, BARCODE NUMBERS and DESCRIPTION
(in PT-BR).
"""    

    payload = {
        "model": MODEL,
        "prompt": prompt2,
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

def processar_imagem(caminho):
    resultado_text.delete("1.0", tk.END)
    resultado_text.insert(tk.END, f"Processando: {os.path.basename(caminho)}...\n")
    janela.update_idletasks()

    imagem_base64 = converter_imagem_para_base64(caminho)
    resultado = enviar_para_ollama(imagem_base64)
    resultado_text.delete("1.0", tk.END)
    resultado_text.insert(tk.END, resultado)

def selecionar_imagens():
    caminhos = filedialog.askopenfilenames(title="Selecione as imagens", filetypes=[
        ("Imagens", "*.jpg *.jpeg *.png")
    ])
    if not caminhos:
        return

    for widget in galeria_interna.winfo_children():
        widget.destroy()
    referencias_imagens.clear()

    for i, caminho in enumerate(caminhos):
        try:
            imagem = Image.open(caminho)
            imagem.thumbnail((100, 100))
            img_tk = ImageTk.PhotoImage(imagem)

            btn = tk.Button(galeria_interna, image=img_tk, command=lambda c=caminho: processar_imagem(c))
            btn.grid(row=0, column=i, padx=4, pady=4)
            referencias_imagens.append(img_tk)
        except Exception as e:
            print(f"Erro ao carregar imagem {caminho}: {e}")

# Interface
janela = tk.Tk()
janela.title("Detector de Preços com Ollama + Gemma3")
janela.geometry("1000x600")

btn_selecionar = tk.Button(janela, text="Selecionar Imagens", font=("Arial", 12), command=selecionar_imagens)
btn_selecionar.pack(pady=10)

galeria_canvas = tk.Canvas(janela, height=120)
scroll_x = tk.Scrollbar(janela, orient="horizontal", command=galeria_canvas.xview)
galeria_canvas.configure(xscrollcommand=scroll_x.set)

scroll_x.pack(fill="x")
galeria_canvas.pack(fill="x")

galeria_interna = tk.Frame(galeria_canvas)
galeria_canvas.create_window((0, 0), window=galeria_interna, anchor="nw")

def atualizar_scroll(event):
    galeria_canvas.configure(scrollregion=galeria_canvas.bbox("all"))

galeria_interna.bind("<Configure>", atualizar_scroll)

resultado_text = tk.Text(janela, wrap=tk.WORD, height=20, width=100)
resultado_text.pack(pady=10)

janela.mainloop()
