"""
Automação de download e consolidação de documentos de um bloco de assinatura no SEI.

Para cada processo dentro de um intervalo definido em um bloco de assinatura, o script:
    1. Abre o processo em uma nova aba.
    2. Localiza e baixa uma lista configurável de documentos (por nome).
    3. Trata o caso especial de documentos "Notificação", que precisam ser gerados
       em PDF pela própria interface do SEI antes do download.
    4. Salva os PDFs organizados por processo.
    5. Consolida todos os PDFs de cada processo em um único arquivo.
    6. Copia o consolidado para uma pasta de saída final.

Motivação: eliminar a etapa manual e repetitiva de abrir, localizar e baixar
documento por documento, processo por processo, dentro de um bloco de assinatura.

Uso:
    1. Copie `.env.example` para `.env` e preencha LOGIN, SENHA e os demais parâmetros.
    2. pip install -r requirements.txt
    3. python bloco_assinatura_download.py

Requer o Microsoft Edge WebDriver instalado e compatível com a versão do navegador.
"""

import os
import shutil
import time
import traceback

import pyautogui
import pyperclip
from dotenv import load_dotenv
from pikepdf import Pdf
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

# ---------------------------------------------------------------------------
# CONFIGURAÇÃO (via variáveis de ambiente — ver .env.example)
# ---------------------------------------------------------------------------
load_dotenv()

SEI_URL = os.getenv(
    "SEI_URL",
    "https://colaboragov.sei.gov.br/sip/modulos/MF/login_especial/login_especial.php"
    "?sigla_orgao_sistema=MGI&sigla_sistema=SEI&infra_url=L3NlaS8=",
)
LOGIN = os.getenv("SEI_LOGIN")
SENHA = os.getenv("SEI_SENHA")
ORGAO_VALUE = os.getenv("SEI_ORGAO_VALUE", "7")

BLOCO_ID = os.getenv("BLOCO_ID", "0000000")
PROCESSO_INICIO = os.getenv("PROCESSO_INICIO", "00000.000000/2025-00")
PROCESSO_FIM = os.getenv("PROCESSO_FIM", "00000.000000/2025-00")

PASTA_DOWNLOADS = os.path.join(os.path.expanduser("~"), "Downloads")
PASTA_SAIDA = os.getenv("PASTA_SAIDA", os.path.join(os.path.expanduser("~"), "SEI_PDF_Bloco"))
PASTA_SAIDA_CONSOLIDADO = os.getenv(
    "PASTA_SAIDA_CONSOLIDADO", os.path.join(os.path.expanduser("~"), "SEI_PDF_Bloco_Consolidado")
)

# Lista de documentos a localizar/baixar em cada processo, na ordem desejada.
DOCUMENTOS = [
    "Notificação",
    "Memória de Cálculo",
    "Nota Técnica",
    "Tabela PSS",
    "Tabela Selic",
    "Notícia RFB",
    "Ficha - Financeira",
    "Formulário - Resposta",
]

processos_processados = set()


# ---------------------------------------------------------------------------
# FUNÇÕES AUXILIARES
# ---------------------------------------------------------------------------
def abrir_documento(driver, nome_doc):
    """Localiza e clica em um documento pelo nome, dentro dos iframes da árvore do processo."""
    try:
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            driver.switch_to.frame(iframe)
            try:
                elemento = driver.find_element(
                    By.XPATH, f"//span[contains(normalize-space(text()), '{nome_doc}')]"
                )
                link = elemento.find_element(By.XPATH, "..")
                driver.execute_script("arguments[0].scrollIntoView(true);", link)
                time.sleep(3)
                link.click()
                driver.switch_to.default_content()
                print(f"✔ Documento aberto: {nome_doc}")
                return True
            except Exception:
                driver.switch_to.default_content()
                continue
        print(f"⚠ Documento não encontrado: {nome_doc}")
        return False
    finally:
        driver.switch_to.default_content()


def salvar_pdf_com_focus(driver, caminho_completo, click_x=600, click_y=200, retries=3):
    """Aciona 'Salvar como' do visualizador de PDF nativo e cola o caminho via clipboard
    (evita problemas de digitação de caracteres acentuados pelo pyautogui)."""
    for attempt in range(1, retries + 1):
        try:
            try:
                driver.execute_script("window.focus();")
            except Exception:
                pass

            time.sleep(0.5)
            pyautogui.click(click_x, click_y)
            time.sleep(1.2)

            pyautogui.hotkey("ctrl", "s")
            time.sleep(2)

            pyperclip.copy(caminho_completo)
            time.sleep(0.6)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.6)

            pyautogui.press("enter")
            time.sleep(3)

            print(f"✔ Tentativa {attempt}: PDF salvo em: {caminho_completo}")
            return caminho_completo

        except Exception as e:
            print(f"⚠ Tentativa {attempt} falhou ao salvar PDF: {e}")
            traceback.print_exc()
            time.sleep(2)

    raise RuntimeError("Falha ao salvar PDF após múltiplas tentativas.")


def pegar_pdf_recente():
    """Retorna o PDF mais recente na pasta de downloads (usado após gerar a Notificação)."""
    arquivos = [
        os.path.join(PASTA_DOWNLOADS, f)
        for f in os.listdir(PASTA_DOWNLOADS)
        if f.lower().endswith(".pdf")
    ]
    if not arquivos:
        return None
    return max(arquivos, key=os.path.getmtime)


def gerar_pdf_notificacao(driver):
    """Aciona o fluxo específico do SEI para gerar o PDF de um documento de Notificação."""
    print("📄 Notificação encontrada — gerando PDF manualmente...")

    botao_pdf_clicado = False
    for iframe in driver.find_elements(By.TAG_NAME, "iframe"):
        driver.switch_to.frame(iframe)
        time.sleep(3)
        try:
            btn_pdf = driver.find_element(By.XPATH, "//img[contains(@src,'documento_gerar_pdf')]")
            driver.execute_script("arguments[0].scrollIntoView(true);", btn_pdf)
            time.sleep(2)
            btn_pdf.click()
            botao_pdf_clicado = True
            driver.switch_to.default_content()
            print("✔ Botão Gerar PDF clicado.")
            break
        except Exception:
            driver.switch_to.default_content()
            continue

    if not botao_pdf_clicado:
        print("❌ Botão Gerar PDF não encontrado.")
        return None

    time.sleep(10)

    botao_gerar_clicado = False
    for iframe in driver.find_elements(By.TAG_NAME, "iframe"):
        driver.switch_to.frame(iframe)
        time.sleep(2)
        try:
            botao_gerar = driver.find_element(By.NAME, "btnGerar")
            driver.execute_script("arguments[0].scrollIntoView(true);", botao_gerar)
            time.sleep(2)
            botao_gerar.click()
            botao_gerar_clicado = True
            driver.switch_to.default_content()
            print("✔ Botão GERAR clicado.")
            break
        except Exception:
            driver.switch_to.default_content()
            continue

    if not botao_gerar_clicado:
        print("❌ Botão GERAR não encontrado.")
        return None

    print("⏳ Aguardando download...")
    time.sleep(12)
    return pegar_pdf_recente()


def processar_documento_padrao(driver, nova_aba, abas_antes_processo, doc, caminho_pdf):
    """Abre o link 'aqui' do documento (visualização) e salva o PDF correspondente."""
    print(f"📄 Abrindo PDF de: {doc}")
    time.sleep(6)

    abas_antes_pdf = driver.window_handles
    link_clicado = False

    for iframe in driver.find_elements(By.TAG_NAME, "iframe"):
        driver.switch_to.frame(iframe)
        time.sleep(1)
        try:
            link_aqui = driver.find_element(
                By.XPATH,
                "//a[contains(normalize-space(text()), 'aqui') or contains(@class,'ancoraVisualizacaoArvore')]",
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", link_aqui)
            time.sleep(1)
            link_aqui.click()
            link_clicado = True
            driver.switch_to.default_content()
            print("✔ Link 'aqui' clicado.")
            break
        except Exception:
            driver.switch_to.default_content()
            continue

    if not link_clicado:
        print("⚠ Link não localizado via Selenium — usando coordenada de fallback.")
        try:
            driver.execute_script("window.focus();")
        except Exception:
            pass
        time.sleep(0.5)
        pyautogui.click(400, 273)
        time.sleep(0.5)

    time.sleep(4)

    handles = driver.window_handles
    if len(handles) > len(abas_antes_pdf):
        driver.switch_to.window(handles[-1])
        print("✔ Mudou para aba do PDF.")
    else:
        print("⚠ Salvando na aba atual.")

    time.sleep(4)
    salvar_pdf_com_focus(driver, caminho_pdf)

    if len(handles) > len(abas_antes_pdf):
        driver.close()
        time.sleep(1)
        driver.switch_to.window(nova_aba)
    else:
        try:
            driver.switch_to.window(nova_aba)
        except Exception:
            pass


def consolidar_processo(pasta_processo, texto_proc, pdfs_salvos):
    """Consolida os PDFs baixados de um processo em um único arquivo e copia para a
    pasta de saída final."""
    pdf_consolidado = os.path.join(
        pasta_processo, f"Consolidado - {texto_proc.replace('/', '-')}.pdf"
    )

    pdf_final = Pdf.new()
    for pdf in pdfs_salvos:
        try:
            with Pdf.open(pdf) as pdf_temp:
                pdf_final.pages.extend(pdf_temp.pages)
        except Exception as e:
            print(f"Erro ao consolidar {pdf}: {e}")

    pdf_final.save(pdf_consolidado)
    pdf_final.close()
    print(f"✔ Consolidado gerado: {pdf_consolidado}")

    os.makedirs(PASTA_SAIDA_CONSOLIDADO, exist_ok=True)
    destino_final = os.path.join(PASTA_SAIDA_CONSOLIDADO, os.path.basename(pdf_consolidado))
    shutil.copy(pdf_consolidado, destino_final)
    print(f"✔ Consolidado copiado para pasta final: {destino_final}")


# ---------------------------------------------------------------------------
# FLUXO PRINCIPAL
# ---------------------------------------------------------------------------
def main():
    if not LOGIN or not SENHA:
        raise SystemExit("Defina SEI_LOGIN e SEI_SENHA no arquivo .env antes de executar.")

    driver = webdriver.Edge()
    driver.get(SEI_URL)
    driver.maximize_window()
    wait = WebDriverWait(driver, 30)

    wait.until(EC.presence_of_element_located((By.ID, "txtUsuario"))).send_keys(LOGIN)
    driver.find_element(By.ID, "pwdSenha").send_keys(SENHA)
    Select(driver.find_element(By.ID, "selOrgao")).select_by_value(ORGAO_VALUE)
    driver.find_element(By.ID, "Acessar").click()

    wait.until(EC.presence_of_element_located((By.ID, "txtPesquisaRapida")))
    print("Login realizado com sucesso.")

    wait = WebDriverWait(driver, 25)

    driver.find_element(By.XPATH, "//span[text()='Blocos']").click()
    time.sleep(4)
    driver.find_element(By.XPATH, "//span[text()='Assinatura']").click()
    time.sleep(5)

    driver.find_element(By.LINK_TEXT, BLOCO_ID).click()
    time.sleep(8)

    pyautogui.click(968, 404)  # aba "Processos do bloco"
    time.sleep(8)

    wait = WebDriverWait(driver, 30)

    while True:
        try:
            processos = wait.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//a[contains(@class,'protocoloAberto') and contains(@class,'aIdProcedimento')]")
                )
            )
            lista_textos = [p.text.strip() for p in processos]

            if PROCESSO_INICIO not in lista_textos:
                print(f"❌ Processo inicial '{PROCESSO_INICIO}' não encontrado.")
                break
            if PROCESSO_FIM not in lista_textos:
                print(f"❌ Processo final '{PROCESSO_FIM}' não encontrado.")
                break

            idx_inicio = lista_textos.index(PROCESSO_INICIO)
            idx_fim = lista_textos.index(PROCESSO_FIM)

            intervalo = (
                processos[idx_fim : idx_inicio + 1]
                if idx_inicio > idx_fim
                else processos[idx_inicio : idx_fim + 1]
            )
            intervalo = [p for p in intervalo if p.text not in processos_processados]

            if not intervalo:
                print("✔ Todos os processos no intervalo foram processados.")
                break

            processo_link = intervalo[0]
            texto_proc = processo_link.text.strip()
            processos_processados.add(texto_proc)

            abas_antes = driver.window_handles
            processo_link.click()
            print(f"➡ Abrindo processo: {texto_proc}")

            wait.until(lambda d: len(d.window_handles) > len(abas_antes))
            nova_aba = [a for a in driver.window_handles if a not in abas_antes][0]
            driver.switch_to.window(nova_aba)
            time.sleep(7)

            pasta_processo = os.path.join(PASTA_SAIDA, texto_proc.replace("/", "-"))
            os.makedirs(pasta_processo, exist_ok=True)

            pdfs_salvos = []

            for index, doc in enumerate(DOCUMENTOS, start=1):
                if not abrir_documento(driver, doc):
                    time.sleep(5)
                    continue

                if doc == "Notificação":
                    pdf_recente = gerar_pdf_notificacao(driver)
                    if pdf_recente:
                        novo_nome = os.path.join(pasta_processo, f"{index:02d} - {doc}.pdf")
                        shutil.move(pdf_recente, novo_nome)
                        pdfs_salvos.append(novo_nome)
                        print(f"✔ PDF movido: {novo_nome}")
                    else:
                        print("❌ Nenhum PDF baixado para Notificação.")
                    continue

                try:
                    caminho_pdf = os.path.join(pasta_processo, f"{index:02d} - {doc}.pdf")
                    processar_documento_padrao(driver, nova_aba, abas_antes, doc, caminho_pdf)
                    pdfs_salvos.append(caminho_pdf)
                    print(f"✔ Documento salvo: {caminho_pdf}")
                except Exception as ex_doc:
                    print("⚠ Erro ao processar documento:", ex_doc)
                    traceback.print_exc()
                    try:
                        for h in driver.window_handles:
                            if h != nova_aba and h not in abas_antes:
                                driver.switch_to.window(h)
                                driver.close()
                        driver.switch_to.window(nova_aba)
                    except Exception:
                        pass
                    continue

            consolidar_processo(pasta_processo, texto_proc, pdfs_salvos)

            driver.close()
            driver.switch_to.window(abas_antes[0])
            time.sleep(2)

        except Exception as erro_final:
            print("Erro no loop principal:", erro_final)
            traceback.print_exc()
            break

    print("✔ Rotina finalizada.")
    driver.quit()


if __name__ == "__main__":
    main()
