# LearnKit 0.2.0

Esta release reúne as mudanças do ciclo de productização desde a `v0.1.2` até `e8f72576b71fc9ea659fbe2640e29c2c198dd24e`. O foco é transformar materiais importados em sessões de estudo mais úteis, apresentar resumos visuais de forma mais completa e tornar o fluxo IA/importação mais previsível e seguro.

## Destaques

- Revisão para Prova com seleção por matéria, módulo e bloco.
- Resumos visuais com presets, modo apresentação e exportação PNG/PDF.
- Validação estruturada de respostas de IA antes do salvamento.
- Workspace IA experimental para ChatGPT, Gemini e Claude.
- Correções de lifecycle, navegação pós-importação e exportação de tabelas longas.

## Revisão para Prova

A nova revisão permite selecionar uma hierarquia inteira ou blocos individuais e escolher se a sessão terá resumos, flashcards, perguntas e pegadinhas de prova. Conteúdos repetidos são deduplicados, mas cada item mantém suas origens para que o progresso e as ações continuem vinculados aos blocos corretos.

## Resumos visuais

O renderer compartilhado agora oferece os presets Auto, Prova, Lab, Neon, Retro e Minimalista, integrados ao prompt gerado para a IA. O modo de apresentação ganhou navegação por teclado, tela cheia com F11/Escape, Home/End, contador e progresso. Também é possível copiar a imagem do resumo ou salvar PNG e PDF multipágina; tabelas longas são expandidas antes da exportação e bitmaps excessivos são recusados com segurança.

## Importação e IA

O wizard passou a separar preparação, geração de prompt, validação e salvamento, com opções avançadas recolhidas. O pacote da IA recebe um relatório de erros fatais, avisos e informações, normaliza alternativas A–D e ignora itens incompletos. O texto extraído aceito permanece disponível até o salvamento.

O Workspace IA experimental abre ChatGPT, Gemini e Claude com cópia explícita do prompt. Quando o QtWebEngine está disponível, cada workspace usa uma sessão isolada e efêmera, sem downloads, popups ou permissões perigosas; quando não está, o navegador externo é usado.

## Estabilidade e correções

Foram corrigidos resultados stale e requisições duplicadas no worker de importação, o fechamento durante extração ativa, a renderização fora da viewport, a preservação de tabelas longas e a navegação/seleção do bloco após importação.

## Qualidade

- 178 testes automatizados passando em execução por grupos, incluindo os testes de UI e WebView isolados.
- `python -m compileall -q app tests` validado.
- A suíte monolítica apresentou comportamento nativo instável do QtWebEngine nesta máquina; os testes afetados passaram isoladamente e em conjunto, sem falha funcional Python.

## Limitações conhecidas

- O PDF visual ainda é rasterizado e sua paginação não é semântica.
- O Workspace IA continua experimental e não persiste sessões nem automatiza o envio aos providers.
- Alguns logins baseados em popup/permissão podem exigir o navegador externo.
- Revisões combinadas extremamente grandes podem aumentar o custo de memória e renderização da UI.
- A integração dos presets do resumo com o tema global ainda é parcial.
