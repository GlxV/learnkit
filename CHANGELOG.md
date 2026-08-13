# Changelog

Este arquivo registra as mudanças relevantes do LearnKit por release.

## [0.2.0] - 2026-08-13

Release de productização do fluxo de estudo, com revisão para prova, resumos visuais exportáveis, importação de pacotes de IA mais segura e melhorias de estabilidade no aplicativo desktop.

### Estudo e revisão

- Adicionada a Revisão para Prova, com seleção hierárquica por matéria, módulo e bloco e escolha dos tipos de conteúdo incluídos.
- Adicionada revisão combinada de resumos, flashcards, perguntas e pegadinhas de prova.
- Implementada deduplicação de itens equivalentes em revisões combinadas, mantendo as origens de cada ocorrência para registrar ações nos blocos corretos.
- Mantidos contexto de matéria/módulo/bloco e origem dos conteúdos apresentados na sessão combinada.
- Corrigida a seleção do bloco importado ao abrir Estudos depois de criar ou atualizar um bloco.

### Resumos visuais

- Adicionado um contrato declarativo para resumos visuais ricos, com suporte a blocos como hero, cards, callouts, tabelas, comparações, etapas, fluxos, gráficos, mapas conceituais, pegadinhas e preview de quiz.
- Centralizados os presets visuais Auto, Prova, Lab, Neon, Retro e Minimalista, com paleta, tipografia, espaçamento, estilo de cartões e orientação correspondente para o PromptBuilder.
- Melhorado o modo de apresentação com navegação por teclado, tela cheia, F11, Escape, Home, End, contador e barra de progresso.
- Adicionadas ações para copiar o resumo visual renderizado como imagem e exportá-lo para PNG ou PDF multipágina.
- Corrigida a exportação de resumos longos para expandir tabelas roláveis e preservar todas as linhas fora da viewport.
- Adicionada proteção contra alocações excessivas de bitmap durante exportações.

### Importação e IA

- Reestruturado o wizard de importação com o fluxo explícito “Preparar pacote de estudo” e opções avançadas recolhidas por padrão.
- Adicionada validação estruturada do pacote retornado pela IA, distinguindo erros fatais, avisos e informações antes do salvamento.
- Tornado o parser mais tolerante a formatos de coleção parcialmente malformados, sem converter valores semânticos não textuais em conteúdo enganoso.
- Normalizadas alternativas de perguntas para A–D e filtrados flashcards e perguntas incompletos antes da persistência.
- Adicionado o Workspace IA experimental para ChatGPT, Gemini e Claude, com cópia explícita do prompt e fallback para o navegador externo.
- Isoladas as sessões WebView por workspace, sem cookies persistentes, bloqueando downloads, popups, permissões e esquemas inseguros.
- Preservado o texto extraído aceito entre a preparação, a validação da resposta e o salvamento do pacote.

### Confiabilidade e correções

- Endurecido o lifecycle dos workers de extração: requisições duplicadas são evitadas, resultados stale são descartados e o fechamento do aplicativo é bloqueado durante processamento ativo.
- Corrigida a navegação após salvar um bloco importado, mantendo o contexto correto ao abrir a área de Estudos.
- Estabilizada a renderização de resumos visuais longos e o comportamento de widgets fora da tela usados na exportação.

### Qualidade

- A suíte atual contém 178 testes automatizados, cobrindo domínio, persistência, importação, UI, Workspace IA, exportação visual e atualizações.
- A validação de compilação com `python -m compileall -q app tests` foi mantida no fluxo da release.

### Limitações conhecidas

- O PDF é gerado a partir do bitmap renderizado e, portanto, permanece rasterizado; a paginação não é semântica.
- O Workspace IA é experimental: não injeta credenciais, não envia prompts automaticamente e não persiste sessões de provider.
- Popups de login e fluxos que dependem de permissões bloqueadas podem exigir o navegador externo.
- Revisões combinadas extremamente grandes podem aumentar o custo de memória e renderização da UI, pois a sessão é montada em memória.
- Os presets visuais controlam o renderer do resumo; sua integração com o tema global do aplicativo ainda é parcial.
