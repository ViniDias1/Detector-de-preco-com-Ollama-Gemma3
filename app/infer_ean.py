# app/infer_ean.py

import pandas as pd
import os
import re
from fuzzywuzzy import process
# import csv # No longer need csv module directly for this approach

# --- Funções Auxiliares (mantidas as mesmas, exceto carregar_base_dados_produtos) ---

def parse_gemma_output(gemma_output_text):
    data = {}
    gemma_output_text = gemma_output_text.replace('\xa0', ' ')
    matches = re.findall(
        r"^\*\s*\*\*\s*([\w\s\/]+?)\s*:\s*\s*\*?\*?\s*(.*?)(?=\n\*\s*\*\*|$|\Z)",
        gemma_output_text,
        re.MULTILINE | re.DOTALL
    )
    for key, value in matches:
        key_cleaned = key.strip().replace(" ", "_").lower()
        data[key_cleaned] = value.strip()
    return data

def carregar_base_dados_produtos(csv_database_path):
    """
    Carrega o CSV da base de dados de produtos, assumindo um formato CSV padrão
    com vírgulas como delimitador e aspas duplas como caractere de citação.
    """
    try:
        print("DEBUG CSV: Tentando carregar CSV com delimitador ',', quotechar '\"', engine 'python'...")
        df = pd.read_csv(
            csv_database_path,
            sep=',',            # Explicitamente a vírgula como delimitador
            quotechar='"',      # Os campos são citados por aspas duplas
            doublequote=True,   # Aspas duplas dentro de um campo citado são escapadas com outra aspa dupla
            engine='python',    # Use o motor Python para parsear (mais robusto para casos complexos)
            encoding='utf-8',   # A codificação parece ser UTF-8
            # Adiciona skipinitialspace para lidar com espaços após o delimitador
            skipinitialspace=True 
        )
        print("DEBUG CSV: CSV lido com sucesso usando os parâmetros especificados.")

        # --- Verificação CRÍTICA após o carregamento ---
        if 'brand' not in df.columns or 'name' not in df.columns:
            print("ERRO CRÍTICO: As colunas 'brand' e/ou 'name' NÃO FORAM ENCONTRADAS no CSV após a leitura.")
            print(f"Colunas disponíveis: {df.columns.tolist()}")
            # Imprime as primeiras linhas para depuração
            print("\nDEBUG CSV: Primeiras 5 linhas do DataFrame (para inspeção de colunas):")
            print(df.head().to_string())
            return None # Retorna None para abortar o processo se colunas essenciais não forem encontradas
        
        print(f"\nDEBUG CSV: Conteúdo original das colunas 'brand' e 'name' (primeiras 5 linhas):")
        print(df[['brand', 'name']].head().to_string())
        print(f"DEBUG CSV: Tipos de dados de 'brand' e 'name': {df['brand'].dtype}, {df['name'].dtype}")
        print(f"DEBUG CSV: Contagem de valores nulos em 'brand': {df['brand'].isnull().sum()}")
        print(f"DEBUG CSV: Contagem de valores nulos em 'name': {df['name'].isnull().sum()}")

        # Preenche valores NaN nas colunas 'brand' e 'name' com strings vazias para evitar erros
        df['brand'] = df['brand'].fillna('') 
        df['name'] = df['name'].fillna('')   

        # Garante que a coluna 'ean' seja tratada como string e limpa espaços
        df['ean'] = df['ean'].astype(str).str.strip()
        
        # Cria a coluna comparable_text_db combinando marca e nome
        df['comparable_text_db'] = (df['brand'] + ' ' + df['name']).str.lower().str.strip()
        df['comparable_text_db'] = df['comparable_text_db'].apply(lambda x: ' '.join(x.split()))

        print(f"\nBase de dados de produtos carregada com sucesso. {len(df)} registros.")
        
        empty_comparable_count = df['comparable_text_db'].apply(len).eq(0).sum()
        if empty_comparable_count > 0:
            print(f"AVISO: {empty_comparable_count} registros em 'comparable_text_db' estão vazios após o processamento.")
            print("Isso pode indicar que as colunas 'brand' e 'name' no seu CSV original estavam vazias ou não continham dados relevantes.")
        print(f"DEBUG: Primeiros 5 valores de 'comparable_text_db' após processamento: {df['comparable_text_db'].head().tolist()}")
        print(f"DEBUG: Últimos 5 valores de 'comparable_text_db' após processamento: {df['comparable_text_db'].tail().tolist()}")
        
        return df
    except FileNotFoundError:
        print(f"ERRO: Arquivo da base de dados '{csv_database_path}' não encontrado. Verifique o caminho e o volume do Docker.")
        return None
    except Exception as e:
        print(f"ERRO fatal ao carregar ou processar a base de dados CSV: {e}")
        import traceback
        traceback.print_exc()
        return None

def inferir_ean(dados_extraidos, df_produtos, threshold_fuzzy):
    # --- Essa função permanece a mesma ---
    marca_extraida = dados_extraidos.get('marca', '').strip()
    produto_extraido = dados_extraidos.get('produto', '').strip()

    print(f"\n--- Tentando inferir EAN para: '{produto_extraido}' (Marca: '{marca_extraida}') ---")

    ean_do_gemma = dados_extraidos.get('códigos_de_barras', '').strip()
    if ean_do_gemma and ean_do_gemma.isdigit() and len(ean_do_gemma) >= 8: 
        match_ean_df = df_produtos[df_produtos['ean'] == ean_do_gemma]
        if not match_ean_df.empty:
            infered_ean = match_ean_df.iloc[0]['ean']
            print(f"✅ EAN inferido por código de barras direto: {infered_ean}")
            return infered_ean, "Correspondência Direta por EAN"
        else:
            print(f"🔍 Código de barras '{ean_do_gemma}' não encontrado na base de dados. Tentando fuzzy match...")

    texto_busca_extraido = ""
    if marca_extraida and produto_extraido:
        texto_busca_extraido = (marca_extraida + ' ' + produto_extraido).lower().strip()
    elif produto_extraido:
        texto_busca_extraido = produto_extraido.lower().strip()
    elif marca_extraida:
        texto_busca_extraido = marca_extraida.lower().strip()
    
    texto_busca_extraido = ' '.join(texto_busca_extraido.split())

    if not texto_busca_extraido:
        print("❌ Não foi possível inferir EAN: Nome do produto e/ou marca não extraídos ou vazios para fuzzy match.")
        return None, "Dados insuficientes do Gemma para Fuzzy Match"

    choices_to_search = df_produtos['comparable_text_db'].tolist()
    
    choices_to_search = [choice for choice in choices_to_search if choice.strip()] 
    
    if not choices_to_search:
        print("❌ Nenhuma opção de busca VÁLIDA disponível na base de dados para fuzzy match (todos os valores são vazios ou irrelevantes).")
        return None, "Base de Dados Inválida para Fuzzy Match"
    
    print(f"DEBUG: Texto de busca para fuzzy match: '{texto_busca_extraido}'")
    print(f"DEBUG: Total de escolhas válidas na base de dados para fuzzy match: {len(choices_to_search)}")
    if len(choices_to_search) > 0:
        print(f"DEBUG: Primeiras 5 escolhas válidas na base de dados: {choices_to_search[:min(5, len(choices_to_search))]}")

    best_match_info = process.extractOne(texto_busca_extraido, choices_to_search)

    if best_match_info:
        if len(best_match_info) == 3:
            matched_text_db, score, index_in_list = best_match_info
        elif len(best_match_info) == 2:
            matched_text_db, score = best_match_info
            index_in_list = None 
            print(f"AVISO: process.extractOne retornou apenas 2 valores. Prosseguindo sem o índice direto.")
        else:
            print(f"ERRO CRÍTICO: process.extractOne retornou um número inesperado de valores: {best_match_info}")
            return None, "Erro Interno: Retorno inesperado de fuzzywuzzy"

        if score >= threshold_fuzzy:
            original_row = df_produtos.loc[df_produtos['comparable_text_db'] == matched_text_db]
            
            if not original_row.empty:
                best_match_ean = original_row.iloc[0]['ean']
                print(f"✅ EAN inferido por fuzzy match: {best_match_ean} (Score: {score})")
                return best_match_ean, f"Fuzzy Match (Score: {score})"
            else:
                print(f"❌ Erro interno: Correspondência fuzzy encontrada ('{matched_text_db}'), mas não foi possível localizá-la na base de dados original.")
                return None, "Erro Interno de Correspondência DB"
        else:
            print(f"❌ Não foi possível inferir EAN com alta confiança. Melhor score: {score} < {threshold_fuzzy}.")
            print(f"   Melhor correspondência DB: '{matched_text_db}'")
            return None, f"Baixa Confiança (Score: {score})"
    else:
        print("❌ Nenhuma correspondência fuzzy relevante encontrada na base de dados para o produto.")
        return None, "Nenhuma Correspondência Fuzzy Encontrada"

def processar_resultados_e_inferir_eans(
    results_file_path,
    csv_database_path,
    inference_output_file,
    fuzzy_threshold
):
    # --- Essa função permanece a mesma ---
    df_produtos = carregar_base_dados_produtos(csv_database_path)
    if df_produtos is None:
        print("Não foi possível carregar a base de dados de produtos. Abortando inferência.")
        return

    inferences = []

    current_image_name = None
    current_gemma_output_lines = []
    is_reading_gemma_output = False 

    try:
        with open(results_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()

                if line.startswith("Imagem: "):
                    if current_image_name and current_gemma_output_lines and is_reading_gemma_output:
                        gemma_full_output = "\n".join(current_gemma_output_lines).strip()
                        dados_extraidos = parse_gemma_output(gemma_full_output)
                        
                        print(f"DEBUG: Dados extraídos para imagem '{current_image_name}': {dados_extraidos}")
                        
                        ean, status = inferir_ean(dados_extraidos, df_produtos, fuzzy_threshold)
                        inferences.append({
                            'Imagem': current_image_name,
                            'Produto Extraído': dados_extraidos.get('produto', 'N/A'),
                            'Marca Extraída': dados_extraidos.get('marca', 'N/A'),
                            'EAN Inferido': ean if ean else 'NÃO ENCONTRADO',
                            'Status Inferência': status
                        })

                    current_image_name = line.replace("Imagem: ", "")
                    current_gemma_output_lines = []
                    is_reading_gemma_output = True 
                
                elif line.startswith("========================================"):
                    if current_image_name and current_gemma_output_lines and is_reading_gemma_output:
                        gemma_full_output = "\n".join(current_gemma_output_lines).strip()
                        dados_extraidos = parse_gemma_output(gemma_full_output)
                        
                        print(f"DEBUG: Dados extraídos para imagem '{current_image_name}': {dados_extraidos}")
                        
                        ean, status = inferir_ean(dados_extraidos, df_produtos, fuzzy_threshold)
                        inferences.append({
                            'Imagem': current_image_name,
                            'Produto Extraído': dados_extraidos.get('produto', 'N/A'),
                            'Marca Extraída': dados_extraidos.get('marca', 'N/A'),
                            'EAN Inferido': ean if ean else 'NÃO ENCONTRADO',
                            'Status Inferência': status
                        })
                    current_image_name = None
                    current_gemma_output_lines = []
                    is_reading_gemma_output = False
                
                elif is_reading_gemma_output and line and not line.startswith("Aqui estão as informações"):
                    current_gemma_output_lines.append(line)
        
        if current_image_name and current_gemma_output_lines and is_reading_gemma_output:
            gemma_full_output = "\n".join(current_gemma_output_lines).strip()
            dados_extraidos = parse_gemma_output(gemma_full_output)
            
            print(f"DEBUG: Dados extraídos para imagem '{current_image_name}' (último bloco): {dados_extraidos}")
            
            ean, status = inferir_ean(dados_extraidos, df_produtos, fuzzy_threshold)
            inferences.append({
                'Imagem': current_image_name,
                'Produto Extraído': dados_extraidos.get('produto', 'N/A'),
                'Marca Extraída': dados_extraidos.get('marca', 'N/A'),
                'EAN Inferido': ean if ean else 'NÃO ENCONTRADO',
                'Status Inferência': status
            })

    except FileNotFoundError:
        print(f"ERRO: Arquivo de resultados do Gemma '{results_file_path}' não encontrado. Verifique o caminho e o volume do Docker.")
        return
    except Exception as e:
        print(f"ERRO durante a leitura ou processamento do arquivo de resultados: {e}")
        import traceback
        traceback.print_exc()
        return
    
    if inferences:
        df_inferences = pd.DataFrame(inferences)
        output_dir_inferences = os.path.dirname(inference_output_file)
        os.makedirs(output_dir_inferences, exist_ok=True)
        df_inferences.to_csv(inference_output_file, index=False, encoding='utf-8')
        print(f"\nResultados da inferência salvos em '{inference_output_file}'")
    else:
        print("\nNenhuma inferência foi realizada ou resultados válidos foram encontrados.")

# --- Execução Principal do Script ---
if __name__ == "__main__":
    RESULTS_FILE = os.getenv("RESULTS_FILE", "/app/results/resultado_test.txt")
    CSV_DATABASE_FILE = os.getenv("CSV_DATABASE_FILE", "/app/data/ludiiprice_db_17012025.csv")
    INFERENCE_OUTPUT_FILE = os.getenv("INFERENCE_OUTPUT_FILE", "/app/inferences/ean_inferences.csv")
    FUZZY_THRESHOLD = int(os.getenv("FUZZY_THRESHOLD", 75))

    print("Iniciando script de inferência de EAN...")
    processar_resultados_e_inferir_eans(
        RESULTS_FILE,
        CSV_DATABASE_FILE,
        INFERENCE_OUTPUT_FILE,
        FUZZY_THRESHOLD
    )