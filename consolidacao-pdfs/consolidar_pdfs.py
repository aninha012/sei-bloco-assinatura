"""
Consolidador de PDFs de processos SEI.

Percorre uma pasta raiz contendo subpastas de processos (uma por processo),
identifica os PDFs relevantes em cada subpasta com base em palavras-chave
configuráveis (ver `ordem.txt` / lista ORDEM abaixo) e gera um único PDF
consolidado por processo, respeitando a ordem definida.

Uso:
    1. Copie `.env.example` para `.env` e ajuste RAIZ_DOCUMENTOS.
    2. pip install -r requirements.txt
    3. python consolidar_pdfs.py
"""

import os
import re
import unicodedata
from pathlib import Path

import pikepdf
from dotenv import load_dotenv

load_dotenv()

# Pasta raiz onde estão as pastas dos processos (uma subpasta por processo).
# Configurável via variável de ambiente para não expor caminhos locais no código.
RAIZ = os.getenv("RAIZ_DOCUMENTOS", str(Path.home() / "Documents" / "processos_para_consolidar"))

# Ordem desejada de consolidação, por palavra-chave normalizada (sem acento, minúscula)
# presente no nome do arquivo. Ajuste conforme o fluxo documental do seu processo.
ORDEM = [
    "notificacao",
    "memoria",
    "nota",
    "pss",
    "selic",
    "calculo",
    "zero",       # tratado como "nome de arquivo começa com 0"
    "formulario",
]


def normalizar(texto: str) -> str:
    """Remove acentos e converte para minúsculas, para comparação robusta de nomes."""
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto.lower()


def classificar_pdf(nome_arquivo: str):
    """Retorna a posição do arquivo na ordem de consolidação, ou None se não for relevante."""
    nome = normalizar(nome_arquivo)

    # Caso especial: arquivos cujo nome começa com "0" (ex.: numeração de anexos)
    if re.match(r"^0", nome):
        return ORDEM.index("zero")

    for i, chave in enumerate(ORDEM):
        if chave == "zero":
            continue
        if chave in nome:
            return i
    return None


def consolidar_pasta(pasta_processo: str) -> None:
    """Consolida todos os PDFs relevantes de uma pasta de processo em um único arquivo."""
    pdfs = []

    for arquivo in os.listdir(pasta_processo):
        if arquivo.lower().endswith(".pdf"):
            pos = classificar_pdf(arquivo)
            if pos is not None:
                pdfs.append((pos, arquivo))

    if not pdfs:
        return

    pdfs.sort(key=lambda x: x[0])

    nome_pasta = os.path.basename(pasta_processo)
    saida = os.path.join(pasta_processo, f"{nome_pasta}_Consolidado.pdf")

    pdf_saida = pikepdf.Pdf.new()

    for _, arquivo in pdfs:
        caminho_pdf = os.path.join(pasta_processo, arquivo)
        try:
            with pikepdf.open(caminho_pdf) as pdf:
                pdf_saida.pages.extend(pdf.pages)
        except Exception as e:
            print(f"Erro ao abrir {caminho_pdf}: {e}")

    pdf_saida.save(saida)
    print(f"Consolidado criado: {saida}")


def main() -> None:
    if not os.path.isdir(RAIZ):
        print(f"Pasta raiz não encontrada: {RAIZ}")
        print("Defina a variável de ambiente RAIZ_DOCUMENTOS ou crie a pasta.")
        return

    for pasta in os.listdir(RAIZ):
        caminho_pasta = os.path.join(RAIZ, pasta)
        if os.path.isdir(caminho_pasta):
            consolidar_pasta(caminho_pasta)


if __name__ == "__main__":
    main()
