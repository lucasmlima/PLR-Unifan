from playwright.sync_api import sync_playwright
import dotenv
import os
from time import sleep
import json
import pandas as pd

dotenv.load_dotenv()

URL_REDDIT = os.getenv('URL')

dicionario = {
    'titulo':[],
    'quem_publicou':[],
    'texto_publicacao':[]
}

with sync_playwright() as pw:

    browser = pw.chromium.launch(headless=False, timeout= 30000)
    context = browser.new_context(storage_state='state.json')
    page = context.new_page()

    page.goto(URL_REDDIT, wait_until='domcontentloaded')

    page.locator('.input-container input').press_sequentially('tigrinho')
    page.locator('.input-container input').press('Enter')

    for i in range(30):

        page.mouse.wheel(0,15000)
        sleep(1.5)

    publicacoes = page.get_by_test_id('sdui-post-unit').all()

    for publicacao in publicacoes:

        dados_publicacao = publicacao.locator('.text-neutral-content-weak search-telemetry-tracker').get_attribute('data-faceplate-tracking-context')
        dados_json = json.loads(dados_publicacao)
        titulo = dados_json['post']['title']
        quem_publicou = dados_json['subreddit']['name']
        try:
            texto_publicacao = dados_json['search']['snippet']
        except Exception as e:
            texto_publicacao = None

        dicionario['titulo'].append(titulo)
        dicionario['quem_publicou'].append(quem_publicou)
        dicionario['texto_publicacao'].append(texto_publicacao)

    print(f'\nQuantidade de comentários: {len(publicacoes)}')

    browser.close()

df = pd.DataFrame(dicionario)

df.to_excel('publicacoes_tigrinho_reddit.xlsx',index=False)