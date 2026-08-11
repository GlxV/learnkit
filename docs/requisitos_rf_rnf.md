# Requisitos do LearnKit

Este documento consolida os requisitos funcionais (RF) e requisitos não funcionais (RNF) do LearnKit, considerando o escopo atual do aplicativo desktop local.

## Requisitos Funcionais

### Organização de Estudos

- **RF01** - O sistema deve permitir criar uma matéria de estudo.
- **RF02** - O sistema deve permitir editar nome, descrição, cor e ícone de uma matéria.
- **RF03** - O sistema deve permitir excluir uma matéria, com confirmação do usuário.
- **RF04** - O sistema deve listar as matérias cadastradas.
- **RF05** - O sistema deve permitir selecionar uma matéria para visualizar seus módulos e blocos.
- **RF06** - O sistema deve permitir criar módulos dentro de uma matéria.
- **RF07** - O sistema deve permitir editar módulos cadastrados.
- **RF08** - O sistema deve permitir excluir módulos, com confirmação do usuário.
- **RF09** - O sistema deve listar os módulos de uma matéria.
- **RF10** - O sistema deve permitir criar blocos de estudo dentro de um módulo.
- **RF11** - O sistema deve permitir editar blocos de estudo.
- **RF12** - O sistema deve permitir excluir blocos de estudo, com confirmação do usuário.
- **RF13** - O sistema deve organizar os conteúdos na hierarquia Matéria -> Módulo -> Bloco de Estudo.
- **RF14** - O sistema deve evitar sobrescrever itens existentes quando houver nomes repetidos.
- **RF15** - O sistema deve gerar identificadores internos únicos para matérias, módulos, blocos, flashcards e perguntas.
- **RF16** - O sistema deve permitir navegar diretamente para uma matéria, módulo ou bloco a partir de cards, listas e resultados de busca.

### Importação e Extração de Conteúdo

- **RF17** - O sistema deve permitir selecionar arquivos locais para importação.
- **RF18** - O sistema deve aceitar arquivos PDF, PPTX, DOCX, TXT, Markdown e arquivos de texto/código suportados.
- **RF19** - O sistema deve permitir remover arquivos da lista antes da extração.
- **RF20** - O sistema deve extrair texto dos arquivos selecionados.
- **RF21** - O sistema deve permitir extrair texto antes de escolher matéria, módulo ou bloco de destino.
- **RF22** - O sistema deve exibir nome, extensão, tamanho e status de cada arquivo selecionado.
- **RF23** - O sistema deve extrair texto de PDFs preservando separação por páginas quando possível.
- **RF24** - O sistema deve extrair texto de apresentações PPTX preservando separação por slides quando possível.
- **RF25** - O sistema deve ler diretamente arquivos TXT, Markdown e arquivos de texto/código.
- **RF26** - O sistema deve tentar aplicar OCR local em imagens de PDFs, PPTX e DOCX quando houver backend disponível.
- **RF27** - O sistema deve informar quando um arquivo ou página aparentar ser escaneado ou ter pouco texto selecionável.
- **RF28** - O sistema deve continuar processando os demais arquivos mesmo que um arquivo falhe.
- **RF29** - O sistema deve exibir quantidade de caracteres, palavras, páginas/slides e avisos da extração.
- **RF30** - O sistema deve permitir visualizar um preview do texto extraído.
- **RF31** - O sistema deve permitir salvar/exportar o texto extraído.

### Geração de Prompt e Importação da Resposta da IA

- **RF32** - O sistema deve gerar prompt para uso manual em uma IA externa gratuita, como Gemini.
- **RF33** - O sistema deve deixar claro no prompt que a IA deve usar apenas o conteúdo fornecido.
- **RF34** - O sistema deve gerar prompt para resumo em Markdown simples.
- **RF35** - O sistema deve gerar prompt para resumo visual avançado em JSON estruturado.
- **RF36** - O sistema deve permitir configurar quantidade desejada de flashcards.
- **RF37** - O sistema deve permitir configurar quantidade desejada de perguntas.
- **RF38** - O sistema deve permitir configurar dificuldade e linguagem do prompt.
- **RF39** - O sistema deve permitir copiar o prompt para a área de transferência.
- **RF40** - O sistema deve permitir abrir uma IA externa no navegador sem integração por API.
- **RF41** - O sistema deve permitir colar/importar a resposta da IA em Markdown.
- **RF42** - O sistema deve validar a resposta da IA antes de salvar o bloco.
- **RF43** - O sistema deve identificar resumo em texto na resposta da IA.
- **RF44** - O sistema deve identificar resumo visual estruturado quando existir.
- **RF45** - O sistema deve identificar flashcards no formato pergunta e resposta.
- **RF46** - O sistema deve identificar perguntas de múltipla escolha com alternativas A, B, C e D.
- **RF47** - O sistema deve identificar gabarito e explicação das perguntas.
- **RF48** - O sistema deve exibir avisos quando partes da resposta da IA estiverem ausentes ou inválidas.
- **RF49** - O sistema deve impedir o salvamento final quando não houver nenhum conteúdo válido reconhecido.

### Salvamento do Pacote de Estudo

- **RF50** - O sistema deve permitir escolher ou criar a matéria de destino ao final da importação.
- **RF51** - O sistema deve permitir escolher ou criar o módulo de destino ao final da importação.
- **RF52** - O sistema deve permitir informar o nome do bloco de estudo ao final da importação.
- **RF53** - O sistema deve salvar o texto extraído associado ao bloco.
- **RF54** - O sistema deve salvar o prompt gerado associado ao bloco.
- **RF55** - O sistema deve salvar a resposta original da IA associada ao bloco.
- **RF56** - O sistema deve salvar o resumo em texto associado ao bloco.
- **RF57** - O sistema deve salvar o resumo visual associado ao bloco quando existir.
- **RF58** - O sistema deve salvar flashcards associados ao bloco.
- **RF59** - O sistema deve salvar perguntas associadas ao bloco.
- **RF60** - O sistema deve criar registro de progresso para o bloco salvo.
- **RF61** - O sistema deve permitir atualizar um bloco existente com novo conteúdo importado.

### Resumo

- **RF62** - O sistema deve permitir visualizar o resumo de um bloco.
- **RF63** - O sistema deve oferecer modo de resumo em texto simples.
- **RF64** - O sistema deve oferecer modo de resumo visual/apresentação quando houver JSON visual válido.
- **RF65** - O sistema deve permitir alternar entre os modos Texto e Visual.
- **RF66** - O sistema deve salvar o modo de resumo preferido por bloco.
- **RF67** - O sistema deve renderizar Markdown básico no modo texto.
- **RF68** - O sistema deve renderizar componentes visuais estruturados no modo visual.
- **RF69** - O sistema deve tratar JSON visual inválido sem quebrar o resumo em texto.
- **RF70** - O sistema deve permitir editar e salvar resumo em texto.
- **RF71** - O sistema deve permitir editar e salvar resumo visual.
- **RF72** - O sistema deve permitir copiar o conteúdo do resumo.
- **RF73** - O sistema deve oferecer modo apresentação para resumo visual.
- **RF74** - O sistema deve permitir navegar entre seções do modo apresentação.

### Flashcards

- **RF75** - O sistema deve listar flashcards reais por matéria, módulo e bloco.
- **RF76** - O sistema deve permitir selecionar um bloco com flashcards.
- **RF77** - O sistema deve exibir frente e verso do flashcard.
- **RF78** - O sistema deve permitir virar o flashcard.
- **RF79** - O sistema deve permitir navegar para o flashcard anterior.
- **RF80** - O sistema deve permitir navegar para o próximo flashcard.
- **RF81** - O sistema deve permitir pular um flashcard.
- **RF82** - O sistema deve permitir marcar um flashcard como Repetir.
- **RF83** - O sistema deve permitir marcar um flashcard como Difícil.
- **RF84** - O sistema deve permitir marcar um flashcard como Bom.
- **RF85** - O sistema deve permitir marcar um flashcard como Dominei.
- **RF86** - O sistema deve salvar o status escolhido para cada flashcard.
- **RF87** - O sistema deve atualizar contadores de revisão de flashcards.
- **RF88** - O sistema deve priorizar cards vencidos e novos na fila de revisão.
- **RF89** - O sistema não deve aplicar limite diário obrigatório de flashcards.

### Perguntas

- **RF90** - O sistema deve listar perguntas reais por matéria, módulo e bloco.
- **RF91** - O sistema deve permitir selecionar um bloco com perguntas.
- **RF92** - O sistema deve exibir perguntas de múltipla escolha.
- **RF93** - O sistema deve exibir quatro alternativas por pergunta quando disponíveis.
- **RF94** - O sistema deve permitir selecionar uma alternativa.
- **RF95** - O sistema deve permitir responder a pergunta selecionada.
- **RF96** - O sistema deve informar se a resposta está correta ou incorreta.
- **RF97** - O sistema deve destacar a alternativa correta.
- **RF98** - O sistema deve destacar a alternativa escolhida pelo usuário.
- **RF99** - O sistema deve exibir explicação da pergunta quando disponível.
- **RF100** - O sistema deve permitir navegar para a próxima questão.
- **RF101** - O sistema deve permitir voltar para a questão anterior.
- **RF102** - O sistema deve salvar a resposta escolhida pelo usuário.
- **RF103** - O sistema deve salvar se a resposta estava correta.
- **RF104** - O sistema deve manter histórico de tentativas de perguntas.
- **RF105** - O sistema deve permitir filtrar perguntas por todas, não respondidas, erradas e corretas.
- **RF106** - O sistema não deve contar a mesma pergunta repetidamente de forma incorreta.

### Progresso e Atividade

- **RF107** - O sistema deve calcular progresso por bloco.
- **RF108** - O sistema deve calcular progresso por módulo.
- **RF109** - O sistema deve calcular progresso por matéria.
- **RF110** - O sistema deve calcular progresso global.
- **RF111** - O sistema deve contabilizar flashcards totais, revisados, vencidos, novos e dominados.
- **RF112** - O sistema deve contabilizar perguntas totais, respondidas, corretas, erradas e em branco.
- **RF113** - O sistema deve registrar último acesso aos blocos.
- **RF114** - O sistema deve sugerir continuação de estudo com base em pendências reais.
- **RF115** - O sistema deve exibir atividade recente baseada em ações reais.
- **RF116** - O sistema deve atualizar o progresso após revisar flashcards.
- **RF117** - O sistema deve atualizar o progresso após responder perguntas.
- **RF118** - O sistema deve manter o progresso ao trocar de aba.
- **RF119** - O sistema deve manter o progresso ao fechar e abrir o aplicativo.

### Navegação, Busca e Interface

- **RF120** - O sistema deve possuir navegação lateral entre Início, Matérias, Estudos, Flashcards, Perguntas, Progresso, Importação/IA, Configurações e Banco de Dados.
- **RF121** - O sistema deve destacar a página ativa na navegação.
- **RF122** - O sistema deve permitir recolher e expandir a sidebar.
- **RF123** - O sistema deve permitir navegar para flashcards de um bloco a partir de outras telas.
- **RF124** - O sistema deve permitir navegar para perguntas de um bloco a partir de outras telas.
- **RF125** - O sistema deve permitir navegar para o resumo de um bloco a partir de outras telas.
- **RF126** - O sistema deve oferecer busca global.
- **RF127** - A busca deve consultar matérias, módulos, blocos, resumos, flashcards e perguntas.
- **RF128** - A busca deve exibir sugestões com o tipo do resultado.
- **RF129** - O sistema deve navegar para o item correto ao clicar em uma sugestão.
- **RF130** - Os dropdowns de matéria, módulo e bloco devem atualizar os dados exibidos.
- **RF131** - Botões importantes devem executar ação real ou estar claramente desabilitados.
- **RF132** - O sistema deve exibir feedback visual para ações de sucesso, erro, aviso e informação.

### Configurações e Banco de Dados

- **RF133** - O sistema deve permitir alterar tema visual.
- **RF134** - O sistema deve permitir alterar cor de destaque.
- **RF135** - O sistema deve permitir alterar densidade visual quando disponível.
- **RF136** - O sistema deve salvar preferências locais do usuário.
- **RF137** - O sistema deve permitir abrir a pasta de dados.
- **RF138** - O sistema deve permitir criar backup dos dados.
- **RF139** - O sistema deve permitir importar backup quando suportado.
- **RF140** - O sistema deve permitir limpar cache com confirmação.
- **RF141** - O sistema deve exibir tela de demonstração do banco de dados.
- **RF142** - A tela de banco de dados deve mostrar caminho do arquivo SQLite.
- **RF143** - A tela de banco de dados deve mostrar status da conexão.
- **RF144** - A tela de banco de dados deve mostrar contadores reais de matérias, módulos, blocos, flashcards, perguntas e progresso.
- **RF145** - A tela de banco de dados deve permitir atualizar os dados exibidos.
- **RF146** - A tela de banco de dados deve listar registros recentes.

### Inicialização e Instalação

- **RF147** - O sistema deve poder ser iniciado por comando Python.
- **RF148** - O sistema deve poder ser iniciado por arquivo `.bat` no Windows.
- **RF149** - O sistema deve fornecer instalador Windows para preparar dependências.
- **RF150** - O instalador deve criar ambiente virtual local.
- **RF151** - O instalador deve instalar dependências Python.
- **RF152** - O instalador deve tentar preparar OCR local.

## Requisitos Não Funcionais

### Plataforma e Arquitetura

- **RNF01** - O aplicativo deve ser desktop.
- **RNF02** - O aplicativo deve ser desenvolvido em Python 3.11 ou superior.
- **RNF03** - A interface gráfica deve usar PySide6.
- **RNF04** - A lógica principal deve ficar separada da interface.
- **RNF05** - A aplicação deve possuir separação clara entre UI, serviços, modelos, banco de dados, importação, parser, prompt e extração.
- **RNF06** - A UI não deve acessar SQL diretamente.
- **RNF07** - A arquitetura deve permitir evolução futura sem reescrever o core.
- **RNF08** - Dados mockados só devem existir como seed opcional ou fallback de desenvolvimento.

### Persistência e Dados

- **RNF09** - O sistema deve persistir dados localmente em SQLite.
- **RNF10** - O banco deve ficar em `data/learnkit.db`.
- **RNF11** - O sistema deve manter dados após fechar e abrir o aplicativo.
- **RNF12** - O sistema deve evitar registros órfãos ao excluir matérias, módulos ou blocos.
- **RNF13** - Operações destrutivas devem exigir confirmação.
- **RNF14** - O sistema deve preservar integridade dos relacionamentos Matéria -> Módulo -> Bloco.
- **RNF15** - O sistema deve evitar sobrescrita acidental de dados.
- **RNF16** - O sistema deve usar codificação UTF-8 para textos, prompts, respostas e arquivos exportados.

### Privacidade, Segurança e Licenciamento

- **RNF17** - O aplicativo deve funcionar sem cloud obrigatória.
- **RNF18** - O aplicativo não deve enviar materiais do usuário automaticamente para serviços externos.
- **RNF19** - O aplicativo não deve depender de API paga de IA.
- **RNF20** - O fluxo com IA deve ser manual via prompt copiado pelo usuário.
- **RNF21** - O aplicativo não deve possuir paywall, plano premium ou assinatura.
- **RNF22** - O aplicativo deve ser gratuito e open source.
- **RNF23** - O sistema não deve executar HTML bruto vindo da IA.
- **RNF24** - O resumo visual deve ser renderizado a partir de JSON estruturado seguro.
- **RNF25** - Logs não devem armazenar conteúdo integral de PDFs, prompts ou respostas da IA.

### Usabilidade e Interface

- **RNF26** - A interface deve seguir tema escuro.
- **RNF27** - A interface deve manter consistência visual entre páginas, cards, dropdowns, modais e botões.
- **RNF28** - A interface deve evitar aparência de produto SaaS pago.
- **RNF29** - A interface deve usar feedback visual para cliques, carregamento, sucesso, erro e avisos.
- **RNF30** - A aplicação deve apresentar estados vazios quando não houver dados reais.
- **RNF31** - A aplicação não deve mostrar números falsos como fonte principal.
- **RNF32** - A interface deve ser legível em telas de notebook.
- **RNF33** - Modais grandes devem ser roláveis em telas menores.
- **RNF34** - Botões clicáveis devem ter cursor, hover, pressed, disabled e estados visuais claros.
- **RNF35** - Dropdowns devem seguir o tema dark do aplicativo.
- **RNF36** - Textos da interface devem estar em português claro e com acentuação correta.
- **RNF37** - O modo apresentação deve oferecer boa leitura em notebook e projetor.

### Desempenho e Robustez

- **RNF38** - Extrações demoradas não devem travar a interface.
- **RNF39** - O sistema deve usar processamento em background para extração de arquivos.
- **RNF40** - O sistema deve continuar funcionando quando OCR local não estiver disponível.
- **RNF41** - O sistema deve exibir erros amigáveis para arquivos inválidos ou não suportados.
- **RNF42** - Falha em um arquivo importado não deve impedir o processamento dos demais.
- **RNF43** - A busca deve responder de forma aceitável para bases locais pequenas e médias.
- **RNF44** - A aplicação deve inicializar mesmo com banco vazio.
- **RNF45** - O sistema deve degradar funcionalidades opcionais de forma controlada.

### Manutenibilidade e Qualidade

- **RNF46** - O código deve ser modular e organizado.
- **RNF47** - O código deve usar nomes claros para classes, funções e arquivos.
- **RNF48** - O código deve usar type hints quando fizer sentido.
- **RNF49** - O core deve ser testável sem depender da UI.
- **RNF50** - O projeto deve possuir testes automatizados para funcionalidades centrais.
- **RNF51** - O sistema deve possuir documentação de instalação, uso e limitações.
- **RNF52** - O projeto deve possuir checklist manual para fluxos de UI.
- **RNF53** - O sistema deve registrar logs de ações importantes para debug.
- **RNF54** - O instalador Windows deve automatizar preparação do ambiente sempre que possível.
- **RNF55** - Dependências externas opcionais, como OCR, devem ser documentadas.

### Compatibilidade e Evolução

- **RNF56** - O aplicativo deve priorizar Windows como ambiente principal de execução.
- **RNF57** - O projeto deve continuar executável por linha de comando Python.
- **RNF58** - O projeto deve continuar executável pelo atalho `.bat` no Windows.
- **RNF59** - O OCR deve ter suporte a backend local do Windows e fallback Tesseract quando disponível.
- **RNF60** - O sistema deve permitir evolução futura para revisão espaçada mais avançada.
- **RNF61** - O sistema deve permitir evolução futura para novos tipos de resumo visual.
- **RNF62** - O sistema deve permitir evolução futura para novos formatos de arquivo.
- **RNF63** - O sistema deve permitir evolução futura da interface sem alterar o core principal.
- **RNF64** - O banco deve permitir demonstrar persistência em apresentação acadêmica.

