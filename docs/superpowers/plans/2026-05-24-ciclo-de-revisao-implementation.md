# Ciclo de Revisao - Plano Tecnico

Data: 2026-05-24
Especificacao: `docs/superpowers/specs/2026-05-24-ciclo-de-revisao-design.md`

## Objetivo E Limites

Implementar agendas fixas por Bloco de Estudo em SQLite, com criacao
automatica opcional, ativacao manual, fila dedicada, sessao curta e
indicadores visuais. O agendamento adaptativo dos flashcards continua isolado.
Nao incluir notificacao nativa nem retrocriacao para blocos existentes.

## Decisoes Tecnicas

- Usar `ReviewSchedule` como modelo em `app/core/models`, pois os modelos
  persistidos atuais ainda vivem nessa camada de compatibilidade.
- Usar `BlockReviewCycleScheduler` em `app/domain/services` para calculo puro
  de datas; o `ReviewScheduler` atual permanece exclusivo de flashcards.
- Usar repositorio SQLite dedicado e expor metodos pela facade
  `SQLiteStorage`, seguindo a migracao incremental ja adotada.
- Armazenar preferencias no JSON ja usado por `SettingsPage`; os casos de uso
  recebem o mapping de configuracoes explicitamente, evitando acoplamento de
  dominio ao filesystem.
- Criar `ReviewCycleQueryService` e DTOs especificos em `app/application`
  para que a nova UI nao dependa de dicionarios de banco.
- Criar pagina `ReviewsPage` e dialogo `ReviewSessionDialog`; as paginas
  existentes continuam responsaveis por estudo livre de cards/perguntas.

## Lote 1 - Dominio E Persistencia

Arquivos previstos:

- `app/core/models/review_schedule.py`
- `app/domain/services/block_review_cycle_scheduler.py`
- `app/infrastructure/sqlite/migrations.py`
- `app/infrastructure/sqlite/row_mappers.py`
- `app/infrastructure/sqlite/repositories/review_schedule_repository.py`
- `app/core/database/sqlite_storage.py`
- `tests/test_review_cycle_scheduler.py`
- `tests/test_review_schedule_storage.py`

Passos:

1. Escrever testes para calculo UTC, horario preferido local, etapas
   desabilitadas e erro quando nenhuma etapa estiver habilitada.
2. Implementar o modelo e o scheduler puro.
3. Escrever testes para tabela, insert idempotente, listagem e mudanca de
   status.
4. Criar migracao versionada e repositorio; expor operacoes na facade SQLite.

Verificacao do lote:

```powershell
python -m pytest -q tests/test_review_cycle_scheduler.py tests/test_review_schedule_storage.py tests/test_sqlite_bootstrap.py
```

## Lote 2 - Casos De Uso, Gatilhos E Consultas

Arquivos previstos:

- `app/application/dto/review_cycle.py`
- `app/application/use_cases/manage_review_cycle.py`
- `app/application/query_services/review_cycle_query_service.py`
- `app/application/use_cases/import_study_package.py`
- `app/application/query_services/study_session_query_service.py`
- `app/core/services/block_service.py`
- `tests/test_review_cycle_use_case.py`
- `tests/test_import_existing_block.py`
- `tests/test_application_layer.py`

Passos:

1. Escrever testes para ativacao manual, deduplicacao, concluir/pular e
   agrupamento `overdue/today/upcoming`.
2. Implementar casos de uso e consultas tipadas.
3. Cobrir criacao automatica no fluxo de importacao com configuracao
   explicitamente fornecida pela UI.
4. Integrar o inicio automatico no fluxo `Continuar estudo`, sem disparar em
   simples navegacao ou atualizacao.
5. Garantir que update de pacote nao altere agendas persistidas.

Verificacao do lote:

```powershell
python -m pytest -q tests/test_review_cycle_use_case.py tests/test_application_layer.py tests/test_import_existing_block.py
```

## Lote 3 - Configuracoes E Superficies PySide

Arquivos previstos:

- `app/ui/pages/settings_page.py`
- `app/ui/pages/reviews_page.py`
- `app/ui/pages/studies_page.py`
- `app/ui/pages/home_page.py`
- `app/ui/navigation.py`
- `app/ui/main_window.py`
- `app/ui/components/icons.py` se necessario para iconografia
- `tests/test_review_cycle_ui.py`
- `tests/test_ui_smoke.py`
- `tests/test_developer_mode.py`

Passos:

1. Adicionar configuracoes globais e validacao de horario preferido.
2. Adicionar pagina `Revisoes`, agrupamentos, acoes de status e dialogo de
   sessao com conteudo parcial.
3. Expor estado e ativacao manual no bloco selecionado em `Estudos`.
4. Adicionar card independente de agenda na Home e rota/sidebar.
5. Verificar que configuracao global controla apenas criacao automatica.

Verificacao do lote:

```powershell
$env:QT_QPA_PLATFORM='offscreen'; python -m pytest -q tests/test_review_cycle_ui.py tests/test_ui_smoke.py tests/test_developer_mode.py
```

## Lote 4 - Integracao E Validacao Final

Passos:

1. Executar toda a suite automatizada.
2. Executar a aplicacao offscreen e validar instancia/navegacao.
3. Abrir a interface local, quando praticavel no ambiente, e inspecionar Home,
   pagina Revisoes, Estudos e Configuracoes com dados de agenda.
4. Revisar `git diff` para confirmar que `docs/requisitos_rf_rnf.md` nao foi
   incorporado acidentalmente.

Verificacao:

```powershell
python -m pytest -q
```

## Riscos E Tratamento

- `LocalStorage` legado nao tem tabela de agendas: a nova funcionalidade sera
  invocada pela UI SQLite; fluxos legados nao devem falhar quando nao
  fornecerem suporte a agenda.
- O horario preferido depende do timezone local do sistema: os testes usarao
  timezone explicito no scheduler e a UI convertera usando timezone local.
- A Home possui indicadores preexistentes de cards/perguntas: os novos dados
  terao nomes e query separados para nao alterar seus significados.
- O dialogo de sessao reutiliza componentes e casos de uso atuais; ele nao
  devera assumir que exista qualquer item de estudo especifico.

## Forma De Execucao

As tarefas compartilham contratos entre modelo, repositorio, consultas e UI;
por isso serao executadas diretamente nesta sessao com checkpoints por lote,
em vez de delegadas a agentes independentes.
