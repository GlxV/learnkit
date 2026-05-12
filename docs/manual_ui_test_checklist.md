# Checklist Manual de Teste da UI

Use este roteiro para validar a UI depois de alteracoes em botoes, navegacao ou storage.

## Preparacao

1. Abrir o app com `python -m app.main`.
2. Confirmar que a sidebar aparece.
3. Confirmar que nenhuma mensagem de erro aparece ao iniciar.

## Fluxo principal

1. Ir para `Materias`.
2. Clicar em `Nova materia personalizada`.
3. Criar uma materia chamada `Teste UI`.
4. Confirmar que a materia aparece na lista sem reiniciar o app.
5. Clicar em `Criar modulo`.
6. Criar um modulo chamado `Modulo 1`.
7. Confirmar que o modulo aparece na materia.
8. Ir para `Importacao/IA`.
9. Confirmar que nao e obrigatorio escolher materia/modulo/bloco no inicio.
10. Selecionar ou arrastar um arquivo `.txt` simples.
11. Confirmar que a lista mostra card de arquivo, nao caminho gigante.
12. Clicar em `Limpar lista` e confirmar que ele sai da lista.
13. Selecionar o `.txt` novamente.
14. Clicar em `Extrair texto`.
15. Confirmar loading, toast e contagem de caracteres/palavras.
16. Clicar em `Opcoes avancadas` e abrir os dropdowns de dificuldade/linguagem.
17. Confirmar que os dropdowns estao dark, sem popup default branco.
18. Clicar em `Gerar prompt`.
19. Confirmar que o prompt aparece.
20. Clicar em `Copiar prompt`.
21. Confirmar feedback visual de copia.
22. Colar em `Resposta da IA` o conteudo de `tests/fixtures/sample_ai_response.md`.
23. Clicar em `Validar resposta`.
24. Confirmar que aparecem resumo, 3 flashcards e 3 perguntas.
25. No passo `Salvar no LearnKit`, escolher `Teste UI`, `Modulo 1` e digitar `Bloco TXT`.
26. Clicar em `Salvar bloco de estudo`.
27. Confirmar toast e mensagem de bloco criado.
28. Clicar em `Abrir resumo`.
29. Confirmar que abre a pagina Estudos no bloco.
30. Voltar para `Importacao/IA` se necessario e clicar em `Estudar flashcards`.
31. Virar o card.
32. Clicar em `Dominei`.
33. Confirmar feedback visual.
34. Ir para `Perguntas`.
35. Selecionar uma alternativa.
36. Clicar em `Responder`.
37. Confirmar acerto/erro e explicacao.
38. Ir para `Progresso`.
39. Confirmar que progresso, cards revisados e perguntas respondidas mudaram.
40. Fechar e abrir o app novamente.
41. Confirmar que materia, modulo, bloco, cards, perguntas e progresso persistiram.

## Auditoria de botoes principais

1. Sidebar: clicar em todas as paginas e confirmar estado ativo.
2. Sidebar: abrir/fechar `Comunidade`.
3. Sidebar Comunidade: clicar nos itens e confirmar mensagem de recurso futuro.
4. Topbar: buscar por nome de materia, modulo, bloco, pergunta ou flashcard e abrir resultado.
5. Topbar: trocar materia no dropdown e confirmar filtro em Home/Progresso.
6. Home: testar `Continuar`, `Flashcards`, `Ver todas`, `Ver todos`, `Abrir`.
7. Materias: testar selecionar materia, abrir modulo, excluir modulo/bloco com confirmacao.
8. Estudos: testar dropdowns, resumo, flashcards, perguntas e blocos da lista.
9. Flashcards: testar dropdowns, lista lateral, virar card, anterior, proximo, dificil, dominei e pular.
10. Perguntas: testar dropdowns, lista lateral, selecionar alternativa, responder, anterior e proxima.
11. Importacao/IA: testar selecionar arquivos sem materia, limpar lista, extrair, gerar, copiar, abrir Gemini, validar resposta, escolher destino no final e salvar bloco.
12. Configuracoes: salvar, abrir pasta de dados, exportar dados, criar backup, limpar cache e itens futuros.

## Testes especificos de polish

1. Abrir todos os dropdowns de Topbar, Estudos, Flashcards, Perguntas, Importacao/IA e Configuracoes.
2. Confirmar que o popup do dropdown esta escuro e integrado ao tema.
3. Clicar nos botoes principais e observar hover/pressed/disabled/loading.
4. Confirmar que `Extrair texto` mostra loading e nao bloqueia a janela.
5. Confirmar que os toasts aparecem no canto inferior direito e somem sozinhos.

## Resultado esperado

- Nenhum botao importante fica sem feedback.
- Acoes futuras mostram mensagem clara.
- Acoes destrutivas pedem confirmacao.
- Mudancas de dados persistem em `data/`.
- Logs aparecem em `app/logs/learnkit.log`.
