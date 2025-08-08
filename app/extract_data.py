import base64
import requests
import json
import os
import sys
import time

OLLAMA_URL = "http://ollama:11434/api/generate"
MODEL = "gemma3:4b"

PASTA_IMAGENS_INPUT = "/app/dataset-images/valid"

OUTPUT_DIR = "/app/results"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def converter_imagem_para_base64(caminho):
    """Converte uma imagem de um caminho para formato base64."""
    with open(caminho, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def enviar_para_ollama(imagem_base64):
    """Envia a imagem para o modelo Gemma no Ollama e retorna a resposta."""
    prompt_gemma ="""
    Extraia o nome do produto, marca, preço e unidade da imagem.
    """

    payload = {
        "model": MODEL,
        "prompt": prompt_gemma,
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
    except requests.exceptions.ConnectionError as e:
        return f"Erro de conexão com o Ollama. Verifique se o serviço 'ollama' está rodando e acessível em {OLLAMA_URL}: {e}"
    except Exception as e:
        return f"Erro ao se comunicar com o modelo: {str(e)}"

def processar_imagem(caminho):
    """Processa uma única imagem: converte, envia para Ollama e salva o resultado."""
    print(f"Processando: {os.path.basename(caminho)}...")
    imagem_base64 = converter_imagem_para_base64(caminho)
    resultado_gemma = enviar_para_ollama(imagem_base64)
    print("--- Resposta do Gemma ---")
    print(resultado_gemma)
    print("------------------------")

    output_file_path = os.path.join(OUTPUT_DIR, "resultado_gemma3:27b-it-qat.txt")
    with open(output_file_path, "a", encoding="utf-8") as f:
        f.write(f"Imagem: {os.path.basename(caminho)}\n")
        f.write(resultado_gemma + "\n")
        f.write("="*40 + "\n")

def ler_ultima_imagem_processada():
    """Lê o nome da última imagem processada para retomar o processamento."""
    prog_file_path = os.path.join(OUTPUT_DIR, "progresso.txt")
    if os.path.exists(prog_file_path):
        with open(prog_file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

def salvar_ultima_imagem_processada(nome):
    """Salva o nome da última imagem processada."""
    prog_file_path = os.path.join(OUTPUT_DIR, "progresso.txt")
    with open(prog_file_path, "w", encoding="utf-8") as f:
        f.write(nome)

if __name__ == "__main__":

    caminhos = [os.path.join(PASTA_IMAGENS_INPUT, f)
                for f in sorted(os.listdir(PASTA_IMAGENS_INPUT))
                if os.path.isfile(os.path.join(PASTA_IMAGENS_INPUT, f))
                and f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    if not caminhos:
        print(f"Nenhuma imagem encontrada em {PASTA_IMAGENS_INPUT}. Verifique seu volume Docker.")
        sys.exit(1)

    print(f"Total de {len(caminhos)} imagens encontradas para processar.")

    print("Se quiser retomar de um ponto específico, digite o nome do arquivo (ex: 1003.jpg). Deixe em branco para começar do início.")
    inicio = input("Arquivo para começar (ou Enter): ").strip()
    pular = bool(inicio)

    for caminho_completo_imagem in caminhos:
        nome_arquivo_imagem = os.path.basename(caminho_completo_imagem)
        if pular:
            if nome_arquivo_imagem == inicio:
                pular = False
                print(f"Retomando o processamento a partir de: {nome_arquivo_imagem}")
            else:
                print(f"Pulando: {nome_arquivo_imagem}")
                continue

        processar_imagem(caminho_completo_imagem)
        salvar_ultima_imagem_processada(nome_arquivo_imagem)
        time.sleep(2)

    print("\nProcessamento de todas as imagens concluído.")