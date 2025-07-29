import base64
import requests
import json
import os
import sys
import time

# --- Configurações da Conexão com Ollama e Modelo ---
OLLAMA_URL = "http://ollama:11434/api/generate" # Nome do serviço 'ollama' definido no docker-compose
MODEL = "gemma3:4b" # Seu modelo Gemma no Ollama

# --- Caminhos de Input/Output dentro do contêiner ---
# As imagens de entrada estarão em '/app/dataset-images/train/train' dentro do contêiner
PASTA_IMAGENS_INPUT = "/app/dataset-images"
# Os resultados da extração (resultado_train.txt) e o arquivo de progresso (progresso.txt)
# serão salvos em '/app/results' dentro do contêiner. Este diretório será mapeado para seu host.
OUTPUT_DIR = "/app/results"

# Garante que o diretório de saída exista dentro do contêiner
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Funções do seu Script Original (com pequenos ajustes de caminho) ---

def converter_imagem_para_base64(caminho):
    """Converte uma imagem de um caminho para formato base64."""
    with open(caminho, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def enviar_para_ollama(imagem_base64):
    """Envia a imagem para o modelo Gemma no Ollama e retorna a resposta."""
    # Prompt ajustado para encorajar uma saída mais consistente e fácil de parsear
    prompt_gemma ="""Extraia a produto, marca preço e unidade a partir desse cartaz de promoção da imagem.
    """

    payload = {
        "model": MODEL,
        "prompt": prompt_gemma,
        "images": [imagem_base64]
    }

    try:
        with requests.post(OLLAMA_URL, json=payload, stream=True) as response:
            response.raise_for_status() # Lança exceção para status de erro HTTP
            resposta_final = ''.join(
                json.loads(linha.decode("utf-8")).get("response", "")
                for linha in response.iter_lines() if linha # Lê linha a linha para respostas grandes
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

    # Define o caminho completo do arquivo de saída dentro do volume mapeado
    output_file_path = os.path.join(OUTPUT_DIR, "resultado_cropado.txt")
    with open(output_file_path, "a", encoding="utf-8") as f:
        f.write(f"Imagem: {os.path.basename(caminho)}\n")
        f.write(resultado_gemma + "\n")
        f.write("="*40 + "\n")

# --- Funções para Salvar/Ler Progresso (Ajustadas para o novo diretório de saída) ---

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

# --- Execução Principal do Script ---

if __name__ == "__main__":
    # Lista todos os arquivos de imagem no diretório de entrada
    # PASTA_IMAGENS_INPUT = "/app/dataset-images/train/train" (caminho dentro do contêiner)
    caminhos = [os.path.join(PASTA_IMAGENS_INPUT, f)
                for f in sorted(os.listdir(PASTA_IMAGENS_INPUT))
                if os.path.isfile(os.path.join(PASTA_IMAGENS_INPUT, f))
                and f.lower().endswith(('.png', '.jpg', '.jpeg'))] # Garante que só pegue imagens

    if not caminhos:
        print(f"Nenhuma imagem encontrada em {PASTA_IMAGENS_INPUT}. Verifique seu volume Docker.")
        sys.exit(1)

    print(f"Total de {len(caminhos)} imagens encontradas para processar.")

    # Lógica para retomar o processamento de onde parou
    print("Se quiser retomar de um ponto específico, digite o nome do arquivo (ex: 1003.jpg). Deixe em branco para começar do início.")
    inicio = input("Arquivo para começar (ou Enter): ").strip()
    pular = bool(inicio) # True se o usuário digitou algo, False se apertou Enter

    for caminho_completo_imagem in caminhos:
        nome_arquivo_imagem = os.path.basename(caminho_completo_imagem)
        if pular:
            if nome_arquivo_imagem == inicio:
                pular = False # Encontrou o arquivo de início, começa a processar a partir daqui
                print(f"Retomando o processamento a partir de: {nome_arquivo_imagem}")
            else:
                print(f"Pulando: {nome_arquivo_imagem}")
                continue # Continua pulando até encontrar o arquivo de início

        processar_imagem(caminho_completo_imagem)
        salvar_ultima_imagem_processada(nome_arquivo_imagem) # Salva o progresso
        time.sleep(2) # Pausa para não sobrecarregar o Ollama

    print("\nProcessamento de todas as imagens concluído.")