# Consolidador de PDFs de Processos SEI

Script em Python que automatiza a consolidação de documentos de processos administrativos
do **SEI (Sistema Eletrônico de Informações)**, eliminando a etapa manual de abrir, ordenar
e mesclar dezenas de PDFs por processo.

## Problema resolvido

Em fluxos de gestão documental com grande volume de processos, cada processo gera vários
PDFs separados (notificação, memória de cálculo, notas técnicas, tabelas, formulários etc.).
Consolidar manualmente esses arquivos em um único PDF, na ordem correta, é repetitivo e
sujeito a erro humano quando feito em escala.

## O que o script faz

- Varre uma pasta raiz contendo uma subpasta por processo.
- Identifica os PDFs relevantes em cada subpasta por palavra-chave no nome do arquivo
  (ignorando acentuação e caixa).
- Ordena os documentos segundo uma sequência lógica predefinida (ex.: Notificação → Memória
  de Cálculo → Nota Técnica → Tabelas → Formulário).
- Gera um único PDF consolidado por processo, mantendo a pasta original intacta.

## Tecnologias

- Python 3.10+
- [pikepdf](https://pikepdf.readthedocs.io/) para manipulação de PDFs
- `python-dotenv` para configuração via variáveis de ambiente

## Como usar

```bash
pip install -r requirements.txt
cp .env.example .env
# edite .env e defina RAIZ_DOCUMENTOS com o caminho da pasta raiz dos processos
python consolidar_pdfs.py
```

## Estrutura esperada de pastas

```
RAIZ_DOCUMENTOS/
├── 19975.012290-2025-10/
│   ├── 01 - Notificacao.pdf
│   ├── 02 - Memoria de Calculo.pdf
│   └── ...
└── 19975.011503-2025-88/
    └── ...
```

Cada subpasta gera `NOMEDAPASTA_Consolidado.pdf` dentro dela mesma.

## Personalização

A ordem de consolidação é definida na lista `ORDEM`, no início do script — basta
editar as palavras-chave para adaptar a outro tipo de fluxo documental.

## Observação

Este projeto é uma versão sanitizada/generalizada de um script usado internamente em um
fluxo real de gestão documental; caminhos e dados específicos de processo foram removidos.
