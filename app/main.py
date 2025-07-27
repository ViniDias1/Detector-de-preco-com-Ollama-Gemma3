import base64
import requests
import json
import os
import sys
import time

OLLAMA_URL = "http://ollama:11434/api/generate"
MODEL = "gemma3:4b"


def converter_imagem_para_base64(caminho):
    with open(caminho, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def enviar_para_ollama(imagem_base64):
    prompt2 = """ "**CONTEXTO:** Você recebeu o texto bruto extraído de uma imagem de promoção de produtos de supermercado. Sua tarefa é analisar este texto para identificar informações específicas do produto e da promoção.
**TEXTO BRUTO DA IMAGEM (GERADO POR OCR):**
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
    print(f"Processando: {os.path.basename(caminho)}...")
    imagem_base64 = converter_imagem_para_base64(caminho)
    resultado = enviar_para_ollama(imagem_base64)
    print(resultado)
    # Salva o resultado em um arquivo txt
    with open("resultado_train.txt", "a", encoding="utf-8") as f:
        f.write(f"Imagem: {os.path.basename(caminho)}\n")
        f.write(resultado + "\n")
        f.write("="*40 + "\n")

def ler_ultima_imagem_processada():
    if os.path.exists("progresso.txt"):
        with open("progresso.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

def salvar_ultima_imagem_processada(nome):
    with open("progresso.txt", "w", encoding="utf-8") as f:
        f.write(nome)

if __name__ == "__main__":
    pasta_imagens = "/app/dataset-images/train/train"
    caminhos = [os.path.join(pasta_imagens, f) for f in sorted(os.listdir(pasta_imagens)) if os.path.isfile(os.path.join(pasta_imagens, f))]
    if not caminhos:
        print(f"Nenhuma imagem encontrada em {pasta_imagens}.")
        sys.exit(1)
    print("Se quiser retomar de um ponto específico, digite o nome do arquivo (ex: 1003.jpg). Deixe em branco para começar do início.")
    inicio = input("Arquivo para começar (ou Enter): ").strip()
    pular = bool(inicio)
    for caminho in caminhos:
        if pular:
            if os.path.basename(caminho) == inicio:
                pular = False
            else:
                continue
        print(f"Processando: {os.path.basename(caminho)}")
        processar_imagem(caminho)
        salvar_ultima_imagem_processada(os.path.basename(caminho))
        time.sleep(2)