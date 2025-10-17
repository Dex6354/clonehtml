# Para rodar este arquivo, salve-o como 'app_downloader.py' e execute no terminal:
# streamlit run app_downloader.py

# Certifique-se de que as bibliotecas estão instaladas:
# pip install streamlit requests beautifulsoup4

import streamlit as st
import requests
from bs4 import BeautifulSoup
import io 
from urllib.parse import urlparse # Para extrair o domínio da URL

# Importa o módulo de componentes do Streamlit
import streamlit.components.v1 as components

# Configuração da página Streamlit
st.set_page_config(
    page_title="Baixador de HTML Estático Puro",
    layout="wide"
)

def fetch_and_display_html(url_inicial):
    """
    Função para fazer a requisição HTTP, processar e exibir o HTML,
    salvando o conteúdo da URL final após todos os redirecionamentos.
    """
    # Cabeçalhos para simular um navegador 
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        # 1. Fazendo a requisição com timeout, permitindo redirecionamentos (default=True)
        st.info(f"Tentando baixar o HTML de: **{url_inicial}**")
        raw_html = ""

        with st.spinner('Aguardando resposta do servidor (máx. 15s)...'):
            response = requests.get(url_inicial, headers=headers, timeout=15, allow_redirects=True)
            response.raise_for_status() 
            raw_html = response.text 

        url_final = response.url

        # --- LÓGICA DE REDIRECIONAMENTO ---
        if response.history:
            st.warning(f"Redirecionamento detectado! A URL inicial era: `{url_inicial}`.")
            st.info(f"O conteúdo baixado é da URL final: **{url_final}** (Status: {response.status_code})")

            st.markdown("---")
            st.markdown("#### Cadeia de Redirecionamentos:")
            for resp in response.history:
                st.markdown(f"➡️ De: `{resp.url}` (Status {resp.status_code})")
            st.markdown(f"✅ Para: `{url_final}`")
            st.markdown("---")
        else:
            st.success(f"HTML da página baixado com sucesso! (Status: {response.status_code})")
        # --- FIM DA LÓGICA ---

        # 2. Processamento e formatação do HTML
        soup = BeautifulSoup(raw_html, 'html.parser')

        st.subheader("Processamento de Limpeza Profunda (Garantindo Estaticidade)")

        # --- ETAPA 1: Remover tags <script> ---
        st.error("🗑️ Removendo todas as tags `<script>` do código.")
        for script_tag in soup.find_all('script'):
            script_tag.decompose()

        # --- ETAPA 2: Remover atributos JS inline (on-...) ---
        st.error("💣 Removendo atributos JS inline ('on...', como `onload`, `onclick`) para garantir que o loop pare.")
        for tag in soup.find_all(True): # Itera sobre todas as tags
            attrs_to_remove = [attr for attr in tag.attrs if attr.startswith('on')]
            for attr in attrs_to_remove:
                del tag[attr]

        # --- ETAPA 3: REMOVER TAGS <META> DE REDIRECIONAMENTO ---
        # A remoção mais importante para loops persistentes!
        st.error("🚨 Removendo tags `<meta>` que causam **redirecionamento (refresh)** e **bloqueio (CSP)**.")
        for meta_tag in soup.find_all('meta'):
            # Verifica se o atributo http-equiv é 'refresh' ou 'content-security-policy' (CSP)
            http_equiv_value = meta_tag.get('http-equiv', '').lower()
            if http_equiv_value in ['refresh', 'content-security-policy']:
                 meta_tag.decompose()


        # --- ETAPA 4: Injetar a tag <base> ---
        # Isso diz ao navegador (ao abrir o arquivo .html localmente) para buscar
        # CSS/JS/Imagens na URL original do site.
        base_tag = soup.new_tag("base", href=url_final)

        if soup.head:
            soup.head.insert(0, base_tag)
            st.success("✅ Tag `<base>` injetada para corrigir links de CSS/Imagens ao abrir localmente.")
        else:
            st.warning("Aviso: A tag <head> não foi encontrada para injetar a tag `<base>`.")

        # O HTML modificado será usado para download e exibição
        prettified_html_final = soup.prettify()


        # 3. Botão de Download
        html_file = io.StringIO(prettified_html_final)

        # Define o nome do arquivo usando o domínio da URL FINAL
        try:
            domain = urlparse(url_final).netloc
            file_name_base = domain.replace('www.', '')
        except:
            file_name_base = "site_baixado"

        st.download_button(
            label="⬇️ Baixar o HTML Estático Puro (Layout para Cópia)",
            data=html_file.getvalue(), 
            file_name=f"html_layout_{file_name_base}_limpo.html",
            mime="text/html"
        )

        # Estilos CSS
        st.markdown(
            """
            <style>
            .stDownloadButton > button {
                background-color: #007bff;
                color: white;
                font-size: 1.1rem;
                border-radius: 8px;
                padding: 10px 20px;
                box-shadow: 3px 3px 7px rgba(0, 0, 0, 0.2);
                transition: background-color 0.3s;
            }
            .stDownloadButton > button:hover {
                 background-color: #0056b3;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # 4. Visualização Embarcada (HTML Estático Baixado)
        st.subheader("Visualização da Estrutura (Puro HTML)")
        st.info("""
        Esta é a visualização do código HTML **totalmente limpo** de redirecionamentos. Se ainda não carregar, é um bloqueio de rede ou CSS. **Use o botão de download para obter o arquivo .html e inspecioná-lo localmente.**
        """)

        # Usamos components.html para renderizar o HTML estático
        components.html(
            prettified_html_final,
            height=500, # Altura fixa para o iframe
            scrolling=True
        )

        # 5. Exibindo o HTML na tela (Código Fonte)
        st.subheader("Código HTML (Fonte Formatada)")
        st.markdown(f"**Nota:** Este é o código pronto para download, **totalmente limpo** de elementos que causavam o loop.")
        st.code(prettified_html_final, language='html')


    except requests.exceptions.MissingSchema:
        st.error("Erro: A URL fornecida está incompleta. Certifique-se de incluir o prefixo 'http://' ou 'https://'.")
    except requests.exceptions.ConnectionError:
        st.error("Erro de Conexão: O site pode estar offline, o endereço pode estar incorreto, ou a rede está inacessível.")
    except requests.exceptions.Timeout:
        st.error("Erro de Timeout: A requisição demorou muito para responder. Tente novamente.")
    except requests.exceptions.HTTPError as e:
        # Captura erros como 404, 403, 500
        st.error(f"Erro HTTP: Falha na requisição com código de status {e.response.status_code}.")
        st.warning("O site pode estar bloqueando nosso acesso (ex: 403 Forbidden).")
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado: {e}")


# --- Estrutura da Aplicação Streamlit ---

st.title("Baixador de Conteúdo HTML (Streamlit)")
st.markdown("Cole a URL do site que você deseja inspecionar. O código fará o download do **conteúdo final** após qualquer redirecionamento.")

# 1. Campo para colar a URL
url_input = st.text_input(
    label="URL do Site (ex: https://accounts.google.com/)",
    value="",
    placeholder="https://www.seudominio.com.br"
)

# 2. Botão de Ação
if st.button("Buscar e Processar HTML"):
    if url_input:
        # Chamada da função principal se a URL não estiver vazia
        fetch_and_display_html(url_input.strip())
    else:
        st.warning("Por favor, cole uma URL para começar.")

st.markdown("""
<hr style="border: 0; height: 1px; background: #333; background-image: linear-gradient(to right, #ccc, #333, #ccc);">
<div style="text-align: center; color: #555; font-size: 0.9em;">
Powered by Python, Streamlit, Requests, and BeautifulSoup.
</div>
""", unsafe_allow_html=True)
