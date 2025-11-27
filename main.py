from playwright.sync_api import sync_playwright
import dotenv
import os
from time import sleep
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO INICIAL ---
dotenv.load_dotenv()
URL_REDDIT = os.getenv('URL')
# O dicionário será preenchido com dados de todos os assuntos
dicionario = {'comentario':[]} 
assuntos = ['casas de apostas', 'jogo de azar', 'cassino online', 'apostas esportivas', 'bônus de apostas']
TAMANHO_DO_LOTE = 2 # Define o número de abas simultâneas

print(f"Início do scraping em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

for assunto in assuntos:
    print(f"\n========================================================")
    print(f"Iniciando coleta para o assunto: '{assunto}'")
    print(f"========================================================")

    with sync_playwright() as pw:
        # Aumentei o timeout do launch para acomodar a navegação e o contexto
        browser = pw.chromium.launch(headless=False, timeout= 60000) 
        context = browser.new_context(storage_state='state.json')
        page = context.new_page()

        # 1. Pesquisa inicial
        page.goto(URL_REDDIT, wait_until='domcontentloaded')
        page.locator('.input-container input').press_sequentially(assunto)
        page.locator('.input-container input').press('Enter')
        
        # Opcional: Adicionar um pequeno sleep para garantir que a página de resultados carregou
        sleep(2) 

        # 2. Rolagem e coleta de publicações
        print("Rolando a página para carregar mais publicações...")
        for _ in range(5):
            page.mouse.wheel(0,15000)
            sleep(1)

        # Coletar os elementos (Localizadores) das publicações
        publicacoes_elements = page.get_by_test_id('sdui-post-unit').all()
        # Mapear para uma lista de links
        links = [
            URL_REDDIT + p.get_by_test_id('post-title-text').get_attribute('href')
            for p in publicacoes_elements if p.get_by_test_id('post-title-text').get_attribute('href')
        ]
        
        print(f"Total de links encontrados para '{assunto}': {len(links)}")
        
        # 3. Processamento em Lote (Batch)
        for i in range(0, len(links), TAMANHO_DO_LOTE):
            lote_links = links[i:i + TAMANHO_DO_LOTE]
            abas_do_lote = []
            
            print(f"\nLote {i // TAMANHO_DO_LOTE + 1}/{len(links) // TAMANHO_DO_LOTE + 1}: Abrindo {len(lote_links)} abas...")

            # A. Abrir todas as abas no lote
            for link in lote_links:
                page_post = context.new_page()
                try:
                    page_post.goto(link, wait_until='domcontentloaded', timeout=20000)
                    abas_do_lote.append(page_post)
                except Exception as e:
                    print(f"ERRO: Falha ao navegar para o link {link}: {e}")
                    page_post.close()
            
            # B. Processar o conteúdo de cada aba no lote
            for page_post in abas_do_lote:
                print(f"   -> Processando: {page_post.url}")
                
                try:
                    # Rola a página para carregar mais conteúdo e comentários
                    page_post.mouse.wheel(0, 15000)
                    # Usando wait_for_selector em vez de sleep para maior robustez
                    page_post.wait_for_selector(
                        '.md.text-14-scalable.rounded-2.pb-2xs.overflow-hidden', 
                        state='visible', 
                        timeout=10000
                    )
                    
                    comentarios = page_post.locator('.md.text-14-scalable.rounded-2.pb-2xs.overflow-hidden').all()
                    
                    for comentario in comentarios:
                        # Extrai o texto completo do comentário
                        texto_completo = comentario.inner_text().strip()
                        if texto_completo: # Só adiciona se o texto não for vazio
                            dicionario['comentario'].append(texto_completo)

                except Exception as e:
                    print(f"   -> ERRO: Falha ao extrair comentários de {page_post.url}. {e}")
            
            # C. Fechar todas as abas do lote
            for page_post in abas_do_lote:
                page_post.close()
                
        # 4. Finalização do Navegador
        page.close()
        browser.close()

    # **********************************************
    # ADICIONANDO A PAUSA DE 360 SEGUNDOS (6 minutos)
    # **********************************************
    if assunto != assuntos[-1]: # Verifica se não é o último assunto
        print(f"\n--- PAUSA ATIVA: Aguardando 360 segundos (6 minutos) antes de começar o próximo assunto. ---")
        sleep(360)
    else:
        print("\nTodos os assuntos foram processados.")
        
# 5. Criação e Exportação Final do DataFrame (DEVE SER FORA DO LOOP)
df = pd.DataFrame(dicionario)
nome_arquivo = 'publicacoes_comentarios_totais.xlsx'
df.to_excel(nome_arquivo, index=False)
print(f"\nScraping Concluído. Total de {len(df)} comentários salvos em '{nome_arquivo}'.")