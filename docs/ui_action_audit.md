# Auditoria de Acoes da UI - LearnKit

Data: 2026-05-10

Escopo auditado:

- `app/ui/main_window.py`
- `app/ui/components/`
- `app/ui/pages/`

Status:

- **Funcional**: acao executa fluxo real ou navega corretamente.
- **Desabilitado corretamente**: acao aparece indisponivel com tooltip claro.
- **Futuro/TODO explicito**: acao mostra mensagem clara de recurso futuro.

## Resumo

| Area | Problema principal encontrado | Correcao |
| --- | --- | --- |
| Feedback global | Acoes usavam `QMessageBox` isolado ou nao davam feedback | Criado `app/ui/feedback.py` com `show_toast`, `confirm_action`, `future_action` e logging |
| Logs | Nao havia log de acoes importantes | Criado log em `app/logs/learnkit.log` |
| Busca global | Campo de busca nao fazia nada | Enter agora abre modal de resultados reais por materia, modulo, bloco, flashcard e pergunta |
| Topbar | Dropdown de materia era visual | Agora filtra Home/Progresso e tenta selecionar materia em paginas compativeis |
| Cards/linhas de bloco | `Estudar` em `StudyBlockRow` nao tinha acao propria | Criado sinal `open_requested`; paginas conectam para abrir estudo real |
| Comunidade/open source | Botoes pareciam funcionais, mas nao tinham destino | Agora mostram mensagem explicita de recurso futuro |
| Importacao/IA | Faltava remover arquivo individual e botoes finais ficavam ativos cedo | Adicionado `Remover selecionado`; botoes finais ficam desabilitados ate importar resposta |
| Configuracoes | Backup/abrir pasta/exportar/limpar cache eram ausentes ou placeholder | Implementado abrir pasta, exportar dados, backup e limpar cache com confirmacao |

## Sidebar

| Pagina/componente | Acao | Estado anterior | Problema encontrado | Correcao feita | Status final |
| --- | --- | --- | --- | --- | --- |
| Sidebar | Inicio, Materias, Estudos, Flashcards, Perguntas, Progresso, Importacao/IA, Configuracoes | Funcional | Navegava, mas sem logging | Navegacao registra `page_opened` | Funcional |
| Sidebar | Comunidade abrir/fechar | Funcional parcial | Abria/fechava sem log | Toggle registra `community_toggled` | Funcional |
| Sidebar Comunidade | Feito com codigo aberto, Ver repositorio, Contribuir, Reportar problema | Botao sem handler | Clique nao fazia nada | Conectado a `future_action` com tooltip | Futuro/TODO explicito |

## Topbar

| Pagina/componente | Acao | Estado anterior | Problema encontrado | Correcao feita | Status final |
| --- | --- | --- | --- | --- | --- |
| Topbar | Busca global | Campo morto | Nenhum handler | `returnPressed` abre busca global real | Funcional |
| Topbar | Dropdown Todas as materias | Visual | Nao filtrava nada | `subject_changed` atualiza filtro global em paginas suportadas | Funcional |

## Home

| Pagina/componente | Acao | Estado anterior | Problema encontrado | Correcao feita | Status final |
| --- | --- | --- | --- | --- | --- |
| Home | Criar primeira materia | Funcional | Navegava sem feedback proprio | Mantido como navegacao para Materias | Funcional |
| Home | Importar conteudo | Funcional | Navegacao simples | Mantido para Importacao/IA | Funcional |
| Home | Continuar | Funcional parcial | Abria Estudos sem selecionar bloco | Agora chama `open_block(block_id, "studies")` | Funcional |
| Home | Flashcards | Funcional parcial | Abria pagina sem selecionar bloco | Agora chama `open_block(block_id, "flashcards")` | Funcional |
| Home | Ver todas em Suas materias | Funcional | Navegava para Materias | Mantido | Funcional |
| Home | Ver todos em Modulos recentes | Ausente | Cabecalho nao tinha acao | Adicionado botao para Materias | Funcional |
| Home | Ver todos em Ultimos blocos | Ausente | Cabecalho nao tinha acao | Adicionado botao para Estudos | Funcional |
| Home | Abrir materia | Ausente | Linhas eram apenas visuais | Adicionado botao `Abrir` por materia | Funcional |
| Home | Abrir modulo | Ausente | Linhas eram apenas visuais | Adicionado botao `Abrir` por modulo | Funcional |
| Home | Abrir bloco | Ausente | Linhas eram apenas visuais | Adicionado botao `Abrir` por bloco | Funcional |
| OpenSourcePanel | Ver no GitHub | Morto | Sem handler | Conectado a mensagem de recurso futuro | Futuro/TODO explicito |

## Materias

| Pagina/componente | Acao | Estado anterior | Problema encontrado | Correcao feita | Status final |
| --- | --- | --- | --- | --- | --- |
| Materias | Nova materia personalizada | Funcional | Criava no storage, mas sem toast/log | Adicionado feedback e log | Funcional |
| Materias | Selecionar materia | Funcional | Sem entrada externa para busca/topbar | Adicionado `select_subject_by_name` | Funcional |
| Materias | Criar modulo | Funcional | Sem toast/log | Adicionado feedback e log | Funcional |
| Materias | Estudar materia | Ausente | Botao pedido nao existia | Adicionado botao que navega para Estudos | Funcional |
| Materias | Adicionar bloco | Funcional | Navegava para importacao | Mantido | Funcional |
| Materias | Excluir materia | Funcional parcial | Usava confirmacao local | Agora usa `confirm_action`, toast e log | Funcional |
| Materias | Abrir modulo | Funcional | Seleciona modulo | Mantido | Funcional |
| Materias | Excluir modulo | Funcional parcial | Usava confirmacao local | Agora usa helper, toast e log | Funcional |
| Materias | Estudar bloco | Morto em `StudyBlockRow` | Botao Estudar nao emitia acao | `StudyBlockRow.open_requested` conectado para Estudos | Funcional |
| Materias | Excluir bloco | Ausente | Nao havia acao direta | Adicionado botao `Excluir bloco` com confirmacao | Funcional |
| Materias | Renomear materia/modulo/bloco | Ausente | Ainda nao existe editor inline | Nao adicionado nesta rodada para evitar fluxo incompleto | Futuro/TODO explicito |

## Estudos

| Pagina/componente | Acao | Estado anterior | Problema encontrado | Correcao feita | Status final |
| --- | --- | --- | --- | --- | --- |
| Estudos | Dropdown Materia/Modulo | Funcional | Atualizava lista | Mantido | Funcional |
| Estudos | Continuar estudo | Funcional | Abre resumo e registra acesso | Adicionado log `block_accessed` | Funcional |
| Estudos | Ver resumo | Funcional | Abre dialog Markdown basico | Adicionado toast | Funcional |
| Estudos | Resumo/Flashcards/Perguntas | Funcional | Flashcards/Perguntas nao recebiam bloco | Navegacao por `open_block` quando chamada de fora | Funcional |
| Estudos | Estudar nos blocos recentes | Morto | `StudyBlockRow` sem handler | Conectado a `select_block_by_id` | Funcional |
| Estudos | Importar novo bloco | Funcional | Navega para Importacao/IA | Mantido | Funcional |

## Flashcards

| Pagina/componente | Acao | Estado anterior | Problema encontrado | Correcao feita | Status final |
| --- | --- | --- | --- | --- | --- |
| Flashcards | Dropdown Materia/Modulo/Bloco | Funcional | Atualizava cards reais | Mantido | Funcional |
| Flashcards | Selecionar bloco na lista | Funcional | Selecionava combo | Mantido | Funcional |
| Flashcards | Virar card | Funcional | Alterna frente/verso | Mantido | Funcional |
| Flashcards | Anterior/Proximo | Funcional | Navega dentro da lista | Mantido | Funcional |
| Flashcards | Dificil/Dominei/Pular | Funcional | Gravava progresso sem feedback | Adicionado toast e log `flashcard_marked` | Funcional |
| Flashcards | Abrir bloco vindo de busca/Home/Importacao | Parcial | Nao havia API de selecao externa | Adicionado `select_block_by_id` | Funcional |

## Perguntas

| Pagina/componente | Acao | Estado anterior | Problema encontrado | Correcao feita | Status final |
| --- | --- | --- | --- | --- | --- |
| Perguntas | Dropdown Materia/Modulo/Bloco | Funcional | Atualizava perguntas reais | Mantido | Funcional |
| Perguntas | Selecionar conjunto | Funcional | Selecionava bloco | Mantido | Funcional |
| Perguntas | Selecionar alternativa | Funcional | Destacava alternativa | Mantido | Funcional |
| Perguntas | Responder | Funcional parcial | Sem alternativa falhava silenciosamente; botao seguia ativo apos resposta | Adicionado toast de aviso e desabilitacao apos responder | Funcional |
| Perguntas | Anterior/Proxima questao | Funcional | Navega entre questoes | Mantido | Funcional |
| Perguntas | Explicacao/gabarito | Funcional | Aparece apos resposta | Mantido | Funcional |
| Perguntas | Abrir bloco vindo de busca/Home/Importacao | Parcial | Nao havia API de selecao externa | Adicionado `select_block_by_id` | Funcional |
| QuestionViewer componente | Alternativas | Morto se componente fosse usado | Botoes internos nao emitiam evento | Adicionado sinal `option_selected` | Funcional |

## Progresso

| Pagina/componente | Acao | Estado anterior | Problema encontrado | Correcao feita | Status final |
| --- | --- | --- | --- | --- | --- |
| Progresso | Importar conteudo no estado vazio | Funcional | Navega para Importacao/IA | Mantido | Funcional |
| Progresso | Filtro topbar por materia | Ausente | Sempre mostrava agregado global | Adicionado `set_subject_filter` e agregado filtrado | Funcional |
| Progresso | Ver relatorio completo/graficos avancados | Ausente | Ainda nao existe tela analitica completa | Nao exposto como botao funcional | Futuro/TODO explicito |

## Importacao/IA

| Pagina/componente | Acao | Estado anterior | Problema encontrado | Correcao feita | Status final |
| --- | --- | --- | --- | --- | --- |
| Importacao/IA | Escolher/criar materia | Funcional | Criava no storage durante extracao | Adicionado log quando criado pelo fluxo | Funcional |
| Importacao/IA | Escolher/criar modulo | Funcional | Criava no storage durante extracao | Adicionado log quando criado pelo fluxo | Funcional |
| Importacao/IA | Selecionar arquivos | Funcional | Sem feedback/log | Adicionado toast e log | Funcional |
| Importacao/IA | Remover arquivo selecionado | Ausente | So havia limpar lista inteira | Adicionado botao e handler | Funcional |
| Importacao/IA | Limpar lista | Funcional | Sem feedback | Adicionado toast | Funcional |
| Importacao/IA | Extrair texto | Funcional | Rodava em thread | Adicionado feedback/log de inicio/fim/falha | Funcional |
| Importacao/IA | Gerar prompt | Funcional | Sem feedback/log | Adicionado toast/log | Funcional |
| Importacao/IA | Copiar prompt | Funcional parcial | Copiava vazio sem aviso | Agora exige prompt nao vazio | Funcional |
| Importacao/IA | Abrir Gemini | Funcional | Abria browser sem feedback | Adicionado toast/log | Funcional |
| Importacao/IA | Importar resposta | Funcional parcial | Aceitava texto vazio ate parser reclamar | Valida vazio, salva, parseia, habilita acoes finais | Funcional |
| Importacao/IA | Ver resumo/Flashcards/Perguntas | Parcial | Botoes ativos cedo e sem bloco selecionado | Desabilitados ate importacao; navegam com `open_block` | Funcional |

## Configuracoes

| Pagina/componente | Acao | Estado anterior | Problema encontrado | Correcao feita | Status final |
| --- | --- | --- | --- | --- | --- |
| Configuracoes | Tema/cor/densidade/estudos | Funcional parcial | Salvava so no botao final | Mantido com persistencia em `data/settings.json` | Funcional |
| Configuracoes | Salvar configuracoes | Funcional | Salvava preferencias | Adicionado toast/log | Funcional |
| Configuracoes | Abrir pasta de dados | Ausente | Nao havia botao | Implementado com `os.startfile` | Funcional |
| Configuracoes | Exportar dados | Ausente | Nao havia botao | Implementado via `BackupService.export_all_data` | Funcional |
| Configuracoes | Criar backup agora | Placeholder | Mostrava modal de futuro | Implementado backup em `backups/learnkit_data_backup.zip` | Funcional |
| Configuracoes | Limpar cache | Ausente | Nao havia acao | Implementado com confirmacao para `.pytest_cache` e `__pycache__` | Funcional |
| Configuracoes | Importar dados | Ausente | Merge seguro ainda nao existe | Botao mostra `future_action` com tooltip | Futuro/TODO explicito |
| Configuracoes | GitHub/Discussoes/Licenca/Reportar problema | Desabilitado | Botao desabilitado unico | Agora cada acao mostra futuro explicito | Futuro/TODO explicito |

## Logging

Arquivo: `app/logs/learnkit.log`

Eventos cobertos:

- app iniciado;
- pagina aberta;
- busca global;
- filtro de materia;
- comunidade aberta/fechada;
- materia/modulo/bloco criado ou excluido;
- arquivos selecionados/removidos;
- extracao iniciada/finalizada/falha;
- prompt gerado/copiado;
- Gemini aberto;
- resposta IA importada;
- flashcard marcado;
- pergunta respondida;
- configuracoes/backup/export/cache.

## Pendencias explicitas

| Item | Motivo | Status |
| --- | --- | --- |
| Renomear materia/modulo/bloco pela UI | Core tem base, mas a UI precisa de modal/editor dedicado | Futuro/TODO explicito |
| Importar dados com merge seguro | Risco de sobrescrever dados locais; precisa fluxo de preview/confirmacao | Futuro/TODO explicito |
| Links reais GitHub/Discussoes/Issues | Repositorio publico ainda nao configurado no app | Futuro/TODO explicito |
| Relatorio analitico completo | Pagina Progresso mostra agregado real, mas ainda nao exporta relatorio detalhado | Futuro/TODO explicito |
