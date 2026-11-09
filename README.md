<div align="center">

# 🎯 cv-tailoring

**Seu currículo adaptado a cada vaga em minutos, sem inventar nada.**

Uma *skill* para o [Claude](https://claude.com) que lê uma vaga, mostra se vale a pena aplicar e gera um currículo de uma página feito para ela. Todo fato vem do **seu** perfil.

![Python](https://img.shields.io/badge/python-3.11+-3776AB?logo=python&logoColor=white)
![Claude Code](https://img.shields.io/badge/Claude%20Code-skill-D97757)
![PDF](https://img.shields.io/badge/PDF-Typst-239DAD)
![ATS](https://img.shields.io/badge/ATS-friendly-2ea44f)

</div>

---

## 💡 Por que existe

Mandar o mesmo currículo para todas as vagas não funciona: os sistemas de triagem (ATS) e os recrutadores procuram as palavras da vaga. Reescrever à mão para cada uma cansa, e usar IA "solta" é pior: ela inventa experiências, ferramentas e números.

O **cv-tailoring** resolve isso com uma regra simples:

> 🔒 **A vaga dá o vocabulário. O seu perfil dá os fatos.**

Se a vaga pede algo que você não tem, isso aparece como **lacuna** na análise. Não entra no currículo.

## ✨ O que ele faz

```
 vaga  ──►  análise de aderência  ──►  ✋ você aprova  ──►  currículo  ──►  verificador  ──►  PDF
```

| | |
| --- | --- |
| 🔎 **Análise de aderência** | Localidade, senioridade, requisito por requisito com a evidência do seu perfil, palavras-chave, score e recomendação. |
| ✋ **Para e pergunta** | Nada é escrito antes de você aprovar a análise. |
| 📝 **Currículo de 1 página** | Escolhe o posicionamento certo (QA, automação, full stack, IA...) e reescreve os bullets com os termos da vaga. |
| ✅ **Verificador de fatos** | Confere cada linha contra o perfil e reprova número, ferramenta ou cargo inventado. |
| 📄 **PDF pronto para ATS** | Uma coluna, texto selecionável, gerado com Typst. |
| 🌎 **PT e EN** | Vagas em português ou inglês. |
| ✉️ **Extras** | Carta de apresentação, possíveis perguntas de entrevista e texto para os campos da Gupy. |

## 🚀 Começando

### 1. Instale

```bash
git clone https://github.com/ySSamaeL/cv-tailoring.git
cd cv-tailoring
pip install -r requirements.txt       # só typst e pypdf; não precisa de LaTeX
python -m unittest discover -s tests  # confere se está tudo certo
```

### 2. Crie o seu perfil-mestre

O perfil **não vem no repositório**, porque é pessoal. Crie `references/perfil-mestre.md` com tudo o que pode ir para um currículo: experiências (no formato Contexto → Ação → Resultado), ferramentas com nível, formação, idiomas e métricas com fonte. Os modelos em `references/modelos/` mostram o formato esperado.

> ⚠️ O arquivo já está no `.gitignore`. Ele fica só no seu computador.

### 3. Conecte ao Claude

**Claude Code**: crie um link da pasta em `~/.claude/skills/`:

```bash
# macOS / Linux
ln -s "$(pwd)" ~/.claude/skills/cv-tailoring
```

```powershell
# Windows (PowerShell, não exige administrador)
New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\cv-tailoring" -Target (Get-Location)
```

Abra uma sessão nova e confira com `/skills`.

**claude.ai / Cowork**: gere o pacote e faça upload em *Settings → Capabilities → Skills*:

```bash
python scripts/empacotar.py   # gera dist/cv-tailoring.zip
```

## 🗣️ Como usar

É só colar a vaga e pedir:

> *"Adapta meu currículo para esta vaga: https://empresa.gupy.io/jobs/123"*
>
> *"Vale a pena aplicar? [texto da vaga]"*
>
> *"Tailor my resume for this job: [job description]"*
>
> *"Faz a carta de apresentação também."*

1. **Vaga:** links da Gupy, Greenhouse, Lever e páginas de carreira são lidos direto. No **LinkedIn**, cole o texto: os termos de uso proíbem acesso automatizado.
2. **Análise:** você recebe a aderência com evidências e responde "ok" ou ajusta o rumo.
3. **Currículo:** o PDF sai em `historico/<empresa>-<cargo>-<data>/`, pasta que também fica fora do Git.

### Usando os scripts sem o Claude

```bash
python scripts/extrair_vaga.py --texto vaga.txt -o vaga.json
python scripts/aderencia.py vaga.json -o aderencia.md --json aderencia.json
python scripts/verificar_fatos.py curriculo.md --aderencia aderencia.json
python scripts/render.py curriculo.md --png
```

## 🗂️ Estrutura

| Caminho | Conteúdo |
| --- | --- |
| `SKILL.md` | A skill: gatilhos, regras invioláveis e fluxo em 5 etapas. |
| `references/` | Léxico de conceitos, glossário PT/EN, guia de ATS, modelos por posicionamento e idioma. |
| `scripts/` | Extração da vaga, aderência, verificador de fatos, render e empacotamento. |
| `assets/curriculo.typ` | Template do PDF. |
| `evals/` | Vagas de teste e juiz automático (`python evals/rodar_evals.py`). |
| `tests/` | Testes, incluindo currículos com fatos inventados que o verificador precisa reprovar. |
| `docs/` | Pesquisa e decisões de design. |

## 🔐 Privacidade

Currículos gerados (`historico/`, `evals/resultados/`) e o perfil-mestre **nunca são versionados**. Eles ficam no `.gitignore` e existem só na sua máquina.
