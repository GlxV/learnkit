from __future__ import annotations

SUBJECT_ICONS = [
    "calculator", "ruler", "compass", "function", "chart", "stats", "sigma", "geometry", "triangle", "axis",
    "atom", "flask", "molecule", "lab", "microscope", "dna", "cell", "leaf", "ecology", "anatomy",
    "globe", "map", "landmark", "timeline", "scroll", "scale", "law", "politics", "society", "philosophy",
    "brain", "psychology", "book", "bookmark", "pen", "quote", "grammar", "language", "dictionary", "paragraph",
    "palette", "brush", "music", "camera", "film", "image", "design", "layers", "spark", "star",
    "database", "sql", "terminal", "code", "web", "api", "git", "network", "server", "cloud",
    "shield", "lock", "chip", "circuit", "robot", "gamepad", "mobile", "bug", "wrench", "gear",
    "tree", "list", "stack", "queue", "hash", "graph", "binary", "ai", "model", "data",
    "briefcase", "coins", "finance", "chart-up", "marketing", "target", "project", "calendar", "checklist", "clock",
    "heart", "stethoscope", "pill", "tooth", "nursing", "pharmacy", "engineering", "mechanics", "bolt", "building",
]


SUBJECT_ICON_LABELS = {
    "calculator": "Matematica",
    "ruler": "Regua",
    "compass": "Compasso",
    "function": "Funcao",
    "chart": "Grafico",
    "stats": "Estatistica",
    "sigma": "Somatorio",
    "geometry": "Geometria",
    "triangle": "Triangulo",
    "axis": "Eixos",
    "atom": "Fisica",
    "flask": "Quimica",
    "molecule": "Molecula",
    "lab": "Laboratorio",
    "microscope": "Microscopio",
    "dna": "DNA",
    "cell": "Celula",
    "leaf": "Biologia",
    "ecology": "Ecologia",
    "anatomy": "Anatomia",
    "globe": "Geografia",
    "map": "Mapa",
    "landmark": "Historia",
    "timeline": "Linha do tempo",
    "scroll": "Documento historico",
    "scale": "Direito",
    "law": "Lei",
    "politics": "Politica",
    "society": "Sociedade",
    "philosophy": "Filosofia",
    "brain": "Mente",
    "psychology": "Psicologia",
    "book": "Livro",
    "bookmark": "Leitura",
    "pen": "Escrita",
    "quote": "Literatura",
    "grammar": "Gramatica",
    "language": "Idiomas",
    "dictionary": "Dicionario",
    "paragraph": "Texto",
    "palette": "Arte",
    "brush": "Desenho",
    "music": "Musica",
    "camera": "Fotografia",
    "film": "Cinema",
    "image": "Imagem",
    "design": "Design",
    "layers": "Camadas",
    "spark": "Criatividade",
    "star": "Favorito",
    "database": "Banco de dados",
    "sql": "SQL",
    "terminal": "Terminal",
    "code": "Codigo",
    "web": "Web",
    "api": "API",
    "git": "Git",
    "network": "Redes",
    "server": "Servidor",
    "cloud": "Cloud",
    "shield": "Seguranca",
    "lock": "Privacidade",
    "chip": "Hardware",
    "circuit": "Circuitos",
    "robot": "Robotica",
    "gamepad": "Jogos",
    "mobile": "Mobile",
    "bug": "Debug",
    "wrench": "Manutencao",
    "gear": "Sistemas",
    "tree": "Arvore",
    "list": "Lista",
    "stack": "Pilha",
    "queue": "Fila",
    "hash": "Hash",
    "graph": "Grafo",
    "binary": "Binario",
    "ai": "IA",
    "model": "Modelo",
    "data": "Dados",
    "briefcase": "Negocios",
    "coins": "Economia",
    "finance": "Financas",
    "chart-up": "Crescimento",
    "marketing": "Marketing",
    "target": "Meta",
    "project": "Projeto",
    "calendar": "Agenda",
    "checklist": "Checklist",
    "clock": "Tempo",
    "heart": "Saude",
    "stethoscope": "Medicina",
    "pill": "Farmacia",
    "tooth": "Odonto",
    "nursing": "Enfermagem",
    "pharmacy": "Farmacologia",
    "engineering": "Engenharia",
    "mechanics": "Mecanica",
    "bolt": "Eletrica",
    "building": "Arquitetura",
}


def subject_icon_for_name(name: str, current: str | None = None) -> str:
    if current in SUBJECT_ICONS:
        return str(current)
    normalized = name.casefold()
    if "mat" in normalized or "calculo" in normalized or "cálculo" in normalized:
        return "calculator"
    if "fis" in normalized or "fís" in normalized:
        return "atom"
    if "quim" in normalized or "quím" in normalized:
        return "flask"
    if "bio" in normalized:
        return "dna"
    if "hist" in normalized:
        return "landmark"
    if "geo" in normalized:
        return "globe"
    if "port" in normalized or "lingua" in normalized or "língua" in normalized:
        return "book"
    if "banco" in normalized or "dados" in normalized or "sql" in normalized:
        return "database"
    if "estrutura" in normalized or "algorit" in normalized:
        return "tree"
    if "program" in normalized or "codigo" in normalized or "código" in normalized:
        return "code"
    return "book"


MODULE_PRESETS = [
    "Geral",
    "1o Bimestre",
    "2o Bimestre",
    "3o Bimestre",
    "4o Bimestre",
    "1o Trimestre",
    "2o Trimestre",
    "3o Trimestre",
    "1o Semestre",
    "2o Semestre",
    "Prova 1",
    "Prova 2",
    "Prova 3",
    "Prova 4",
    "Unidade 1",
    "Unidade 2",
    "Unidade 3",
    "Unidade 4",
    "Unidade 5",
    "Unidade 6",
    "Revisao Final",
    "Recuperacao",
    "Extras",
    "Trabalhos",
    "Simulados",
    "Laboratorio",
]
