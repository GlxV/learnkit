# Ciclo de Revisao - Especificacao de Design

Data: 2026-05-24
Status: aprovado para implementacao

## Objetivo

Adicionar ao LearnKit um Ciclo de Revisao por Bloco de Estudo, baseado em
revisao espacada e revisao ativa. Cada bloco pode possuir uma agenda fixa de
revisoes futuras independente do agendamento adaptativo dos seus flashcards.

O fluxo esperado e:

1. Um bloco novo e criado ou importado.
2. Se a criacao automatica estiver ativa, o app agenda seu ciclo.
3. A Home indica revisoes pendentes e atrasadas.
4. O usuario abre a Fila de Revisoes e inicia uma sessao curta.
5. A revisao e concluida ou pulada sem alterar as demais etapas do ciclo.

## Decisoes Aprovadas

- `ReviewSchedule` representa uma revisao do bloco, nao de um flashcard.
- O agendamento adaptativo existente dos flashcards continua independente.
- A persistencia principal sera uma tabela SQLite `review_schedules`.
- Um bloco nao pode ter duas agendas para a mesma etapa.
- A criacao automatica do ciclo inicia desativada.
- O botao manual do bloco funciona mesmo com a criacao automatica desativada.
- Blocos existentes nao recebem ciclos retroativos.
- Atualizar o conteudo de um bloco nao recria, remove ou reinicia seu ciclo.
- As datas sao persistidas em UTC e apresentadas no horario local da interface.
- Nesta entrega nao havera notificacao nativa do Windows; os alertas sao visuais.

## Modelo De Dados

Criar o modelo `ReviewSchedule`:

```python
ReviewSchedule(
    id: str,
    study_block_id: str,
    subject_id: str,
    module_id: str,
    review_step: Literal["1h", "24h", "7d", "30d"],
    scheduled_at: str,
    completed_at: str | None,
    status: Literal["pending", "done", "skipped"],
    created_at: str,
)
```

Criar a tabela SQLite `review_schedules`, ligada a `study_blocks`, `subjects` e
`modules`, com `ON DELETE CASCADE` para acompanhar a exclusao real de um bloco.
A restricao `UNIQUE(study_block_id, review_step)` garante idempotencia mesmo se
mais de um gatilho tentar iniciar o ciclo.

Indices devem atender as consultas da fila:

- indice por `status, scheduled_at`;
- indice por `study_block_id`.

## Configuracoes

As preferencias permanecem em `data/settings.json`, como as demais preferencias
locais atuais:

```json
{
  "review_cycle_enabled": false,
  "review_step_1h_enabled": true,
  "review_step_24h_enabled": true,
  "review_step_7d_enabled": true,
  "review_step_30d_enabled": true,
  "preferred_review_time": ""
}
```

Regras:

- `review_cycle_enabled` governa somente a criacao automatica.
- Desativar a opcao global nao oculta, cancela nem bloqueia agendas existentes.
- As quatro etapas iniciam habilitadas.
- `preferred_review_time` e opcional, no formato local `HH:mm`.
- Se nenhuma etapa estiver habilitada, a ativacao manual e recusada com
  mensagem orientando habilitar pelo menos uma etapa.

## Calculo Do Ciclo

O servico de dominio para criacao do ciclo recebe o bloco, `studied_at` e as
preferencias aplicaveis. Somente etapas habilitadas sao geradas:

| Etapa | Data base | Ajuste de horario |
| --- | --- | --- |
| `1h` | `studied_at + 1 hora` | nunca ajustada |
| `24h` | `studied_at + 24 horas` | horario preferido, se definido |
| `7d` | `studied_at + 7 dias` | horario preferido, se definido |
| `30d` | `studied_at + 30 dias` | horario preferido, se definido |

Para o horario preferido, o calculo deve preservar a data local da etapa e
converter o resultado novamente para UTC antes de persistir. Sem preferencia,
as etapas preservam o horario original do estudo.

## Gatilhos De Criacao

### Bloco Novo

Ao criar/importar um novo bloco por um fluxo de aplicacao:

- criar o ciclo usando o momento da criacao/importacao se
  `review_cycle_enabled` estiver ativo;
- nao criar qualquer agenda se a opcao global estiver desativada.

### Bloco Antigo Ou Existente

O app nao deve migrar nem preencher ciclos para blocos preexistentes. No fluxo
`Continuar estudo`, antes de abrir o resumo:

- registrar o acesso atual;
- criar o ciclo usando o momento desse novo estudo somente se a opcao global
  estiver ativa e o bloco ainda nao possuir ciclo.

Abrir listagens, navegar ate um bloco ou atualizar seu conteudo nao constitui
novo estudo e nao cria ciclo automaticamente.

### Ativacao Manual

Na tela do bloco, o botao `Ativar Ciclo de Revisao`:

- utiliza o momento do clique como `studied_at`;
- funciona independentemente de `review_cycle_enabled`;
- respeita quais etapas individuais estao habilitadas;
- informa que o ciclo ja existe quando houver qualquer agenda para o bloco;
- recusa a criacao quando todas as etapas estiverem desabilitadas.

## Servicos E Integracao

Adicionar componentes dedicados, mantendo as fronteiras atuais:

- modelo de dominio para a agenda;
- servico puro que calcula os horarios de um ciclo;
- repositorio SQLite para gravar, consultar e atualizar agendas;
- caso de uso para ativar o ciclo e marcar revisao como concluida ou pulada;
- query service para montar fila, resumo da Home e contexto da sessao.

A agenda de bloco nao deve ser incorporada em `StudyProgress` nem no
`ReviewScheduler` de flashcards. As sessoes podem chamar os casos de uso ja
existentes para respostas de perguntas e avaliacoes de cards, fazendo com que
o progresso individual continue funcionando normalmente.

## Navegacao E Home

Adicionar uma pagina `Revisoes`, separada de `Flashcards` e `Perguntas`, na
sidebar principal.

Na Home, adicionar um card `Revisoes de Hoje`, alimentado apenas pelas agendas
de bloco:

- quantidade de revisoes pendentes agendadas para hoje;
- quantidade atrasada;
- proxima revisao pendente, no horario local;
- botao `Abrir fila de revisoes`.

Os cards e indicadores atuais de flashcards e perguntas permanecem separados.

## Fila De Revisoes

A pagina `Fila de Revisoes` apresenta tres grupos de agendas `pending`,
ordenados por `scheduled_at`:

- `Atrasadas`: agendas anteriores ao inicio do dia local atual.
- `Para agora / hoje`: agendas do dia local atual; as que ja venceram no
  horario recebem destaque adicional.
- `Proximas`: agendas apos o final do dia local atual.

Cada item mostra:

- titulo do bloco;
- materia e modulo;
- etapa em linguagem amigavel;
- data e horario local;
- estado visual;
- botao primario `Revisar`;
- botoes secundarios `Marcar como feita` e `Pular`.

Revisoes `done` e `skipped` deixam as listas pendentes, permanecendo
persistidas para historico.

## Estado Do Ciclo No Bloco

Na pagina `Estudos`, o bloco selecionado ganha uma secao `Ciclo de Revisao`:

- sem agenda: explicacao curta e botao `Ativar Ciclo de Revisao`;
- com agenda: proxima revisao pendente, progresso `N de M concluidas` e botao
  `Abrir fila`.

O botao manual deve estar disponivel mesmo quando a criacao automatica global
estiver desligada.

## Sessao Curta De Revisao

O clique em `Revisar` abre um dialogo para uma agenda especifica, com titulo do
bloco, materia, modulo, etapa e horario agendado.

O dialogo monta sua composicao somente a partir de conteudo existente:

| Etapa | Composicao preferencial |
| --- | --- |
| `1h` | mini resumo, ate 3 flashcards, 1 pergunta |
| `24h` | pergunta ativa primeiro, ate 3 flashcards, resumo secundario |
| `7d` | resumo curto, perguntas e cards dificeis primeiro quando houver historico |
| `30d` | resumo curto, perguntas gerais disponiveis e flashcards complementares |

Comportamentos obrigatorios:

- resumo ausente nao impede a sessao;
- flashcards ausentes nao impedem a sessao;
- perguntas ausentes nao impedem a sessao;
- flashcards so revelam a resposta por acao do usuario;
- perguntas nao exibem gabarito antes de uma tentativa;
- avaliacoes de cards reutilizam o fluxo adaptativo atual;
- respostas de perguntas reutilizam o fluxo de progresso atual;
- uma sessao sem itens ativos ainda permite concluir ou pular a agenda.

`Concluir revisao` define `status="done"` e registra `completed_at`. `Pular`
define `status="skipped"` e tambem registra `completed_at`. Nenhuma dessas
acoes modifica as etapas restantes do ciclo.

## Notificacoes Visuais

O escopo desta entrega inclui apenas notificacao dentro do aplicativo:

- card na Home;
- contagens e agrupamento na fila;
- destaque visual de itens atrasados;
- proxima revisao na pagina do bloco.

Notificacoes nativas, tarefas em background e integracao com o sistema
operacional ficam fora do escopo.

## Migracao E Compatibilidade

- Aplicar uma migracao versionada para criar `review_schedules`.
- A migracao nao deve criar agendas para blocos existentes.
- A persistencia JSON legada continua sem suporte completo a nova agenda; a UI
  principal usa SQLite, que e o caminho suportado da feature.
- A atualizacao de materiais de um bloco preserva as linhas da agenda.
- A exclusao do bloco remove sua agenda por integridade referencial.

## Validacao

Adicionar testes automatizados para:

- calculo dos quatro horarios, incluindo horario preferido e regra fixa de 1h;
- etapas desabilitadas e tentativa sem nenhuma etapa ativa;
- criacao automatica condicionada a preferencia global;
- criacao manual com a preferencia global desligada;
- idempotencia por bloco e etapa;
- nenhum preenchimento retroativo na migracao;
- preservacao de agenda ao atualizar conteudo;
- consultas de atrasadas, hoje e proximas;
- transicoes `pending -> done` e `pending -> skipped`;
- composicao de sessao com resumo, perguntas ou flashcards ausentes;
- navegacao e instanciacao das novas superficies em modo offscreen.

Na validacao manual, confirmar:

1. criar um bloco com criacao automatica ativa gera as etapas configuradas;
2. criar outro bloco preserva as revisoes anteriores;
3. ativar manualmente com global desligado funciona;
4. concluir ou pular remove o item da fila pendente;
5. o card da Home e a proxima revisao do bloco refletem a mudanca.

## Fora Do Escopo

- notificacoes nativas do Windows;
- reagendamento automatico depois de conclusao ou pulo;
- sincronizacao cloud;
- unificacao da agenda do bloco com a agenda adaptativa dos flashcards;
- retroalimentacao avancada por dificuldade alem da priorizacao simples dos
  cards ja marcados como dificeis.
