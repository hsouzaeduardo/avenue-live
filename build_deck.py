"""
Gera o deck da palestra "Por onde começar criando agentes de IA com o
Microsoft Agent Framework" em PowerPoint (.pptx).

Uso:
    pip install python-pptx
    python build_deck.py            # gera maf-workshop.pptx ao lado do script

Tudo é parametrizado no topo (paleta, fontes, tamanhos) e cada slide é uma
chamada de função, então dá para reordenar, remover ou duplicar à vontade.
As notas do apresentador (fala de cada slide) vão em `notes=`.
"""

from __future__ import annotations

import re
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.util import Inches, Pt

OUT = Path(__file__).with_name("maf-workshop.pptx")

# ---------------------------------------------------------------- paleta
INK = RGBColor(0x16, 0x20, 0x2E)       # texto / fundo escuro
MUTED = RGBColor(0x5E, 0x6B, 0x7C)
LINE = RGBColor(0xD6, 0xDD, 0xE7)
PANEL = RGBColor(0xEE, 0xF2, 0xF7)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BLUE = RGBColor(0x24, 0x56, 0xCF)      # agente / orquestração
BLUE_SOFT = RGBColor(0xE3, 0xEA, 0xFB)
AMBER = RGBColor(0xB8, 0x65, 0x0A)     # tool / dado
AMBER_SOFT = RGBColor(0xFB, 0xEF, 0xD9)
GREEN = RGBColor(0x1C, 0x8A, 0x68)     # resultado
GREEN_SOFT = RGBColor(0xDC, 0xF3, 0xEA)
# código (tema escuro)
CODE_BG = RGBColor(0x0F, 0x17, 0x2A)
CODE_FG = RGBColor(0xE2, 0xE8, 0xF0)
CODE_KW = RGBColor(0x93, 0xC5, 0xFD)
CODE_STR = RGBColor(0xFC, 0xD9, 0x8B)
CODE_CM = RGBColor(0x7C, 0x8B, 0xA3)
CODE_FN = RGBColor(0xA5, 0xF3, 0xD0)
CODE_NUM = RGBColor(0xF9, 0xA8, 0xD4)
DARK_SUB = RGBColor(0xA9, 0xB6, 0xC8)  # texto secundário em fundo escuro

FONT = "Calibri"
MONO = "Consolas"

W, H = Inches(13.333), Inches(7.5)
MARGIN = Inches(0.6)

prs = Presentation()
prs.slide_width, prs.slide_height = W, H
BLANK = prs.slide_layouts[6]


# ---------------------------------------------------------------- helpers
def _fill(shape, color):
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()


def rect(slide, x, y, w, h, color, shape=MSO_SHAPE.RECTANGLE, radius=None):
    s = slide.shapes.add_shape(shape, x, y, w, h)
    _fill(s, color)
    s.shadow.inherit = False
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    return s


def text(slide, x, y, w, h, content, size=16, bold=False, color=INK, font=FONT,
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, italic=False, line_spacing=1.1):
    """content: str (parágrafos separados por \\n) ou lista de (texto, dict de opções)."""
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0.03)
    tf.vertical_anchor = anchor
    paras = content.split("\n") if isinstance(content, str) else content
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = align
        para.line_spacing = line_spacing
        if isinstance(p, tuple):
            ptxt, opts = p
        else:
            ptxt, opts = p, {}
        r = para.add_run()
        r.text = ptxt
        f = r.font
        f.name = opts.get("font", font)
        f.size = Pt(opts.get("size", size))
        f.bold = opts.get("bold", bold)
        f.italic = opts.get("italic", italic)
        f.color.rgb = opts.get("color", color)
        if opts.get("space_after") is not None:
            para.space_after = Pt(opts["space_after"])
    return tb


def bullets(slide, x, y, w, h, items, size=16, color=INK, gap=8, marker="•", marker_color=BLUE):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.05)
    for i, item in enumerate(items):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.space_after = Pt(gap)
        para.line_spacing = 1.1
        m = para.add_run()
        m.text = f"{marker}  "
        m.font.name, m.font.size, m.font.bold = FONT, Pt(size), True
        m.font.color.rgb = marker_color
        if isinstance(item, tuple):          # (negrito, resto)
            b = para.add_run()
            b.text = item[0]
            b.font.name, b.font.size, b.font.bold = FONT, Pt(size), True
            b.font.color.rgb = color
            r = para.add_run()
            r.text = item[1]
        else:
            r = para.add_run()
            r.text = item
        r.font.name, r.font.size = FONT, Pt(size)
        r.font.color.rgb = color
    return tb


def chip(slide, x, y, label, fill, fg, w=None, size=11, mono=False):
    w = w or Inches(0.12 * len(label) + 0.35)
    s = rect(slide, x, y, w, Inches(0.34), fill, MSO_SHAPE.ROUNDED_RECTANGLE, 0.5)
    tf = s.text_frame
    tf.margin_left = tf.margin_right = Inches(0.08)
    tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    r.font.name = MONO if mono else FONT
    r.font.size, r.font.bold = Pt(size), True
    r.font.color.rgb = fg
    return s


def arrow(slide, x, y, w, color=MUTED, h=Inches(0.28)):
    s = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, x, y, w, h)
    _fill(s, color)
    s.shadow.inherit = False
    return s


def notes(slide, txt):
    slide.notes_slide.notes_text_frame.text = txt.strip()


def footer(slide, dark=False, n=None):
    c = DARK_SUB if dark else MUTED
    text(slide, MARGIN, H - Inches(0.5), Inches(8), Inches(0.3),
         "Microsoft Agent Framework · por onde começar", size=10, color=c)
    if n is not None:
        text(slide, W - MARGIN - Inches(1), H - Inches(0.5), Inches(1), Inches(0.3),
             str(n), size=10, color=c, align=PP_ALIGN.RIGHT)


def eyebrow(slide, txt, dark=False, y=Inches(0.45)):
    text(slide, MARGIN, y, Inches(8), Inches(0.3), txt.upper(), size=11, bold=True,
         color=(DARK_SUB if dark else BLUE))


def title(slide, txt, dark=False, y=Inches(0.75), size=32):
    text(slide, MARGIN, y, W - 2 * MARGIN, Inches(0.8), txt, size=size, bold=True,
         color=(WHITE if dark else INK), anchor=MSO_ANCHOR.MIDDLE)


# ---------------------------------------------------------------- código
_PY_KW = r"\b(from|import|def|async|await|class|return|with|as|if|elif|else|for|in|not|and|or|None|True|False|lambda|try|except|raise|yield|pass)\b"
_TOKEN = re.compile(
    r"(?P<cm>#.*$)|(?P<str>[fFrRbB]?(\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'))|"
    r"(?P<kw>" + _PY_KW + r")|(?P<num>\b\d+(\.\d+)?\b)|(?P<fn>\b[A-Za-z_]\w*(?=\())"
)
_COLORS = {"cm": CODE_CM, "str": CODE_STR, "kw": CODE_KW, "num": CODE_NUM, "fn": CODE_FN}


def _runs(para, line, size, lang):
    def add(t, color):
        if not t:
            return
        r = para.add_run()
        r.text = t
        r.font.name, r.font.size = MONO, Pt(size)
        r.font.color.rgb = color

    if lang != "python":
        if line.lstrip().startswith("#"):
            add(line, CODE_CM)
        else:
            add(line, CODE_FG)
        return
    pos = 0
    for m in _TOKEN.finditer(line):
        add(line[pos:m.start()], CODE_FG)
        kind = m.lastgroup
        add(m.group(0), _COLORS.get(kind, CODE_FG))
        pos = m.end()
    add(line[pos:], CODE_FG)


def code_block(slide, x, y, w, h, code, size=12, lang="python", label=None):
    box = rect(slide, x, y, w, h, CODE_BG, MSO_SHAPE.ROUNDED_RECTANGLE, 0.04)
    if label:  # nome do arquivo logo abaixo da caixa, à direita (fora do código)
        text(slide, x + w - Inches(5), y + h + Inches(0.02), Inches(5), Inches(0.25), label,
             size=9, color=MUTED, font=MONO, align=PP_ALIGN.RIGHT)
    tb = slide.shapes.add_textbox(x + Inches(0.1), y + Inches(0.12), w - Inches(0.2), h - Inches(0.24))
    tf = tb.text_frame
    tf.word_wrap = True            # as linhas já são checadas abaixo; wrap evita o "auto-grow" centralizado
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0.05)
    lines = code.strip("\n").split("\n")
    # aviso de linha que não cabe (Consolas ≈ 0.55 em por caractere)
    capacity = int((w - Inches(0.3)) / (Pt(size) * 0.55))
    rows = int((h - Inches(0.34)) / (Pt(size) * 1.15 * 1.2))
    for ln in lines:
        if len(ln) > capacity:
            print(f"  ⚠ linha com {len(ln)} chars (cabem {capacity}): {ln.strip()[:60]}…")
    if len(lines) > rows:
        print(f"  ⚠ bloco com {len(lines)} linhas (cabem ~{rows})")
    for i, line in enumerate(lines):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.line_spacing = 1.15
        _runs(para, line, size, lang)
    return box


# ---------------------------------------------------------------- tipos de slide
def slide_dark():
    s = prs.slides.add_slide(BLANK)
    rect(s, 0, 0, W, H, INK)
    return s


def slide_light():
    s = prs.slides.add_slide(BLANK)
    rect(s, 0, 0, W, H, WHITE)
    return s


def divider(num, titulo, sub, fala, n):
    s = slide_dark()
    chip(s, MARGIN, Inches(2.3), f"ETAPA {num}", BLUE, WHITE, w=Inches(1.3), size=12)
    text(s, MARGIN, Inches(2.8), Inches(11), Inches(1.4), titulo, size=44, bold=True, color=WHITE,
         anchor=MSO_ANCHOR.MIDDLE)
    text(s, MARGIN, Inches(4.2), Inches(10), Inches(1.2), sub, size=20, color=DARK_SUB)
    footer(s, dark=True, n=n)
    notes(s, fala)
    return s


def code_slide(num, titulo, code, fala, n, side=None, lang="python", size=12, label=None):
    """Slide de código: código à esquerda; se `side` (lista), pontos de fala à direita."""
    s = slide_light()
    eyebrow(s, f"Etapa {num}")
    title(s, titulo)
    y = Inches(1.65)
    h = Inches(5.15)
    if side:
        cw = Inches(8.1)
        code_block(s, MARGIN, y, cw, h, code, size=size, lang=lang, label=label)
        bx = MARGIN + cw + Inches(0.35)
        bullets(s, bx, y + Inches(0.05), W - bx - MARGIN, h, side, size=15, gap=10)
    else:
        code_block(s, MARGIN, y, W - 2 * MARGIN, h, code, size=size, lang=lang, label=label)
    footer(s, n=n)
    notes(s, fala)
    return s


# ================================================================ SLIDES
n = 0

# 1 · Capa -------------------------------------------------------------------
n += 1
s = slide_dark()
text(s, MARGIN, Inches(1.2), Inches(9), Inches(0.4), "MICROSOFT AGENT FRAMEWORK", size=13, bold=True, color=DARK_SUB)
text(s, MARGIN, Inches(1.7), Inches(11.5), Inches(2.2),
     "Por onde começar\ncriando agentes de IA", size=52, bold=True, color=WHITE, line_spacing=1.0)
text(s, MARGIN, Inches(4.1), Inches(10.5), Inches(1.2),
     "Flexibilidade, Foundry, um comparativo honesto com o Google ADK\ne o que separa demo de produção: observabilidade.",
     size=20, color=DARK_SUB)
# trilha de 6 etapas
labels = ["Hello agent", "Tools", "Flexibilidade", "Foundry", "Workflows", "Observabilidade"]
x0, yy = MARGIN, Inches(5.7)
for i, lab in enumerate(labels):
    cx = x0 + Inches(2.05) * i
    c = rect(s, cx, yy, Inches(0.42), Inches(0.42), BLUE, MSO_SHAPE.OVAL)
    tf = c.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = str(i + 1); r.font.size = Pt(13); r.font.bold = True; r.font.color.rgb = WHITE; r.font.name = FONT
    text(s, cx + Inches(0.5), yy + Inches(0.02), Inches(1.55), Inches(0.4), lab, size=13, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
footer(s, dark=True)
notes(s, """
Abertura. Pergunta para a sala: "Quem aqui já escreveu na mão um loop de tool-calling com while True e um parser de JSON?"
Metade levanta a mão. Essa é a dor que o framework resolve. O formato de hoje é bate-papo: slide, trecho de código, demo, slide.
""")

# 2 · Agenda -----------------------------------------------------------------
n += 1
s = slide_light()
eyebrow(s, "Roteiro")
title(s, "Seis etapas, do primeiro agente ao monitor")
agenda = [
    ("1", "Por que mais um framework?", "SK + AutoGen viraram um só. Hello agent em 10 linhas."),
    ("2", "Anatomia de um agente", "Instruções + tools. Uma função Python vira ferramenta."),
    ("3", "Flexibilidade e comparativo", "O agente não se casa com o modelo. MAF × ADK sem superlativos."),
    ("4", "Entrando no Foundry", "Demo: catálogo, deploy de modelo, trocar o provider sem tocar no código."),
    ("5", "De agente para sistema", "Workflows: sequencial, concorrente, handoff. Cenário ViaCEP + Postgres."),
    ("6", "Observabilidade", "OpenTelemetry → Foundry Traces / Monitor. O que separa demo de produção."),
]
colw, gap = Inches(3.9), Inches(0.25)
for i, (num, t, d) in enumerate(agenda):
    col, row = i % 3, i // 3
    x = MARGIN + (colw + gap) * col
    y = Inches(1.8) + Inches(2.35) * row
    card = rect(s, x, y, colw, Inches(2.05), PANEL, MSO_SHAPE.ROUNDED_RECTANGLE, 0.06)
    c = rect(s, x + Inches(0.25), y + Inches(0.25), Inches(0.5), Inches(0.5), BLUE, MSO_SHAPE.OVAL)
    tf = c.text_frame; tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = num; r.font.size = Pt(16); r.font.bold = True; r.font.color.rgb = WHITE; r.font.name = FONT
    text(s, x + Inches(0.9), y + Inches(0.22), colw - Inches(1.1), Inches(0.6), t, size=18, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + Inches(0.25), y + Inches(0.95), colw - Inches(0.5), Inches(1.0), d, size=14, color=MUTED)
footer(s, n=n)
notes(s, """
Mostre o arco: começa na dor, passa pelo "olha como é simples", sobe para flexibilidade e comparação, entra no Foundry ao vivo,
escala para multiagente e fecha com observabilidade, que é onde o público técnico decide se leva a sério.
""")

# ====================================================== ETAPA 1
n += 1
divider(1, "Por que mais um framework?", "Semantic Kernel (enterprise, .NET) + AutoGen (multiagente, pesquisa) viraram um só.\nMIT, Python e .NET. Um sucessor, não um terceiro concorrente.",
        """
Conte a origem em uma frase: SK + AutoGen → Microsoft Agent Framework. A mensagem é "é o sucessor dos dois, não um terceiro".
Quem já usa SK ou AutoGen tem guia de migração; quem nunca usou começa pelo próximo slide.
""", n)

n += 1
code_slide(1, "O menor agente possível", '''
pip install agent-framework azure-identity
''' + "\n" + '''
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

agent = Agent(
    client=FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model="gpt-4o-mini",
        credential=AzureCliCredential(),
    ),
    name="HelloAgent",
    instructions="Você é um assistente direto. Respostas curtas.",
)

result = await agent.run("O que é um agente de IA em uma frase?")
print(result)
''', """
Cliente, modelo, instruções, run. Não tem thread, não tem run_id, não tem polling. Isso é o framework fazendo o trabalho chato.
Repare que a primeira linha é o pip; o resto cabe na tela. Esse é o slide que a pessoa fotografa.
""", n, side=[
    ("Cliente", " – de onde vem o modelo (Foundry, Azure OpenAI, OpenAI, Ollama…)"),
    ("Instruções", " – o system prompt"),
    ("run()", " – uma chamada, resposta completa; stream=True para streaming"),
    "Sem thread, sem run_id, sem polling",
    "Não carrega .env sozinho: load_dotenv() ou variáveis no shell",
], label="agents/01_hello_agent.py")

# ====================================================== ETAPA 2
n += 1
divider(2, "Anatomia de um agente", "Instruções dizem o que fazer. Tools dizem o que o agente consegue tocar.\nUma função Python com type hints e docstring já é uma tool.",
        """
O momento "ahh" para quem veio de SK (plugins, decorators) ou AutoGen: nada de registrar schema. Type hints + docstring viram o JSON schema.
""", n)

n += 1
code_slide(2, "Uma função vira tool", '''
from typing import Annotated
import httpx

async def consultar_cep(
    cep: Annotated[str, "CEP com 8 dígitos, com ou sem hífen. Ex.: 01310-100"],
) -> str:
    """Consulta o CEP no ViaCEP e retorna logradouro, bairro, cidade e UF
    em JSON. Use antes de cadastrar ou atualizar qualquer endereço."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"https://viacep.com.br/ws/{cep}/json/")
    return resp.text

agent = Agent(
    client=FoundryChatClient(...),
    instructions="Você atende dúvidas de cadastro. "
                 "Use as ferramentas antes de responder.",
    tools=[consultar_cep, FoundryChatClient.get_web_search_tool()],
)
''', """
Duas tools na mesma lista: uma sua, local (ViaCEP), e uma hospedada pelo Foundry (web search). O agente não sabe a diferença.
Mencione MCP como a terceira fonte de tools (servidores MCP entram na mesma lista), sem demo.
A docstring é o que o modelo lê para decidir QUANDO chamar; escreva-a para o modelo, não para o humano.
""", n, side=[
    ("Annotated", " – a descrição do parâmetro vira o schema"),
    ("Docstring", " – é o que o modelo lê para decidir quando chamar"),
    ("Retorne texto estruturado", " (JSON): previsível para o modelo"),
    ("Três fontes de tools", ": função local, hospedada no Foundry, servidor MCP"),
], label="tools/viacep.py")

# ====================================================== ETAPA 3
n += 1
divider(3, "Flexibilidade", "O agente não é acoplado ao modelo. Trocar o provider é trocar o objeto client;\ninstruções, tools e workflows não mudam.",
        """
Argumento central da etapa. Vamos provar isso duas vezes: aqui no código e, na etapa 4, ao vivo no Foundry.
""", n)

n += 1
s = slide_light()
eyebrow(s, "Etapa 3")
title(s, "Mesmo agente, três providers: só a linha do client muda")
blocks = [
    ("Microsoft Foundry", '''
from agent_framework.foundry import (
    FoundryChatClient,
)

client = FoundryChatClient(
    project_endpoint=ENDPOINT,
    model="gpt-4o-mini",
    credential=AzureCliCredential(),
)'''),
    ("Azure OpenAI direto", '''
from agent_framework.azure import (
    AzureOpenAIChatClient,
)

client = AzureOpenAIChatClient(
    endpoint=AOAI_ENDPOINT,
    deployment_name="gpt-4o-mini",
    credential=AzureCliCredential(),
)'''),
    ("OpenAI / Ollama local", '''
from agent_framework.openai import (
    OpenAIChatClient,
)

client = OpenAIChatClient(
    model_id="llama3.1",
    api_key="ollama",
    base_url=OLLAMA_URL,  # :11434/v1
)'''),
]
bw, bg = Inches(3.95), Inches(0.16)
for i, (lab, code) in enumerate(blocks):
    x = MARGIN + (bw + bg) * i
    text(s, x, Inches(1.65), bw, Inches(0.35), lab, size=14, bold=True, color=MUTED)
    code_block(s, x, Inches(2.05), bw, Inches(2.75), code, size=11)
code_block(s, MARGIN, Inches(5.0), W - 2 * MARGIN, Inches(1.4), '''
agent = Agent(client=client, instructions=..., tools=[consultar_cep, buscar_cliente_por_cpf])
workflow = SequentialBuilder(participants=[validador, analista, comunicador]).build()
# nada acima muda quando o client muda
''', size=12)
footer(s, n=n)
notes(s, """
Três blocos lado a lado, só a linha do client diferente. O bloco de baixo é o que NÃO muda: agente, tools, workflow.
No pacote do workshop isso é a função get_client() em agents/_common.py, controlada por MODEL_PROVIDER no .env.
""")

n += 1
s = slide_light()
eyebrow(s, "Etapa 3 · Comparativo")
title(s, "Microsoft Agent Framework × Google ADK")
rows = [
    ("", "Microsoft Agent Framework", "Google ADK"),
    ("Licença · linguagens", "MIT · Python, .NET", "Apache 2.0 · Python, TypeScript, Go, Java"),
    ("Modelo \"de casa\"", "Foundry (OpenAI, Anthropic, Mistral, Llama, Phi…) e qualquer provider via client", "Gemini nativo; outros via LiteLLM"),
    ("Orquestração", "Sequential, Concurrent, Handoff, Group Chat, Magentic + grafos (WorkflowBuilder)", "SequentialAgent, ParallelAgent, LoopAgent + roteamento por LLM"),
    ("Protocolos", "MCP e A2A", "MCP e A2A"),
    ("Deploy gerenciado", "Foundry Hosted Agents, Azure Functions, Durable Task", "Vertex AI Agent Engine, Cloud Run"),
    ("Dev UI local", "DevUI, Aspire Dashboard", "ADK Web"),
    ("Observabilidade", "OpenTelemetry (GenAI semconv) → Foundry / App Insights, Langfuse, OTLP", "OpenTelemetry → Cloud Trace, Langfuse, OTLP"),
    ("Herança", "Semantic Kernel + AutoGen", "Novo (2025), nascido para Gemini / Vertex"),
]
tbl = s.shapes.add_table(len(rows), 3, MARGIN, Inches(1.6), W - 2 * MARGIN, Inches(4.9)).table
tbl.columns[0].width = Inches(2.3)
tbl.columns[1].width = Inches(5.05)
tbl.columns[2].width = Inches(4.78)
for r_i, row in enumerate(rows):
    for c_i, val in enumerate(row):
        cell = tbl.cell(r_i, c_i)
        cell.fill.solid()
        cell.fill.fore_color.rgb = INK if r_i == 0 else (PANEL if r_i % 2 else WHITE)
        cell.margin_left = cell.margin_right = Inches(0.1)
        cell.margin_top = cell.margin_bottom = Inches(0.05)
        tf = cell.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        rr = p.add_run(); rr.text = val
        rr.font.name = FONT
        rr.font.size = Pt(12 if r_i else 13)
        rr.font.bold = (r_i == 0 or c_i == 0)
        rr.font.color.rgb = WHITE if r_i == 0 else (MUTED if c_i == 0 else INK)
text(s, MARGIN, Inches(6.55), W - 2 * MARGIN, Inches(0.4),
     "A escolha quase nunca é técnica: é onde estão sua identidade, sua rede, seus dados e seu time.",
     size=14, italic=True, color=BLUE)
footer(s, n=n)
notes(s, """
Não venda o MAF como "melhor em tudo": público técnico desconfia. Os dois são bons.
O MAF ganha quando o resto da casa é Azure/M365, quando você precisa de .NET e quando a observabilidade tem que cair no mesmo monitor do resto da plataforma.
""")

n += 1
s = slide_light()
eyebrow(s, "Etapa 3 · Comparativo")
title(s, "O mesmo hello agent nos dois frameworks")
half = (W - 2 * MARGIN - Inches(0.3)) / 2
text(s, MARGIN, Inches(1.6), half, Inches(0.35), "Microsoft Agent Framework · Python", size=14, bold=True, color=MUTED)
text(s, MARGIN + half + Inches(0.3), Inches(1.6), half, Inches(0.35), "Google ADK · Python", size=14, bold=True, color=MUTED)
code_block(s, MARGIN, Inches(2.0), half, Inches(4.5), '''
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient

agent = Agent(
    client=FoundryChatClient(
        project_endpoint=ENDPOINT,
        model="gpt-4o-mini",
        credential=AzureCliCredential(),
    ),
    name="Atendente",
    instructions="Responda em português.",
    tools=[consultar_cep],
)

result = await agent.run("O CEP 01310-100 existe?")
''', size=12)
code_block(s, MARGIN + half + Inches(0.3), Inches(2.0), half, Inches(4.5), '''
from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner

agent = LlmAgent(
    name="atendente",
    model="gemini-2.5-flash",
    instruction="Responda em português.",
    tools=[consultar_cep],
)

runner = InMemoryRunner(agent=agent)
# cria a sessão e itera os eventos:
# async for ev in runner.run_async(
#     user_id=..., session_id=..., new_message=...)
''', size=12)
footer(s, n=n)
notes(s, """
A simetria visual faz o argumento sozinha: a mesma função consultar_cep entra nos dois.
O que muda é o runtime ao redor: no ADK você monta runner + sessão explicitamente; no MAF o agent.run() embute isso.
""")

# ====================================================== ETAPA 4
n += 1
divider(4, "Entrando no Foundry", "Sair dos slides. Catálogo de modelos, deploy, endpoint do projeto\ne o agente da etapa 2 rodando contra ele.",
        """
Aqui é demo. Deixe o modelo JÁ implantado e o App Insights JÁ conectado ao projeto: provisionamento ao vivo é onde demo morre.
""", n)

n += 1
s = slide_light()
eyebrow(s, "Etapa 4 · Demo")
title(s, "Roteiro da tela")
steps = [
    ("Catálogo de modelos", "Filtre por provider: OpenAI, Anthropic, Mistral, Llama, Phi, DeepSeek. Não é só OpenAI."),
    ("Deploy (já feito)", "Mostre um deployment pronto. Copie o endpoint do projeto e o nome do deployment."),
    ("Rodar o agente", "Volte ao terminal, cole no .env, execute agents/02_agent_tools.py."),
    ("Trocar o modelo", "Mude FOUNDRY_MODEL para um Mistral/Anthropic e rode de novo. Zero mudança no código."),
]
for i, (t, d) in enumerate(steps):
    y = Inches(1.75) + Inches(1.15) * i
    c = rect(s, MARGIN, y, Inches(0.55), Inches(0.55), BLUE, MSO_SHAPE.OVAL)
    tf = c.text_frame; tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = str(i + 1); r.font.size = Pt(18); r.font.bold = True; r.font.color.rgb = WHITE; r.font.name = FONT
    text(s, MARGIN + Inches(0.8), y - Inches(0.05), Inches(7.2), Inches(0.4), t, size=18, bold=True)
    text(s, MARGIN + Inches(0.8), y + Inches(0.35), Inches(7.2), Inches(0.6), d, size=14, color=MUTED)
code_block(s, Inches(9.0), Inches(1.75), Inches(3.75), Inches(4.5), '''
# .env
MODEL_PROVIDER=foundry
FOUNDRY_PROJECT_ENDPOINT=
  https://<recurso>.services.ai
  .azure.com/api/projects/<proj>
FOUNDRY_MODEL=gpt-4o-mini

# trocar o modelo:
FOUNDRY_MODEL=mistral-small

# hospedar o próprio agente
# no Foundry (opcional):
pip install \\
  agent-framework-foundry-hosting
azd up
''', size=11, lang="bash")
footer(s, n=n)
notes(s, """
Passo 4 é o "uau": a etapa 3 provada na prática. Se sobrar tempo, mencione que o próprio agente pode virar um hosted agent no Foundry
(agent-framework-foundry-hosting + azd up) e o Foundry passa a gerenciar sessão, escala e identidade. Um slide, sem demo.
""")

# ====================================================== ETAPA 5
n += 1
divider(5, "De agente para sistema", "Um agente resolve conversa aberta. Um processo de negócio tem etapas.\nSe dá para escrever uma função, escreva a função.",
        """
Transição. A frase "se dá para escrever uma função, escreva a função; não use agente" está na própria doc. Técnicos adoram ouvir isso de quem está vendendo agentes.
""", n)

n += 1
s = slide_light()
eyebrow(s, "Etapa 5")
title(s, "Agente ou workflow?")
half = (W - 2 * MARGIN - Inches(0.3)) / 2
for i, (t, items, col, soft) in enumerate([
    ("Use um agente quando…", ["a tarefa é aberta ou conversacional", "precisa de planejamento e uso autônomo de tools", "uma chamada ao modelo (com tools) resolve"], BLUE, BLUE_SOFT),
    ("Use um workflow quando…", ["o processo tem etapas bem definidas", "você precisa controlar a ordem de execução", "vários agentes ou funções precisam se coordenar"], GREEN, GREEN_SOFT),
]):
    x = MARGIN + (half + Inches(0.3)) * i
    rect(s, x, Inches(1.75), half, Inches(3.7), soft, MSO_SHAPE.ROUNDED_RECTANGLE, 0.05)
    text(s, x + Inches(0.3), Inches(1.95), half - Inches(0.6), Inches(0.5), t, size=22, bold=True, color=col)
    bullets(s, x + Inches(0.3), Inches(2.6), half - Inches(0.6), Inches(2.7), items, size=16, gap=12, marker_color=col)
text(s, MARGIN, Inches(5.75), W - 2 * MARGIN, Inches(0.6),
     "Agente = autonomia.  Workflow = controle.  O framework deixa misturar os dois no mesmo grafo.",
     size=18, bold=True, align=PP_ALIGN.CENTER)
footer(s, n=n)
notes(s, """
Imagem mental: agente = autonomia, workflow = controle. Um workflow pode ter agentes como nós, e um workflow inteiro pode ser exposto como um agente (workflow.as_agent()).
""")

n += 1
s = slide_light()
eyebrow(s, "Etapa 5")
title(s, "Cinco padrões prontos: quem decide o próximo passo?")
pats = [
    ("Sequencial", "você", "Um após o outro; cada um recebe a conversa acumulada.", "validar → gravar → avisar"),
    ("Concorrente", "você", "Todos recebem a mesma entrada; um agregador consolida.", "risco, cadastro, venda em paralelo"),
    ("Handoff", "o modelo", "Transfere o controle conforme o contexto.", "triagem → especialista"),
    ("Group Chat", "um orquestrador", "Conversa compartilhada; round-robin, prompt ou regra sua.", "escreve → revisa → reescreve"),
    ("Magentic", "um gerente", "Planeja, escolhe quem age, replaneja se travar.", "problema aberto, sem passos"),
]
cw, cg = Inches(2.31), Inches(0.16)
for i, (nm, who, d, ex) in enumerate(pats):
    x = MARGIN + (cw + cg) * i
    y = Inches(1.75)
    rect(s, x, y, cw, Inches(4.3), PANEL, MSO_SHAPE.ROUNDED_RECTANGLE, 0.06)
    text(s, x + Inches(0.2), y + Inches(0.2), cw - Inches(0.4), Inches(0.45), nm, size=20, bold=True)
    chip(s, x + Inches(0.2), y + Inches(0.75), f"decide: {who}", BLUE_SOFT, BLUE, w=cw - Inches(0.4), size=10)
    text(s, x + Inches(0.2), y + Inches(1.3), cw - Inches(0.4), Inches(1.6), d, size=14, color=INK)
    text(s, x + Inches(0.2), y + Inches(3.1), cw - Inches(0.4), Inches(1.0), ex, size=13, italic=True, color=MUTED)
footer(s, n=n)
notes(s, """
A pergunta que resolve 90% dos casos: quem decide o próximo passo, você ou o modelo?
Sequencial e concorrente: você. Handoff: o modelo. Group chat e Magentic: um orquestrador/gerente, com mais custo e mais autonomia.
Hoje vamos mostrar sequencial e handoff; concorrente está no pacote.
""")

n += 1
s = slide_light()
eyebrow(s, "Etapa 5 · Cenário")
title(s, "Atualização cadastral: ViaCEP → PostgreSQL → resposta")
stages = [
    ("validador_endereco", "valida o CEP e completa o endereço", [("consultar_cep", AMBER_SOFT, AMBER)]),
    ("analista_cadastro", "localiza o cliente, checa entregas, grava o endereço", [("buscar_cliente_por_cpf", AMBER_SOFT, AMBER), ("listar_pedidos_cliente", AMBER_SOFT, AMBER), ("atualizar_endereco_cliente", AMBER_SOFT, AMBER)]),
    ("comunicador", "redige a resposta e registra o log", [("registrar_log_agente", AMBER_SOFT, AMBER)]),
]
sw, sg = Inches(3.6), Inches(0.65)
for i, (nm, d, tools) in enumerate(stages):
    x = MARGIN + (sw + sg) * i
    y = Inches(1.75)
    rect(s, x, y, sw, Inches(1.2), BLUE_SOFT, MSO_SHAPE.ROUNDED_RECTANGLE, 0.1)
    text(s, x + Inches(0.2), y + Inches(0.1), sw - Inches(0.4), Inches(0.4), nm, size=16, bold=True, color=BLUE, font=MONO)
    text(s, x + Inches(0.2), y + Inches(0.52), sw - Inches(0.4), Inches(0.65), d, size=13, color=INK)
    for j, (tl, fl, fg) in enumerate(tools):
        chip(s, x + Inches(0.2), y + Inches(1.4) + Inches(0.42) * j, tl, fl, fg, w=sw - Inches(0.4), size=11, mono=True)
    if i < 2:
        arrow(s, x + sw + Inches(0.12), y + Inches(0.46), Inches(0.4))
# fontes de dados (abaixo dos chips: 1.75 + 1.4 + 3*0.42 = 4.4)
cy = Inches(4.75)
cloud = s.shapes.add_shape(MSO_SHAPE.CLOUD, MARGIN + Inches(0.9), cy, Inches(1.8), Inches(1.0)); _fill(cloud, AMBER_SOFT); cloud.shadow.inherit = False
text(s, MARGIN + Inches(0.9), cy + Inches(0.27), Inches(1.8), Inches(0.5), "ViaCEP", size=14, bold=True, color=AMBER, align=PP_ALIGN.CENTER)
db = s.shapes.add_shape(MSO_SHAPE.CAN, MARGIN + Inches(4.9), cy - Inches(0.05), Inches(1.4), Inches(1.1)); _fill(db, AMBER_SOFT); db.shadow.inherit = False
text(s, MARGIN + Inches(4.6), cy + Inches(0.3), Inches(2.0), Inches(0.5), "PostgreSQL", size=14, bold=True, color=AMBER, align=PP_ALIGN.CENTER)
text(s, MARGIN + Inches(6.9), cy - Inches(0.1), Inches(5.3), Inches(1.3),
     "clientes · enderecos (histórico, principal=true) · pedidos (status) · log_agentes (auditoria)\n"
     "Nada de SQL livre vindo do modelo: queries fixas e parametrizadas. A autonomia está em qual tool chamar, não em qual SQL rodar.",
     size=12, color=MUTED)
text(s, MARGIN, Inches(6.1), W - 2 * MARGIN, Inches(0.5),
     "Por que sequencial? A ordem importa: não se grava endereço sem validar o CEP, nem se avisa o cliente antes de gravar.",
     size=15, bold=True, color=GREEN)
footer(s, n=n)
notes(s, """
Esse é o cenário que vamos rodar. Três agentes, cada um com as tools do seu domínio (azul = agente, âmbar = tool/dado).
Ponto de governança para a plateia: o modelo nunca escreve SQL. As tools são funções com queries fixas e parametrizadas; toda escrita gera linha em log_agentes.
""")

n += 1
code_slide(5, "Sequencial: três agentes, uma linha de build", '''
from agent_framework.orchestrations import SequentialBuilder
from tools import consultar_cep, buscar_cliente_por_cpf, listar_pedidos_cliente, atualizar_endereco_cliente

validador = client.as_agent(name="validador_endereco", tools=[consultar_cep],
    instructions="Extraia CEP e número, valide no ViaCEP e devolva o endereço completo. Não invente.")
analista = client.as_agent(name="analista_cadastro",
    tools=[buscar_cliente_por_cpf, listar_pedidos_cliente, atualizar_endereco_cliente],
    instructions="Busque o cliente, liste pedidos em aberto e, se o CEP foi validado, grave o endereço.")
comunicador = client.as_agent(name="comunicador",
    instructions="Escreva a resposta ao cliente. Alerte sobre pedidos já enviados.")

workflow = SequentialBuilder(
    participants=[validador, analista, comunicador],
    intermediate_output_from=[validador, analista],   # mostra cada etapa, não só a última
).build()

async for event in workflow.run(pedido_do_cliente, stream=True):
    if event.type == "executor_invoked":  print("▶", event.executor_id)
    elif event.type == "intermediate":    print(event.executor_id, event.data.messages[-1].text)
    elif event.type == "output":          print("✔", event.data.messages[-1].text)
''', """
Mostre que o builder é uma linha. O resto é definir agentes, que é o que já vimos na etapa 2.
Os eventos: executor_invoked (quem começou), intermediate (saída de cada etapa), output (resultado final). Em produção você publica isso num stream para a UI.
Rode agents/03_sequential_atualizacao_cadastral.py ao vivo. A saída mostra o pedido PED-2026-0001 "enviado" indo para o endereço antigo: é o tipo de alerta que o comunicador precisa dar.
""", n, size=11, label="agents/03_sequential_atualizacao_cadastral.py")

n += 1
code_slide(5, "Handoff: o modelo decide quem atende", '''
from agent_framework.orchestrations import HandoffBuilder

triagem = client.as_agent(name="triagem",
    instructions="Transfira para 'cadastro' (endereço/dados) ou "
                 "'pedidos' (status/entrega). Não responda ao mérito.")

cadastro = client.as_agent(name="cadastro",
    tools=[consultar_cep, buscar_cliente_por_cpf, atualizar_endereco_cliente],
    instructions="Valide o CEP antes de qualquer atualização.")

pedidos = client.as_agent(name="pedidos",
    tools=[buscar_cliente_por_cpf, listar_pedidos_cliente],
    instructions="Responda com código, status e previsão. Nunca altere dados.")

workflow = (
    HandoffBuilder(name="atendimento", participants=[triagem, cadastro, pedidos])
    .with_start_agent(triagem)
    .with_autonomous_mode(                      # guardrail: rodadas sem humano
        turn_limits={"triagem": 2, "cadastro": 4, "pedidos": 3})
    .build()
)
''', """
Sequencial = você decide a ordem. Handoff = o LLM decide quem atende. Cada especialista só tem as tools do seu domínio: menos tools, menos risco.
with_autonomous_mode(turn_limits=...) é o guardrail de "quantas rodadas sem humano". Gancho perfeito para a etapa 6: como você sabe que o limite foi atingido? Observando.
""", n, side=[
    ("Triagem", " não resolve: só encaminha"),
    ("Escopo por tools", ": o agente de pedidos não consegue alterar nada"),
    ("turn_limits", " = quantas rodadas sem humano"),
    ("Alternativa", ": with_request_info() pausa para aprovação humana"),
], size=11, label="agents/05_handoff_atendimento.py")

# ====================================================== ETAPA 6
n += 1
divider(6, "Observabilidade", "O agente que você não enxerga não vai para produção.\nTudo até aqui é bonito em demo; isto é o que separa demo de produção.",
        """
Argumento: todo o resto desta palestra é bonito em demo. Isto é o que separa demo de produção.
""", n)

n += 1
code_slide(6, "Mesmo workflow, agora instrumentado", '''
from agent_framework.observability import configure_otel_providers, get_tracer

client = get_client()

if OBS_TARGET == "foundry":
    # o FoundryChatClient conhece a connection string do App Insights do projeto
    client.configure_azure_monitor(enable_sensitive_data=True)
elif OBS_TARGET == "aspire":
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://localhost:4317"
    configure_otel_providers(enable_sensitive_data=True)
else:
    os.environ["ENABLE_CONSOLE_EXPORTERS"] = "true"
    configure_otel_providers()

tracer = get_tracer()
with tracer.start_as_current_span("atendimento.atualizacao_cadastral") as span:
    span.set_attribute("workshop.cenario", "atualizacao_cadastral")
    async for event in workflow.run(entrada, stream=True):
        ...
''', """
Nada muda no agente. OpenTelemetry com as convenções semânticas GenAI; o destino é uma variável de ambiente.
enable_sensitive_data=True grava prompts e respostas nos spans: ótimo em demo, decisão de governança em produção.
Demo: rode com OBS_TARGET=foundry e abra Foundry → Build → Agents → Traces.
""", n, side=[
    ("console", " – spans no terminal, zero setup"),
    ("aspire", " – container local, UI em :18888"),
    ("foundry", " – App Insights do projeto; Traces e Monitor"),
    ("Mesmo trace", " vai para Langfuse, Grafana, Datadog: é OTLP"),
], size=11, label="agents/07_observability.py")

n += 1
s = slide_light()
eyebrow(s, "Etapa 6 · O que aparece no monitor")
title(s, "Um trace do cenário: workflow → agente → modelo → tool")
trace = [
    ("atendimento.atualizacao_cadastral", GREEN, 0, 100, "8,4 s"),
    ("  workflow.run · sequential", GREEN, 1, 98, "8,2 s"),
    ("    invoke_agent validador_endereco", BLUE, 2, 22, "1,9 s"),
    ("      chat gpt-4o-mini · 312 → 48 tok", MUTED, 3, 8, "0,7 s"),
    ("      execute_tool consultar_cep", AMBER, 11, 5, "0,4 s"),
    ("      chat gpt-4o-mini · 410 → 96 tok", MUTED, 16, 8, "0,8 s"),
    ("    invoke_agent analista_cadastro", BLUE, 24, 48, "4,0 s"),
    ("      execute_tool buscar_cliente_por_cpf", AMBER, 33, 3, "0,2 s"),
    ("      execute_tool listar_pedidos_cliente", AMBER, 36, 3, "0,2 s"),
    ("      execute_tool atualizar_endereco_cliente", AMBER, 40, 4, "0,3 s"),
    ("      chat gpt-4o-mini · 1,2k → 210 tok", MUTED, 45, 27, "2,6 s"),
    ("    invoke_agent comunicador", BLUE, 73, 25, "2,1 s"),
    ("      execute_tool registrar_log_agente", AMBER, 76, 3, "0,2 s"),
    ("      chat gpt-4o-mini · 980 → 160 tok", MUTED, 80, 18, "1,7 s"),
]
lx, bx, bw_total = MARGIN, Inches(6.3), Inches(5.5)
row_h = Inches(0.32)
y0 = Inches(1.75)
rect(s, lx, y0 - Inches(0.1), W - 2 * MARGIN, row_h * len(trace) + Inches(0.2), PANEL, MSO_SHAPE.ROUNDED_RECTANGLE, 0.03)
for i, (name, col, left, width, dur) in enumerate(trace):
    y = y0 + row_h * i
    text(s, lx + Inches(0.15), y, Inches(5.9), row_h, name.replace("  ", "\u2007\u2007"), size=11, font=MONO, anchor=MSO_ANCHOR.MIDDLE)
    rect(s, bx + int(bw_total * left / 100), y + Inches(0.09), max(int(bw_total * width / 100), Inches(0.06)), Inches(0.14), col, MSO_SHAPE.ROUNDED_RECTANGLE, 0.3)
    text(s, W - MARGIN - Inches(0.9), y, Inches(0.8), row_h, dur, size=10, color=MUTED, align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
legend_y = y0 + row_h * len(trace) + Inches(0.3)
for i, (lab, col) in enumerate([("workflow", GREEN), ("agente", BLUE), ("modelo", MUTED), ("tool", AMBER)]):
    x = MARGIN + Inches(1.5) * i
    rect(s, x, legend_y + Inches(0.08), Inches(0.3), Inches(0.14), col, MSO_SHAPE.ROUNDED_RECTANGLE, 0.3)
    text(s, x + Inches(0.38), legend_y - Inches(0.02), Inches(1.1), Inches(0.35), lab, size=12, color=MUTED, anchor=MSO_ANCHOR.MIDDLE)
text(s, Inches(6.8), legend_y - Inches(0.05), Inches(5.9), Inches(0.5),
     "Tokens e latência por nó. A tabela log_agentes é a trilha de negócio; o trace é a trilha técnica.",
     size=12, italic=True, color=MUTED)
footer(s, n=n)
notes(s, """
Valores ilustrativos de uma execução. Aponte a árvore: span pai por requisição de negócio, abaixo workflow → cada agente → chamada ao modelo → execução de tool.
Repare que o analista é o nó mais caro (3 tools + 1,2k tokens de contexto): é onde otimizar.
Agente rodando fora do Azure? Registre como custom agent no Foundry e envie com o mesmo gen_ai.agent.id; aparece no mesmo monitor.
""")

# ====================================================== FECHAMENTO
n += 1
s = slide_dark()
eyebrow(s, "Para levar", dark=True, y=Inches(1.3))
text(s, MARGIN, Inches(1.8), Inches(11.5), Inches(0.9), "Três frases", size=40, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
for i, (big, small) in enumerate([
    ("Começa com 10 linhas.", "Cliente, instruções, run(). O resto é incremental: tools, workflows, hosting."),
    ("O agente não se casa com o modelo.", "Trocar o provider é trocar um objeto. Foundry dá catálogo, deploy e identidade."),
    ("O que vai para produção é o que você consegue observar.", "OpenTelemetry, GenAI semconv, o mesmo monitor do resto da plataforma."),
]):
    y = Inches(3.0) + Inches(1.15) * i
    rect(s, MARGIN, y + Inches(0.12), Inches(0.12), Inches(0.75), BLUE, MSO_SHAPE.OVAL)
    text(s, MARGIN + Inches(0.4), y, Inches(11.5), Inches(0.5), big, size=22, bold=True, color=WHITE)
    text(s, MARGIN + Inches(0.4), y + Inches(0.5), Inches(11.5), Inches(0.5), small, size=15, color=DARK_SUB)
footer(s, dark=True, n=n)
notes(s, """
Volte para a pergunta da abertura: "quem levantou a mão no while True, agora sabe por onde começar".
""")

n += 1
s = slide_light()
eyebrow(s, "Recursos")
title(s, "Para continuar depois da palestra")
res = [
    ("Pacote do workshop", "maf-workshop/: agentes, tools ViaCEP + Postgres, SQL de criação e carga, docker-compose, página interativa"),
    ("Documentação", "learn.microsoft.com/agent-framework  ·  learn.microsoft.com/azure/foundry"),
    ("Repositório", "github.com/microsoft/agent-framework (samples em python/samples)"),
    ("Migração", "Guias oficiais de Semantic Kernel e AutoGen para o Agent Framework"),
    ("Observabilidade", "learn.microsoft.com/azure/foundry/observability  ·  Aspire Dashboard (docker)"),
]
for i, (t, d) in enumerate(res):
    y = Inches(1.7) + Inches(0.85) * i
    rect(s, MARGIN, y + Inches(0.1), Inches(0.14), Inches(0.5), BLUE_SOFT, MSO_SHAPE.ROUNDED_RECTANGLE, 0.5)
    text(s, MARGIN + Inches(0.4), y, Inches(3.2), Inches(0.7), t, size=17, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    text(s, MARGIN + Inches(3.7), y, Inches(8.4), Inches(0.7), d, size=14, color=MUTED, anchor=MSO_ANCHOR.MIDDLE)
rect(s, MARGIN, Inches(6.1), W - 2 * MARGIN, Inches(0.55), AMBER_SOFT, MSO_SHAPE.ROUNDED_RECTANGLE, 0.3)
text(s, MARGIN + Inches(0.25), Inches(6.1), W - 2 * MARGIN - Inches(0.5), Inches(0.55),
     "Cuidado de palco: modelo implantado e App Insights conectado ANTES de subir. Deixe um trace de execução anterior aberto numa aba, caso a rede falhe.",
     size=13, bold=True, color=AMBER, anchor=MSO_ANCHOR.MIDDLE)
footer(s, n=n)
notes(s, """
Perguntas. Deixe o QR/link do pacote na tela.
""")

prs.save(OUT)
print(f"✔ {OUT.name} gerado com {len(prs.slides)} slides")
