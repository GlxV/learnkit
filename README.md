# LearnKit

LearnKit e um aplicativo desktop local e open source para transformar PDF, PPTX, DOCX, TXT, Markdown e arquivos de codigo/texto comuns em materiais de estudo organizados.

Ele nao usa cloud obrigatoria, nao usa API paga de IA e nao tem plano premium. O fluxo de IA e manual: o app gera um prompt, voce cola em uma IA gratuita externa, como Gemini, e depois cola a resposta Markdown de volta no LearnKit.

## Como o conteudo e organizado

```text
Materia
  -> Modulo
      -> Bloco de Estudo
          -> Resumo
          -> Flashcards
          -> Perguntas
          -> Arquivos importados
          -> Texto extraido
          -> Prompt gerado
          -> Resposta original da IA
          -> Progresso local
```

Novos blocos nao sobrescrevem blocos antigos. Se um nome ja existir, o storage cria slugs unicos automaticamente, como `funcoes_do_1_grau_2`.

## Instalar

Requisitos:

- Python 3.11+
- PyMuPDF
- python-pptx
- Pillow
- PySide6
- pytest para desenvolvimento

```powershell
python -m pip install -r requirements.txt
```

## Rodar a UI

```powershell
python -m app.main
```

A UI atual ja usa o storage real como fonte principal. Se nao houver dados, ela mostra estados vazios em vez de inventar numeros. Dados demo podem ser ligados manualmente com `LEARNKIT_DEMO=1`.

## Fluxo principal na UI

1. Abra `Materias` e crie uma materia personalizada.
2. Crie um modulo dentro da materia.
3. Abra `Importacao/IA`.
4. Importe PDF, PPTX, DOCX, TXT, MD ou arquivo de codigo/texto comum.
5. Extraia texto e confira o preview.
6. Gere e copie o prompt.
7. Cole o prompt no Gemini ou outra IA gratuita.
8. Cole a resposta Markdown no LearnKit.
9. Valide a resposta.
10. Escolha ou crie materia, modulo e bloco no final.
11. Salve o bloco e estude resumo, flashcards e perguntas.

## OCR local

O LearnKit tenta extrair texto de imagens em PDFs, PPTX e DOCX quando existe um backend OCR local disponivel.

No Windows, o backend usado e o OCR local do sistema via pacotes `winrt-*`. Ele nao usa cloud. Se esses pacotes ou idiomas OCR nao estiverem disponiveis, o app continua extraindo texto normal e mostra avisos para arquivos com imagens.

## Storage local

Os dados ficam em `data/`:

```text
data/
  subjects/
    matematica/
      subject.json
      modules/
        primeiro_trimestre/
          module.json
          blocks/
            funcoes_do_1_grau/
              block.json
              extracted_text.md
              generated_prompt.md
              ai_response.md
              summary.md
              flashcards.json
              questions.json
              progress.json
  settings.json
```

## CLI temporaria

Criar materia:

```powershell
python -m app.cli.main create-subject "Matematica"
```

Criar modulo:

```powershell
python -m app.cli.main create-module "Matematica" "1o Trimestre"
```

Adicionar bloco com arquivos:

```powershell
python -m app.cli.main add-block "Matematica" "1o Trimestre" "Funcoes do 1o grau" .\aula1.pdf
```

Gerar prompt:

```powershell
python -m app.cli.main generate-prompt "Matematica" "1o Trimestre" "Funcoes do 1o grau"
```

Importar resposta da IA:

```powershell
python -m app.cli.main import-ai-response "Matematica" "1o Trimestre" "Funcoes do 1o grau" .\resposta.md
```

Estudar:

```powershell
python -m app.cli.main study-block "Matematica" "1o Trimestre" "Funcoes do 1o grau"
python -m app.cli.main study-module "Matematica" "1o Trimestre"
python -m app.cli.main study-subject "Matematica"
```

## Testes

```powershell
python -m pytest -q
```

## Estrutura

```text
app/
  core/
    extractors/      # PDF/PPTX/DOCX/TXT/MD/codigo + OCR opcional
    importer/        # Parser Markdown da resposta da IA
    models/          # Modelos de dominio
    prompt/          # Gerador de prompt
    services/        # Casos de uso do core
    storage/         # JSON/Markdown local
  cli/               # CLI temporaria
  ui/                # UI desktop PySide6
data/                # Dados locais do usuario
tests/               # Testes do core
```

## Limites atuais

- OCR em portugues depende dos idiomas OCR disponiveis no sistema. Sem Tesseract/idioma PT-BR, alguns textos em imagem ainda podem sair imperfeitos.
- O parser Markdown e robusto para o formato pedido pelo prompt, mas respostas muito fora do formato podem gerar avisos.
- Revisao espacada e estatisticas historicas avancadas ainda nao foram implementadas.
