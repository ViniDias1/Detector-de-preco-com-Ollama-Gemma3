import base64
import requests
import json
import os
import sys

OLLAMA_URL = "http://ollama:11434/api/generate"
MODEL = "gemma3:4b"


def converter_imagem_para_base64(caminho):
    with open(caminho, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def enviar_para_ollama(imagem_base64):
    prompt2 = """ Your task is to work and the job of an professional OCR tool, analyzing an image containing
        a price tag and one or more products. You should extract
        the product’s NAME and BRAND, NORMAL PRICE, DISCOUNTED PRICE, UNIT,
        (in PT-BR). You must extract all the text from the. Remind yourself that ALL the text are in Portuguese (Brasilian Portuguese).
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
    with open("resultados.txt", "a", encoding="utf-8") as f:
        f.write(f"Imagem: {os.path.basename(caminho)}\n")
        f.write(resultado + "\n")
        f.write("="*40 + "\n")

if __name__ == "__main__":
    pasta_imagens = "/app/dataset-images/test"
    caminhos = [os.path.join(pasta_imagens, f) for f in sorted(os.listdir(pasta_imagens)) if os.path.isfile(os.path.join(pasta_imagens, f))]
    if not caminhos:
        print(f"Nenhuma imagem encontrada em {pasta_imagens}.")
        sys.exit(1)
    for caminho in caminhos:
        print(f"Pronto para analisar: {os.path.basename(caminho)}")
        comando = input("Digite 'y' para analisar esta imagem, 'sair' para encerrar, ou qualquer outra tecla para pular: ").strip().lower()
        if comando == "sair":
            print("Encerrando.")
            break
        elif comando == "y":
            processar_imagem(caminho)
        else:
            print("Comando não reconhecido. Pulando esta imagem.")