# Revisao Combinada - Plano Tecnico

Data: 2026-05-24
Status: desenho aprovado para implementacao

## Objetivo E Limites

Permitir selecionar dois ou mais Blocos de Estudo na pagina `Estudos` e
executar uma unica sessao temporaria que reaproveita resumos, flashcards e
perguntas dos blocos escolhidos.

- A combinacao nao cria bloco, tabela, agenda ou entidade persistente.
- `ReviewSchedule` continua restrito aos ciclos individuais existentes.
- Flashcards, perguntas e acessos feitos na sessao continuam sendo gravados no
  progresso do bloco de origem.
- A sessao individual agendada nao sera refatorada nem alterada.

## Decisoes Tecnicas

- Criar DTOs de aplicacao para a sessao combinada e suas origens, com
  `block_id`, `block_title` e `item_id`.
- Montar a sessao em memoria em `StudySessionQueryService`, a partir de uma
  lista de IDs unicos.
- Deduplicar flashcards por pergunta e resposta normalizadas; deduplicar
  perguntas por enunciado, alternativas e gabarito normalizados. Cada item
  visual retém todas as origens equivalentes para que a interacao atualize
  todos os blocos correspondentes.
- Preservar resumos por bloco, sem gerar ou mesclar texto novo.
- Criar um dialogo PySide dedicado para a revisao combinada. Ele reutiliza
  componentes visuais e casos de uso de progresso, mas nao opera sobre uma
  linha de `review_schedules`.
- Adicionar selecao discreta apenas aos `StudyBlockRow` usados em `Estudos`,
  por meio de chip selecionavel e borda ativa; usos existentes do componente
  continuam sem selecao.
- Limpar a selecao ao mudar materia, modulo ou ocultar a pagina `Estudos`.

## Lote 1 - Sessao Transitoria E Progresso

Arquivos:

- `app/application/dto/combined_review.py`
- `app/application/query_services/study_session_query_service.py`
- `tests/test_combined_review_session.py`

Passos:

1. Testar montagem com dois ou mais blocos, IDs repetidos e itens repetidos.
2. Implementar DTOs e a consulta em memoria.
3. Testar que uma interacao deduplicada pode preservar todas as origens para
   atualizacao posterior.

Verificacao:

```powershell
python -m pytest -q tests/test_combined_review_session.py
```

## Lote 2 - Selecao E Dialogo

Arquivos:

- `app/ui/components/cards.py`
- `app/ui/pages/studies_page.py`
- `app/ui/pages/combined_review_dialog.py`
- `app/ui/theme.py`
- `tests/test_combined_review_ui.py`

Passos:

1. Testar barra de selecao, limite minimo de dois blocos e limpeza.
2. Adicionar chip de selecao e barra de acao no escopo do modulo exibido.
3. Criar dialogo com blocos incluidos, resumos separados e tags de origem.
4. Roteiar classificacao/resposta a todas as origens e conclusao a
   `record_access` de cada bloco.
5. Testar que concluir pode iniciar ciclos individuais conforme a configuracao
   ja existente, sem persistir uma combinacao.

Verificacao:

```powershell
$env:QT_QPA_PLATFORM='offscreen'; python -m pytest -q tests/test_combined_review_ui.py tests/test_review_cycle_ui.py
```

## Lote 3 - Validacao Visual E Regressao

Passos:

1. Gerar capturas offscreen em `1366x768` da pagina com dois blocos
   selecionados e do dialogo combinado.
2. Confirmar fundo tematico, rodape, scroll e identificacao de origem.
3. Executar a suite completa e, se disponivel, a verificacao estatica.

Verificacao:

```powershell
python -m pytest -q
python -m ruff check app tests
```

## Riscos E Tratamento

- Interacao em item deduplicado nao pode perder progresso: todas as origens
  serao mantidas no DTO e iteradas pelos casos de uso existentes.
- Concluir a sessao pode iniciar ciclos de blocos ainda sem agenda apenas
  quando a configuracao automatica atual estiver habilitada, pois reutiliza
  `record_access`.
- A selecao e estado efemero da pagina e nao sera serializada.
- O novo dialogo recebera estilos explicitos de fundo/scroll/rodape para nao
  reintroduzir superficies pretas.

## Forma De Execucao

A consulta transitoria, a selecao e o dialogo compartilham os mesmos contratos
de origem e progresso. A implementacao sera feita nesta sessao, em lotes
testados antes da validacao visual final.
