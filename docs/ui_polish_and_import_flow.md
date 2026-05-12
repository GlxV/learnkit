# UI Polish e Novo Fluxo de Importacao/IA

## O que foi corrigido

- Dropdowns globais: `QComboBox` agora usa tema dark, borda sutil, hover/focus, popup escuro, item selecionado destacado e seta customizada em `app/ui/assets/combo_down.svg`.
- Botoes: estados `hover`, `pressed`, `disabled` e primario foram reforcados no `theme.py`.
- Feedback: foi criado `app/ui/components/toast.py` com toast dark, fade-in/fade-out e sumico automatico.
- Helpers de botao: `set_button_loading()` e `flash_button_success()` foram adicionados em `app/ui/feedback.py`.
- Cursores: `MainWindow` aplica cursor de mao em botoes e dropdowns ativos.
- Lista de arquivos: foi criado `FileListItem`, evitando caminhos enormes na tela principal.
- Arquivos por arrastar-e-soltar: a area de arquivos aceita drop real de PDF/PPTX/DOCX/TXT/MD.
- Importacao/IA: o fluxo nao cria mais bloco durante a extracao. A extracao roda separada, em background, e o bloco so e salvo no final.

## Novo fluxo da Importacao/IA

1. Arquivos: selecionar PDF/PPTX/DOCX/TXT/MD sem escolher materia.
2. Extracao: extrair texto em `QThread`, ver contagens, avisos, falhas e preview.
3. Prompt: gerar prompt com opcoes avancadas de quantidade, dificuldade e linguagem.
4. Resposta da IA: colar Markdown e validar o parser.
5. Salvar no LearnKit: escolher ou criar materia, modulo e nome do bloco.
6. Resultado: abrir resumo, flashcards, perguntas ou modulo.

## Regras de validacao

- Sem arquivo: `Extrair texto` mostra toast de aviso.
- Sem texto extraido: `Gerar prompt` fica desabilitado e tambem valida no clique.
- Sem resposta da IA: `Validar resposta` mostra toast.
- Resposta sem conteudo reconhecido: nao habilita salvamento.
- Sem materia/modulo/bloco no final: `Salvar bloco de estudo` mostra aviso.
- Conteudo parcial com warnings pode ser salvo depois da validacao.

## Core ajustado

Foi adicionado `BlockService.save_imported_package(...)` para salvar, em uma unica operacao:

- arquivos importados;
- texto extraido;
- prompt gerado;
- resposta original da IA;
- resumo;
- flashcards;
- perguntas;
- `progress.json`.

Esse metodo preserva a separacao entre UI e core e evita que a tela manipule JSON diretamente.

## Como testar

1. Rode `python -m app.main`.
2. Abra `Importacao/IA`.
3. Selecione ou arraste um arquivo `.txt` ou `.md` sem escolher materia.
4. Clique em `Extrair texto` e confira preview/contadores.
5. Gere e copie o prompt.
6. Cole `tests/fixtures/sample_ai_response.md`.
7. Valide a resposta.
8. So no passo final escolha/crie materia, modulo e bloco.
9. Salve e abra resumo/flashcards/perguntas.

## Limitacoes restantes

- OCR para PDF escaneado continua preparado como futuro, nao obrigatorio.
- O popup do `QComboBox` depende do motor do Qt; o QSS cobre o popup e os itens, mas o comportamento nativo ainda vem do PySide6.
