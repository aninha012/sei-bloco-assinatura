# SEI Workflow Automation

Conjunto de scripts em Python que automatizam etapas manuais e repetitivas de um fluxo de
**gestão documental no SEI (Sistema Eletrônico de Informações)**, usado por diversos órgãos
da administração pública brasileira.

Cada automação resolve um gargalo específico do processo de análise e tramitação de
processos administrativos em lote.

## Projetos

| Projeto | Descrição | Tecnologias |
|---|---|---|
| [`consolidacao-pdfs/`](./consolidacao-pdfs) | Consolida os PDFs de cada processo em um único arquivo, na ordem documental correta. | pikepdf |
| [`bloco-assinatura-download/`](./bloco-assinatura-download) | Baixa automaticamente os documentos de todos os processos de um bloco de assinatura e consolida cada processo. | Selenium, PyAutoGUI, pikepdf |
| [`bloco-assinatura-insercao/`](./bloco-assinatura-insercao) | Insere automaticamente listas de processos específicos em blocos de assinatura no SEI, eliminando a etapa manual de inclusão processo a processo. | Selenium |

## Contexto

Em fluxos de trabalho com alto volume de processos (ex.: análise fiscal, notificações,
cobrança administrativa), etapas como localizar documentos, baixá-los na ordem certa,
consolidá-los e organizar processos em blocos de assinatura consomem tempo desproporcional
ao valor analítico do trabalho. Essas automações eliminam essas etapas mecânicas,
permitindo que a equipe foque na análise do conteúdo dos processos.

## Como este repositório está organizado

Cada pasta é um projeto independente, com seu próprio `README.md`, `requirements.txt` e
`.env.example`. Nenhum dado real (credenciais, números de processo, caminhos locais) está
versionado — todos os scripts foram sanitizados para uso público e leem configuração via
variáveis de ambiente.

## Aviso

Estes scripts dependem da estrutura de interface do SEI vigente no momento em que foram
desenvolvidos e podem exigir ajustes em caso de atualização do sistema. São publicados como
demonstração de solução de automação, não como pacote pronto para uso em produção sem
adaptação ao ambiente do usuário.
