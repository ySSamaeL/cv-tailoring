"""Vaga (URL ou texto) -> JSON estruturado.

Uso:
    python scripts/extrair_vaga.py --texto vaga.txt  [-o vaga.json]
    python scripts/extrair_vaga.py --url https://...  [-o vaga.json]
    cat vaga.txt | python scripts/extrair_vaga.py --texto -

A extração é heurística e determinística (regex + léxico de conceitos). O JSON é um
rascunho: o Claude revisa e corrige campos vazios ou errados antes da análise.
Links do LinkedIn não são buscados (os termos de uso proíbem acesso automatizado):
o script sai com código 4 e a skill pede o texto colado. O mesmo vale para qualquer
URL que não devolva o anúncio (login, bloqueio, página só em JS). Gupy e páginas com
JSON-LD JobPosting são lidas direto.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.error
import urllib.request

from _comum import achar_termo, carregar_conceitos, conceitos_no_texto, dobrar, ler_entrada

# ---------------------------------------------------------------- busca por URL

AGENTE = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)
SINAIS_BLOQUEIO = [
    "authwall", "sign in to view", "entre para ver", "faça login", "join linkedin",
    "cadastre-se agora", "captcha", "access denied", "verify you are human",
    "enable javascript", "habilite o javascript", "this job is no longer available",
    "vaga não está mais disponível", "no longer accepting applications",
]


class FalhaBusca(Exception):
    pass


def baixar(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": AGENTE, "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            bruto = resp.read()
            charset = resp.headers.get_content_charset() or "utf-8"
    except urllib.error.HTTPError as e:
        raise FalhaBusca(f"HTTP {e.code}") from e
    except (urllib.error.URLError, TimeoutError) as e:
        raise FalhaBusca(str(e)) from e
    return bruto.decode(charset, errors="replace")


def jsonld_vaga(pagina: str) -> dict | None:
    """Procura um JobPosting em JSON-LD (Gupy, Greenhouse, Lever e muitos ATS publicam)."""
    for bloco in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', pagina, re.S | re.I):
        try:
            dado = json.loads(html.unescape(bloco.strip()))
        except json.JSONDecodeError:
            continue
        candidatos = dado if isinstance(dado, list) else dado.get("@graph", [dado]) if isinstance(dado, dict) else []
        for c in candidatos:
            if isinstance(c, dict) and c.get("@type") == "JobPosting":
                return c
    return None


def html_para_texto(pagina: str) -> str:
    pagina = re.sub(r"<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", pagina, flags=re.S | re.I)
    pagina = re.sub(r"<br\s*/?>|</(p|div|li|h\d|tr|ul|ol)>", "\n", pagina, flags=re.I)
    pagina = re.sub(r"<li[^>]*>", "\n- ", pagina, flags=re.I)
    pagina = re.sub(r"<[^>]+>", " ", pagina)
    texto = html.unescape(pagina)
    linhas = [re.sub(r"[ \t ]+", " ", l).strip() for l in texto.splitlines()]
    return "\n".join(l for l in linhas if l)


def id_linkedin(url: str) -> str | None:
    m = re.search(r"currentJobId=(\d+)", url) or re.search(r"/jobs/view/(?:[^/?]*-)?(\d+)", url)
    return m.group(1) if m else None


def nextdata_vaga(pagina: str) -> dict | None:
    """Páginas da Gupy (Next.js) trazem a vaga no JSON de __NEXT_DATA__, sem JSON-LD."""
    m = re.search(r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>', pagina, re.S)
    if not m:
        return None
    try:
        dado = json.loads(m.group(1))
    except json.JSONDecodeError:
        return None

    def procurar(no):
        if isinstance(no, dict):
            if isinstance(no.get("description"), str) and len(no["description"]) > 200 and ("name" in no or "title" in no):
                return no
            for v in no.values():
                achado = procurar(v)
                if achado:
                    return achado
        elif isinstance(no, list):
            for v in no:
                achado = procurar(v)
                if achado:
                    return achado
        return None

    return procurar(dado)


def texto_da_url(url: str) -> tuple[str, dict]:
    if "linkedin.com" in url:
        # Os termos do LinkedIn (§8.2) e o robots.txt proíbem acesso automatizado,
        # mesmo à página pública. A skill não busca: pede o texto colado.
        vid = id_linkedin(url)
        raise FalhaBusca(
            "o LinkedIn não permite leitura automatizada de vagas"
            + (f" (vaga {vid})" if vid else "")
            + "; abra o link no navegador, selecione todo o texto da vaga e cole aqui"
        )
    pagina = baixar(url)
    meta: dict = {"url": url}
    vaga = jsonld_vaga(pagina)
    if not vaga:
        nd = nextdata_vaga(pagina)
        if nd:
            vaga = {"title": nd.get("name") or nd.get("title"), "description": nd["description"],
                    "hiringOrganization": {"name": (nd.get("company") or {}).get("name") if isinstance(nd.get("company"), dict) else None}}
    if vaga:
        meta["fonte"] = "json-ld"
        org = vaga.get("hiringOrganization") or {}
        meta["empresa"] = org.get("name") if isinstance(org, dict) else None
        meta["titulo"] = vaga.get("title")
        local = vaga.get("jobLocation")
        if isinstance(local, list):
            local = local[0] if local else None
        if isinstance(local, dict):
            end = local.get("address") or {}
            if isinstance(end, dict):
                meta["local"] = ", ".join(x for x in [end.get("addressLocality"), end.get("addressRegion")] if x)
        if vaga.get("jobLocationType") == "TELECOMMUTE":
            meta["modelo"] = "remoto"
        texto = html_para_texto(vaga.get("description", ""))
        if meta.get("titulo"):
            texto = f"{meta['titulo']}\n{texto}"
    else:
        meta["fonte"] = "html"
        texto = html_para_texto(pagina)
    dob = dobrar(texto)
    if len(texto) < 400 or (any(s in dob for s in SINAIS_BLOQUEIO) and len(texto) < 3000):
        raise FalhaBusca("página sem o anúncio (muro de login, bloqueio ou conteúdo só em JavaScript)")
    if not re.search(r"requisit|requirement|qualifica|responsabilidad|responsibilit|experi[eê]ncia|experience", dob):
        raise FalhaBusca("o texto baixado não parece um anúncio de vaga")
    return texto, meta


# ---------------------------------------------------------------- extração do texto

PT = set("de da do que para com uma você voce seu sua nosso nossa vaga requisitos experiência experiencia conhecimento são e em os as".split())
EN = set("the and you your our with for we are to of in experience requirements skills will role team".split())


def detectar_idioma(texto: str) -> str:
    palavras = re.findall(r"[a-zà-ú]+", texto.lower())
    pt = sum(p in PT for p in palavras)
    en = sum(p in EN for p in palavras)
    return "pt" if pt >= en else "en"


CABECALHOS = {
    "obrigatorios": r"requisitos|requirements|qualifica[cç][oõ]es|qualifications|o que (buscamos|esperamos|procuramos)|o que voc[eê] (precisa|deve) (saber|ter)|o que [eé] necess[aá]rio|what (we're|we are) looking for|what you('ll)? (need|bring)|must[- ]haves?|obrigat[oó]rio|pr[eé]-requisitos|you have|you bring|about you|sobre voc[eê]|perfil (desejado|da vaga)|skills",
    "desejaveis": r"diferenciais|desej[aá]v|nice[- ]to[- ]have|bonus|plus|preferred|pontos? extras?|ser[aá] um diferencial|good to have",
    "responsabilidades": r"responsabilidades|atribui[cç][oõ]es|atividades|o que voc[eê] (vai|ir[aá]) fazer|no dia a dia|desafios|responsibilities|what you('ll| will) do|the role|your (day|mission)|key duties",
    "beneficios": r"benef[ií]cios|benefits|perks|oferecemos|o que oferecemos|desenvolvimento e benef[ií]cios|what we offer|remunera[cç][aã]o",
    "empresa": r"sobre (a|n[oó]s|o time|a empresa)|about (us|the company|the team)|quem somos|who we are",
    "etapas": r"etapas do processo|processo seletivo|hiring process|interview process",
    "meta": r"modelo de trabalho|local de trabalho|localiza[cç][aã]o|location|work model|regime|jornada|sal[aá]rio|salary|tipo de contrata[cç][aã]o",
}


def classificar_cabecalho(linha: str) -> str | None:
    limpo = dobrar(linha).strip(" :-–•*#").strip()
    if re.match(rf"^({dobrar(CABECALHOS['meta'])}|{dobrar(CABECALHOS['etapas'])})\s*:", limpo):
        return "meta"
    if len(limpo) > 70 or len(limpo) < 4:
        return None
    for nome, padrao in CABECALHOS.items():
        if re.match(rf"^({dobrar(padrao)})\b", limpo):
            return nome
    return None


def secoes(texto: str) -> dict[str, list[str]]:
    saida: dict[str, list[str]] = {k: [] for k in ["intro", *CABECALHOS]}
    atual = anterior = "intro"
    for linha in texto.splitlines():
        linha = linha.strip()
        if not linha:
            continue
        cab = classificar_cabecalho(linha)
        if cab:
            atual = cab
            resto = re.split(r"[:：]", linha, maxsplit=1)
            if len(resto) == 2 and len(resto[1].strip()) > 3:
                saida[atual].append(resto[1].strip())
            if cab == "meta":
                # linha solta ("Modelo de trabalho: híbrido"), não abre seção nova
                atual = anterior
            else:
                anterior = atual
            continue
        anterior = atual
        item = re.sub(r"^[-•*●▪◦·>]+\s*|^\d+[.)]\s+", "", linha)
        saida[atual].append(item)
    # Itens obrigatórios que se declaram diferencial vão para desejáveis.
    marca = re.compile(r"diferencial|desej[aá]vel|nice to have|is a plus|\bplus\b|\bbonus\b|preferred|ser[aá] um diferencial", re.I)
    mover = [i for i in saida["obrigatorios"] if marca.search(i)]
    saida["obrigatorios"] = [i for i in saida["obrigatorios"] if i not in mover]
    saida["desejaveis"] = mover + saida["desejaveis"]
    return saida


SENIORIDADES = [
    ("estagio", r"est[aá]gio|estagi[aá]ri[oa]|intern(ship)?\b|trainee"),
    ("senior", r"s[eê]nior|\bsr\.?\b|\biii\b|especialista|staff|principal|tech lead|\blead\b|lideran[cç]a t[eé]cnica"),
    ("pleno", r"\bpleno\b|\bpl\b|mid[- ]?level|\bmid\b|\bii\b|intermedi[aá]ri"),
    ("junior", r"j[uú]nior|\bjr\.?\b|entry[- ]level|\bi\b(?=\s*$)|associate|graduate"),
]


def detectar_senioridade(titulo: str, texto: str) -> str:
    for nome, padrao in SENIORIDADES:
        if re.search(padrao, titulo, re.I):
            return nome
    for nome, padrao in SENIORIDADES:
        if nome != "senior" and re.search(rf"(vaga|n[ií]vel|level|position)[^.\n]{{0,20}}({padrao})", texto, re.I):
            return nome
    return "nao-informada"


def detectar_modelo(texto: str) -> str:
    dob = dobrar(texto)
    remoto = re.search(r"100% remot|remoto|remote|home office|anywhere|trabalho a distancia|work from home", dob)
    hibrido = re.search(r"hibrid|hybrid", dob)
    presencial = re.search(r"presencial|on[- ]?site|in[- ]office|no escritorio", dob)
    if hibrido:
        return "hibrido"
    if presencial and not remoto:
        return "presencial"
    if remoto and not presencial:
        return "remoto"
    if remoto and presencial:
        return "ambiguo"
    return "nao-informado"


CIDADES = [
    "Recife", "Olinda", "Jaboatão dos Guararapes", "Jaboatão", "Paulista", "Camaragibe", "Cabo de Santo Agostinho",
    "São Lourenço da Mata", "Abreu e Lima", "Igarassu", "Ipojuca", "Moreno", "Itamaracá", "Itapissuma", "Araçoiaba",
    "São Paulo", "Rio de Janeiro", "Belo Horizonte", "Curitiba", "Porto Alegre", "Florianópolis", "Campinas",
    "Brasília", "Salvador", "Fortaleza", "Goiânia", "Manaus", "Belém", "João Pessoa", "Natal", "Maceió", "Aracaju",
    "Teresina", "São Luís", "Vitória", "Campo Grande", "Cuiabá", "Joinville", "Blumenau", "Barueri", "Santos",
    "São José dos Campos", "Ribeirão Preto", "Sorocaba", "Uberlândia", "Londrina", "Caruaru", "Petrolina",
    "Lisboa", "Porto", "London", "Dublin", "Berlin", "Amsterdam", "Toronto", "Remote",
]


def detectar_local(texto: str) -> str | None:
    for cidade in sorted(CIDADES, key=len, reverse=True):
        if cidade == "Remote":
            continue
        if re.search(rf"(?<![\w]){re.escape(cidade)}(?![\w])", texto):
            return cidade
    return None


def detectar_relocacao(texto: str) -> bool:
    """Oferta de relocação, ignorando frases negadas ("não oferecemos relocation")."""
    padrao = r"reloca|realoca|ajuda de (custo para )?mudan[cç]a|aux[ií]lio[- ]mudan[cç]a|apoio (à|a) mudan[cç]a|relocation|visa sponsorship"
    for m in re.finditer(padrao, texto, re.I):
        antes = texto[max(0, m.start() - 45) : m.start()]
        if not re.search(r"\b(n[aã]o|nem|sem|no|not|without|unable)\b", antes, re.I):
            return True
    return False


def palavras_chave(sec: dict[str, list[str]]) -> list[dict]:
    conceitos = carregar_conceitos()
    pesos = {"obrigatorios": 3, "responsabilidades": 2, "desejaveis": 1, "intro": 1}
    achados: dict[str, dict] = {}
    for nome_sec, peso in pesos.items():
        for item in sec[nome_sec]:
            for c, forma in conceitos_no_texto(item, conceitos):
                reg = achados.setdefault(
                    c["id"],
                    {"conceito": c["id"], "forma_na_vaga": forma, "onde": nome_sec, "ocorrencias": 0, "peso": 0},
                )
                reg["ocorrencias"] += 1
                reg["peso"] += peso
    # Se a forma canônica (1ª variante) aparece no anúncio, ela é a palavra-chave a espelhar.
    todo = "\n".join(sum((sec[k] for k in pesos), []))
    por_id = {c["id"]: c for c in conceitos}
    for reg in achados.values():
        canonica = achar_termo(todo, por_id[reg["conceito"]]["variantes"][0])
        if canonica:
            reg["forma_na_vaga"] = canonica
    return sorted(achados.values(), key=lambda r: (-r["peso"], r["conceito"]))


def detectar_empresa(texto: str) -> str | None:
    """Linha de cabeçalho no formato do LinkedIn/Gupy: 'Empresa · Local · Tipo'."""
    linhas = [l.strip() for l in texto.splitlines() if l.strip()][:4]
    for l in linhas[1:]:
        partes = re.split(r"\s+[·|•]\s+|\s+-\s+", l)
        if len(partes) >= 2 and len(partes[0]) <= 60:
            return partes[0].strip()
    m = re.search(r"(?:empresa|company)\s*:\s*(.+)", texto, re.I)
    return m.group(1).strip() if m else None


def extrair(texto: str, meta: dict | None = None) -> dict:
    meta = meta or {}
    sec = secoes(texto)
    primeira = next((l.strip() for l in texto.splitlines() if l.strip()), "")
    titulo = meta.get("titulo") or primeira[:120]
    texto_util = "\n".join(sum((sec[k] for k in ["intro", "obrigatorios", "desejaveis", "responsabilidades"]), []))
    local = meta.get("local") or detectar_local(texto)
    texto_sem_beneficios = "\n".join(l for k, v in sec.items() if k != "beneficios" for l in v)
    return {
        "titulo": titulo,
        "empresa": meta.get("empresa") or detectar_empresa(texto),
        "local": local,
        # benefícios ("auxílio home office") não dizem nada sobre o modelo de trabalho
        "modelo_trabalho": meta.get("modelo") or detectar_modelo(texto_sem_beneficios),
        "relocacao_oferecida": detectar_relocacao(texto),
        "senioridade": detectar_senioridade(titulo, texto),
        "idioma": detectar_idioma(texto_util or texto),
        "obrigatorios": sec["obrigatorios"],
        "desejaveis": sec["desejaveis"],
        "responsabilidades": sec["responsabilidades"],
        "palavras_chave": palavras_chave(sec),
        "fonte": meta.get("fonte", "texto"),
        "url": meta.get("url"),
        "revisar": [],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    grupo = ap.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--texto", help="arquivo com o texto da vaga ('-' para stdin)")
    grupo.add_argument("--url", help="link da vaga")
    ap.add_argument("-o", "--saida", help="arquivo JSON de saída (padrão: stdout)")
    ap.add_argument("--salvar-texto", help="com --url, grava o texto baixado neste arquivo")
    args = ap.parse_args()

    if args.url:
        try:
            texto, meta = texto_da_url(args.url)
        except FalhaBusca as e:
            print(f"NAO_FOI_POSSIVEL_LER_A_VAGA: {e}. Peça ao usuário para colar o texto do anúncio.", file=sys.stderr)
            return 4
        if args.salvar_texto:
            open(args.salvar_texto, "w", encoding="utf-8").write(texto)
    else:
        texto, meta = ler_entrada(args.texto), {}

    dados = extrair(texto, meta)
    if not dados["obrigatorios"]:
        dados["revisar"].append("Nenhuma seção de requisitos reconhecida: separar obrigatórios e desejáveis à mão.")
    if dados["empresa"] is None:
        dados["revisar"].append("Empresa não identificada.")
    if dados["modelo_trabalho"] in ("nao-informado", "ambiguo"):
        dados["revisar"].append("Modelo de trabalho não está claro no anúncio.")
    if dados["local"] is None and dados["modelo_trabalho"] != "remoto":
        dados["revisar"].append("Localidade não identificada.")

    saida = json.dumps(dados, ensure_ascii=False, indent=2)
    if args.saida:
        open(args.saida, "w", encoding="utf-8").write(saida + "\n")
    else:
        print(saida)
    return 0


if __name__ == "__main__":
    sys.exit(main())
