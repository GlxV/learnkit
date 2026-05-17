# LearnKit

LearnKit é um aplicativo desktop local, gratuito e open source para transformar materiais como PDF, PPTX, DOCX, TXT, Markdown e arquivos de texto/código em pacotes de estudo.

Ele não usa cloud obrigatória, não tem paywall e não depende de API paga de IA. O fluxo com IA é manual: o app extrai o conteúdo, gera um prompt, você cola em uma IA externa gratuita, como Gemini, e depois importa a resposta de volta no LearnKit.

## Organização

```text
Matéria
  -> Módulo
      -> Bloco de Estudo
          -> Resumo em texto
          -> Resumo visual
          -> Flashcards
          -> Perguntas
          -> Progresso
          -> Arquivo de origem
```

Novos blocos não sobrescrevem blocos antigos. Se um nome já existir, o storage cria slugs únicos automaticamente, como `funcoes_do_1_grau_2`.

## Banco de dados

O LearnKit usa SQLite para persistência local em `data/learnkit.db`.

SQLite foi escolhido porque:

- é local e não exige servidor;
- funciona bem para um app desktop;
- é fácil de demonstrar em sala;
- permite persistir progresso real sem depender de JSON espalhado;
- continua simples o suficiente para um MVP.

Tabelas principais:

- `subjects`: matérias;
- `modules`: módulos de uma matéria;
- `study_blocks`: blocos, resumo em texto, resumo visual e modo preferido;
- `flashcards`: cards e status de revisão;
- `questions`: perguntas, resposta escolhida e acerto/erro;
- `study_progress`: progresso agregado por bloco.

O storage JSON anterior continua como base de migração/compatibilidade, mas a UI principal abre usando SQLite.

## Progresso

O progresso é persistido no banco. O app salva:

- flashcards revisados;
- status do card: `again`, `hard`, `good`, `easy`;
- agendamento do card: facilidade, intervalo, próxima revisão e quantidade de revisões;
- perguntas respondidas;
- alternativa escolhida;
- se a resposta estava correta;
- histórico de tentativas das perguntas;
- último acesso;
- porcentagem agregada por bloco, módulo, matéria e global.

Ao fechar e abrir o app, os dados continuam salvos.

Os flashcards usam um agendamento simples inspirado no Anki, sem limite diário:

- `Repetir`: volta como vencido rapidamente;
- `Difícil`: mantém intervalo curto;
- `Bom`: aumenta o intervalo de revisão;
- `Dominei`: aumenta mais o intervalo e a facilidade.

A fila mostra cards vencidos primeiro, cards novos depois e cards futuros por último.

Nas perguntas, o LearnKit mantém a resposta mais recente para calcular progresso, mas também guarda o histórico de tentativas. A aba `Perguntas` permite filtrar por:

- todas;
- não respondidas;
- erradas;
- corretas.

Isso permite revisar erros sem apagar o histórico anterior.

A tela `Progresso` usa esses dados para mostrar:

- flashcards vencidos;
- flashcards novos;
- perguntas erradas;
- perguntas não respondidas;
- blocos com maior prioridade de revisão;
- atividade recente baseada em respostas e revisões reais.

A Home também usa esse dashboard: o card `Continuar estudando` prioriza blocos com pendências reais, e o painel `Revisar agora` aponta direto para flashcards ou perguntas conforme a necessidade.

## Resumo Texto e Visual

Cada bloco pode ter dois modos:

- `Texto`: Markdown comum, compatível com IAs gratuitas mais simples.
- `Visual`: JSON estruturado renderizado por componentes próprios do LearnKit.

O modo visual aceita blocos como:

- `hero`;
- `section`;
- `cards`;
- `callout`;
- `table`;
- `steps`;
- `timeline`;
- `comparison`;
- `key_points`;
- `formula`;
- `quote`;
- `checklist`;
- `tags`;
- `warning`;
- `example`.

O app não executa HTML bruto vindo da IA. Se o JSON visual estiver inválido, o modo texto continua funcionando.

Dentro do resumo visual existe o botão `Modo apresentação`, que abre o conteúdo em uma tela maior e permite navegar por seções como slides usando os botões ou setas do teclado.

O diálogo de resumo também permite editar e salvar o Markdown do modo Texto e o JSON do modo Visual. O LearnKit valida o JSON visual antes de salvar para evitar quebrar a apresentação.

## Instalar

Requisitos:

- Python 3.11+
- PySide6
- PyMuPDF
- python-pptx
- Pillow
- pytest para desenvolvimento

### Instalação automática no Windows

Para preparar uma máquina Windows do zero, use o instalador:

```powershell
.\install_learnkit_windows.bat
```

Ele faz, em sequência:

- verifica ou instala Python 3.11+ via `winget`;
- cria o ambiente virtual local `.venv`;
- instala as dependências do `requirements.txt`;
- tenta configurar os idiomas de OCR local do Windows (`pt-BR` e `en-US`) quando executado como administrador;
- instala o Tesseract OCR como fallback quando `winget` está disponível;
- baixa o idioma português do Tesseract quando necessário;
- testa se as dependências principais e algum backend OCR ficaram disponíveis.

Se a instalação dos idiomas OCR do Windows exigir permissão, execute o `.bat` como administrador. Mesmo sem administrador, o app continua funcionando e tenta usar o Tesseract como OCR local.

Depois da instalação, abra o app com:

```powershell
.\abrir_learnkit.bat
```

O atalho usa automaticamente `.venv\Scripts\python.exe` quando o ambiente virtual existir.

### Instalação manual

```powershell
python -m pip install -r requirements.txt
```

## Rodar

```powershell
python -m app.main
```

Também existe o atalho Windows:

```powershell
.\abrir_learnkit.bat
```

## Atualizações

O auto-updater usa GitHub Releases estáveis do repo `GlxV/learnkit`.

No modo de desenvolvimento (`python -m app.main`), a atualização automática fica
desativada e a tela de Configurações oferece apenas acesso manual às releases.
O fluxo de um clique fica habilitado somente em builds Windows empacotados com
PyInstaller `onedir`, contendo `LearnKit.exe` e `LearnKitUpdater.exe`.

Uma release instalável precisa publicar:

- `LearnKit-<versao>-win.zip`;
- `latest.json` ou `manifest.json` com `version`, `platform`, `asset_name`,
  `sha256`, `release_url` e `notes` opcional.

Sem manifest válido com SHA-256, o app mostra a release como manual-only e não
habilita `Update now`.

Mais detalhes: `docs/release.md`.

## Fluxo principal

1. Abra `Importação/IA`.
2. Escolha PDF, PPTX, DOCX, TXT ou MD.
3. Extraia o texto sem precisar escolher matéria antes.
4. Confira caracteres, palavras, avisos e preview.
5. Gere o prompt.
6. Cole o prompt em uma IA externa gratuita.
7. Cole a resposta no LearnKit.
8. Valide a resposta.
9. Escolha o modo de salvamento.
10. Para criar um bloco novo, escolha/crie matéria e módulo e informe o nome do bloco.
11. Para atualizar, escolha uma matéria, um módulo e um bloco existente.
12. Salve o pacote no LearnKit.
13. Estude pelo resumo, flashcards ou perguntas.

Ao atualizar um bloco existente, o LearnKit substitui resumo, flashcards, perguntas, texto extraído, prompt e resposta da IA daquele bloco. O progresso antigo de flashcards/perguntas removidos é limpo para não ficar apontando para itens que não existem mais.

## Formato da resposta da IA

O prompt atual pede:

```markdown
# RESUMO_TEXTO
Conteúdo em Markdown.

# RESUMO_VISUAL
{ "title": "...", "sections": [] }

# FLASHCARDS
## Card 1
Pergunta: ...
Resposta: ...

# PERGUNTAS
## Pergunta 1
Enunciado: ...
A) ...
B) ...
C) ...
D) ...
Gabarito: A
Explicação: ...
```

Se a IA enviar apenas `RESUMO_TEXTO`, o app salva o resumo simples. Se enviar `RESUMO_VISUAL` válido, o app também libera o modo visual/apresentação.

## Tela Banco de Dados

A UI tem uma página `Banco de Dados` para demonstrar persistência. Ela fica
oculta por padrão e aparece na sidebar somente quando `Modo desenvolvedor` está
ativado em Configurações.

Ela mostra:

- caminho do arquivo SQLite;
- status da conexão;
- quantidade de matérias;
- quantidade de módulos;
- quantidade de blocos;
- quantidade de flashcards;
- quantidade de perguntas;
- quantidade de registros de progresso;
- últimos registros criados.

Roteiro para demonstrar ao professor:

1. Abra o LearnKit.
2. Crie uma matéria.
3. Crie um módulo.
4. Importe um material e salve um bloco.
5. Abra `Banco de Dados`.
6. Clique em `Atualizar dados`.
7. Mostre os contadores.
8. Feche e abra o app.
9. Abra `Banco de Dados` novamente.
10. Mostre que os dados persistiram.
11. Abra um resumo visual.
12. Ative `Modo apresentação`.

## OCR local

O LearnKit tenta extrair texto de imagens em PDFs, PPTX e DOCX quando existe um backend OCR local disponível.

No Windows, o app tenta usar primeiro o OCR local do sistema via pacotes `winrt-*`. Se ele não estiver disponível, tenta usar Tesseract OCR com `pytesseract`. Nenhum desses caminhos usa cloud. Se nenhum backend OCR estiver pronto, o app continua extraindo texto normal e mostra avisos para arquivos com imagens.

## CLI temporária

A CLI ainda existe para testar fluxo de core:

```powershell
python -m app.cli.main create-subject "Matemática"
python -m app.cli.main create-module "Matemática" "1º Trimestre"
python -m app.cli.main add-block "Matemática" "1º Trimestre" "Funções do 1º grau" .\aula1.pdf
python -m app.cli.main generate-prompt "Matemática" "1º Trimestre" "Funções do 1º grau"
python -m app.cli.main import-ai-response "Matemática" "1º Trimestre" "Funções do 1º grau" .\resposta.md
```

## Testes

```powershell
python -m pytest -q
```

## Estrutura

```text
app/
  application/       # Casos de uso, query services e DTOs
  core/
    database/        # SQLiteStorage
    extractors/      # PDF/PPTX/DOCX/TXT/MD/código + OCR opcional
    importer/        # Parser Markdown/visual da resposta da IA
    models/          # Modelos de domínio
    prompt/          # Gerador de prompt
    services/        # Casos de uso do core
    storage/         # Storage JSON legado/compatibilidade
  infrastructure/    # GitHub Releases, update, SQLite repos/queries
  cli/               # CLI temporária
  ui/                # UI desktop PySide6
data/
  learnkit.db        # Banco SQLite local
tests/
```

## Limitações atuais

- PDFs escaneados dependem de OCR local disponível no sistema.
- O parser é robusto para o formato pedido pelo prompt, mas respostas muito fora do formato podem gerar avisos.
- O modo visual renderiza componentes seguros, não HTML arbitrário.
- Revisão espaçada avançada ainda não foi implementada.
