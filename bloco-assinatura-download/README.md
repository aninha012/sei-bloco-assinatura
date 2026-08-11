# Download e Consolidação de Documentos de Bloco de Assinatura — SEI

Automação em Python com Selenium que percorre um intervalo de processos dentro de um
**bloco de assinatura do SEI**, baixa uma lista configurável de documentos por processo
e consolida tudo em um único PDF por processo.

## Problema resolvido

Blocos de assinatura no SEI podem reunir dezenas de processos, cada um com múltiplos
documentos que precisam ser abertos e baixados individualmente antes de análise ou
arquivamento. Esse trabalho manual e repetitivo consumia tempo considerável do fluxo de
gestão documental.

## O que o script faz

- Efetua login no SEI e navega até o bloco de assinatura configurado.
- Percorre um intervalo de processos (definido por número de início e fim).
- Para cada processo, localiza e baixa uma lista de documentos por nome (ex.: Notificação,
  Memória de Cálculo, Nota Técnica, Tabelas, Formulário de Resposta).
- Trata o caso específico do documento "Notificação", que precisa ser gerado em PDF pela
  própria interface do SEI antes do download.
- Consolida os PDFs de cada processo em um único arquivo e o copia para uma pasta de saída.

## Tecnologias

- Python 3.10+
- Selenium + Microsoft Edge WebDriver
- PyAutoGUI (interação com diálogos nativos do sistema operacional)
- pikepdf (consolidação de PDFs)
- pyperclip (colagem de caminhos com acentuação via clipboard)
- python-dotenv (configuração sem hardcode de credenciais)

## Como usar

```bash
pip install -r requirements.txt
cp .env.example .env
# preencha SEI_LOGIN, SEI_SENHA, BLOCO_ID, PROCESSO_INICIO, PROCESSO_FIM etc.
python bloco_assinatura_download.py
```

Requisitos adicionais:
- Microsoft Edge instalado, com o WebDriver correspondente configurado no `PATH`.
- Execução em máquina com interface gráfica (o script interage com diálogos nativos
  de "Salvar como" via PyAutoGUI).

## Configuração

Todos os parâmetros sensíveis ou específicos de ambiente (credenciais, número do bloco,
intervalo de processos, pastas de saída) são lidos de variáveis de ambiente — veja
`.env.example`. Nenhum dado real de processo ou credencial está no código-fonte.

## Segurança

- Credenciais nunca são hardcoded; são carregadas via `.env` (arquivo ignorado pelo Git).
- Este projeto é uma versão sanitizada de uma automação usada em um fluxo real de gestão
  documental; números de processo, bloco e caminhos originais foram substituídos por
  exemplos genéricos.

## Limitações conhecidas

- Depende de elementos de interface específicos do SEI, que podem mudar entre versões
  do sistema.
- O uso de PyAutoGUI para o diálogo "Salvar como" exige que a janela do navegador
  permaneça em foco durante a execução.
