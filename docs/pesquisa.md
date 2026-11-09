# Fase 1 · Pesquisa

Levantamento feito em 22/10/2026. Foram 13 repositórios clonados e lidos (sem executar o código deles), a documentação de renderizadores e da especificação de Agent Skills, fontes de ATS de 2025/2026 e testes ao vivo das páginas de vaga do LinkedIn e da Gupy.

## 1. Repositórios de tailoring com agentes

Os nove repositórios pedidos existem e são públicos. O `devo-id/ResumeEngine` só tem documentação de arquitetura, sem código. Também entraram os mais estrelados do tópico `resume-tailoring`.

| Repositório | Como lê a vaga | Como pontua aderência | Como impede alucinação | Como renderiza / uma página |
| --- | --- | --- | --- | --- |
| **vmlgtm/imprintcv** (TS, CLI + MCP + skill) | Regex sobre tabela de aliases + lista de ~40 termos | `cobertos/skills_da_vaga × 100`; ≥75 forte, ≥45 moderado; separa coberto / existe no cofre / lacuna real | **Determinístico em 5 camadas:** datas, empresa e cargo exatos; números e período inalterados; `sourceBulletIds` existentes e do mesmo emprego; regex de escalada ("zero downtime", "VP of", "led N"); 3 tentativas de reparo e depois volta ao bullet original | Typst; escada de 7 degraus de fonte e margem, depois encurta e por fim remove bullets |
| **tristanheilman/sartor** (TS, plugin do Claude) | "Pistas" por regex; JSON de Greenhouse/Lever/Ashby | **Sem score, de propósito**: termo presente / no perfil / ausente | O LLM devolve só **um plano de IDs**; guarda léxica confere todo número e nome próprio contra o vocabulário do perfil | react-pdf/docx a partir do plano; `fit.ts` corta bullets por ordem fixa até caber |
| **stevenha75/codex-resume-tailoring-skill** | Prompt: P0/P1/P2/Lacunas | Qualitativo | Regras de prompt + `--fact-locks` opcional (números permitidos, frases proibidas) | JSON → HTML/Playwright → PDF; **falha em overflow**; `audit_resume.py` exige 1 página e última linha entre 20 e 75 pt da borda |
| **ledq/resumery** (Claude Code: agentes + hooks) | Agente `jd-parse` → `parsed_jd.json` com grafia exata | Rubrica de 9 dimensões; veracidade é porteira | Avaliador "frio" + re-verificador; empresa, cargo e datas vêm só de `profile.json`; cargos de uma lista permitida | LaTeX (template Jake); hook confere compilação, ≤1 página e **preenchimento ≥85%** |
| **NullSpace-BitCradle/ats-resume-agent** | Prompt | Nenhum | `validate.ts` sem LLM: números, datas, certificações e skills precisam existir no arquivo mestre **na mesma seção** | LaTeX com preâmbulo travado |
| **wyl000bdml-sys/CareerProof** (skill) | Prompt → YAML `must_have/nice_to_have` | 0–100 + aplicar/talvez/pular | Só prompt: rótulos direto / transferível / sem suporte; nível de confidencialidade por métrica | Sem render (MD/DOCX opcional) |
| **GAaronZhao/Resume-Pilot** (Next.js) | LLM → `JobInsight` | Nenhum | Prompt + saída limitada a reescrever/reordenar IDs fixos; usuário aceita cada mudança | react-pdf + controles manuais |
| **anshketchum/resumeop** (Python, 2024) | Prompts | Embeddings (Qdrant), limiar 0,65 | Fraco: o prompt pede para "quantificar com números e valores" | RenderCV |
| **devo-id/ResumeEngine** | Texto colado | LLM instruído a "dar notas baixas por padrão" | Só prompt; remove contato antes de mandar ao modelo | Puppeteer + Handlebars |
| **vesaias/JobNavigator** | Scrapers; LinkedIn com Playwright logado | Rubrica 5 × 20 + mapeamento de requisitos | Só prompt, e `suggested_bullets` **pode inventar métricas** | DOCX/PDF |
| **low-hands/MyCareer** | Requisitos em níveis S/A/B/C, fato × inferência | S faltando → fraco; >50% incerto → evidência insuficiente | **Cada match cita trecho literal do CV**; trecho não confere → "incerto" | n/a |
| **Matthew-J-Lew/resume-tailor-app** | LLM | Nenhum | "Avoid fabrication" no prompt | LLM edita LaTeX; uma página fica a cargo do prompt |
| **crewAI (curso, L7)** | ScrapeWebsiteTool na URL | Nenhum | Só prompt | Markdown |

**Leitura de LinkedIn nesses projetos:** o sartor se recusa a raspar LinkedIn/Indeed/Workday e cai para JSON público, depois extensão, depois texto colado ("which always works"). O resumery tenta 4 vezes e, com menos de 200 caracteres ou muro de login, sai com código 4 e pede o texto. O JobNavigator usa Playwright logado com cookies, o que funciona mas é frágil e viola os termos.

## 2. Renderizador

| Opção | Estado (verificado) | Instalação no Windows / Py 3.14 | Template de uma coluna | Texto extraível (ATS) | PT/EN | Contagem de páginas |
| --- | --- | --- | --- | --- | --- | --- |
| **RenderCV** | v2.8 (mar/2026), Python ≥3.12, Typst via extra `[full]` | `pip install "rendercv[full]"` | Sim (tema `engineeringresumes`) | Sim | Campo `locale`; "portuguese" listado por terceiros, **não confirmado** | Não nativo |
| **`typst` (PyPI)** | v0.15.0 (jun/2026), roda em CPython 3.8+ (inclusive 3.14), sem binário separado | `pip install typst` | Template próprio | Sim (suporta PDF/A e PDF/UA) | `sys_inputs` com JSON | pypdf |
| **JSON Resume** | Schema + temas comunitários | Node + navegador headless | Depende do tema | Em geral sim | Rótulos fixos no tema | Não nativo |
| **Reactive Resume** | App web (Docker ou online) | Não é scriptável por skill | Sim | Sim | Pela interface | Pela interface |

**Decisão: pacote `typst` do PyPI com template próprio (`assets/curriculo.typ`).** Motivos:
- É um único wheel sem dependências que já funciona no Python 3.14 desta máquina. O RenderCV traria pydantic, ruamel, Jinja e um pacote de fontes.
- O currículo chega ao template como **dados JSON** (`sys_inputs`), não como marcação. Nenhum caractere do texto quebra a compilação, que é o bug clássico de escape do LaTeX (no LaTeX, um `%` solto apaga o resto da linha).
- O idioma fica no próprio Markdown (títulos de seção e datas já localizados), sem depender do locale não confirmado do RenderCV.
- Controle total do visual. O layout segue o currículo de referência enviado: uma coluna, nome em versalete, filetes, datas à direita.
- A auditoria usa pypdf: contagem de páginas, texto extraível e preenchimento.

Plano B, se algum dia faltar o pacote `typst`: `rendercv[full]` com o tema `engineeringresumes`.

## 3. Regras de ATS e de leitura humana

As 13 regras, com fonte e grau de confiança, estão em `references/ats-playbook.md`. O essencial:
- **Termo exato:** currículos com o título exato da vaga tiveram ~10,6× mais entrevistas (Jobscan, abr/2026).
- **8 a 15 palavras-chave reais**, sustentadas por bullets e repetidas em Habilidades, sem stuffing (Jobscan 2026; Gupy dez/2025).
- **Cabeçalhos padrão, uma coluna, nada em header/footer, PDF com texto real** (Jobscan 2026).
- **Verbo de ação + resultado numérico** (Harvard Career Services 2025; fórmula XYZ do Google).
- **Uma página para júnior** (guias de Harvard 2022–2024; não achei fonte primária de 2025/2026).
- **Primeiros ~7,4 s:** o recrutador olha cargo e empresa atuais, o anterior, datas e formação. Venceram layouts simples com cargos em negrito (Ladders, via HR Dive, 2018). Daí a headline abaixo do nome e o resultado mais forte no primeiro bullet.
- **Gupy:** ranqueia pelos **campos** Experiência e Habilidades, não pelo PDF, e só elimina por perguntas da empresa (fontes oficiais, nov–dez/2025). Daí o extra "texto para os campos da Gupy".

## 4. Glossário PT/EN

Está em `references/glossario-vagas.md`, para humanos: cargos, senioridade, técnicas, automação, frontend e domínio, cada termo ligado à evidência no perfil ou marcado como lacuna. A versão estruturada, lida pelos scripts, é `references/conceitos.json`, com 103 conceitos.

## 5. Especificação de Agent Skills

- **Frontmatter:** `name` e `description` são obrigatórios. `name` tem até 64 caracteres, só minúsculas, números e hífen, e não pode conter "anthropic" nem "claude"; `cv-tailoring` é válido. `description` tem até 1.024 caracteres e não pode ter tags XML. Para o upload no claude.ai, o frontmatter aceita só `name`, `description`, `license`, `compatibility`, `metadata` e `allowed-tools`. Por isso o SKILL.md usa só `name` e `description`, e funciona nos dois ambientes.
- **Corpo:** até ~500 linhas, com detalhes em arquivos de um nível (`references/`). Scripts rodam sem carregar no contexto. No Claude Code, a pasta da skill é `${CLAUDE_SKILL_DIR}`.
- **Instalação:** Claude Code em `~/.claude/skills/cv-tailoring/`. claude.ai em Settings → Capabilities → Skills → Upload skill, com um zip que contém a pasta `cv-tailoring/` (não o SKILL.md solto). Exige plano pago e execução de código. Skills não sincronizam entre claude.ai, API e Claude Code.
- Fontes: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview, https://code.claude.com/docs/en/skills, https://support.claude.com/en/articles/12512198-creating-custom-skills
- A `skill-creator` estava disponível na sessão, mas **não foi usada**: a estrutura seguiu a especificação acima, e os testes vieram dos evals próprios (`evals/`) e da suíte negativa (`tests/`). Ainda falta usar o ciclo de avaliação de gatilho dela para otimizar o campo `description`.

## 6. Páginas de vaga: LinkedIn e Gupy

- **LinkedIn** (testado deslogado em 22/10/2026): `/jobs/view/<id>` e a API "guest" devolvem 200 com a descrição. Mas o **User Agreement (§8.2, vigente desde 03/11/2025)** proíbe "software, scripts, robots… to scrape or copy the Services" e "bots or other unauthorized automated methods". O robots.txt bloqueia `/jobs-guest/` e exige permissão expressa para acesso automatizado. **Decisão:** a skill não busca links do LinkedIn. Pede o texto colado e usa o ID só para nomear a pasta.
- **Gupy:** páginas públicas em Next.js. A descrição fica no JSON `__NEXT_DATA__`, sem JSON-LD `JobPosting` na página testada. O `extrair_vaga.py` lê esse JSON. Os termos de uso da Gupy não foram revisados; como é uma busca única de um link que o próprio usuário enviou, o risco é baixo, e o texto colado continua sendo o plano B.

## 7. O que adotar e o que rejeitar

### 5 ideias adotadas

1. **O modelo planeja, o código confere** (sartor, imprintcv). Cada bullet cita `<!-- fonte: 4.1#10 -->` (ID derivado da posição no perfil, que não pode ser editado). Rastreabilidade vira uma checagem de pertencimento, não uma opinião.
2. **Verificador determinístico em camadas** (imprintcv, NullSpace, sartor): fonte existe e se parece com o bullet; todo número está na fonte; nomes próprios e siglas com lastro; escalada de alegação ("liderei", "mentorei", "arquitetei"); termos proibidos do perfil.
3. **Uma página decidida por código** (codex skill, resumery, sartor): escada curta de densidade (mínimo 9,5 pt), falha explícita, ordem de corte fixa (nunca uma experiência inteira) e aviso de preenchimento abaixo de 85%.
4. **Aderência com evidência literal** (MyCareer, CareerProof): cada requisito recebe cobre / parcial / lacuna com ID e trecho do perfil. Requisito sem conceito reconhecido fica "revisar", nunca "coberto". O score mostra a fórmula.
5. **Entrada robusta e segura** (resumery, sartor): JSON-LD e `__NEXT_DATA__` quando existem, código 4 e texto colado quando não, LinkedIn nunca buscado, e o texto da vaga tratado como dado (instruções embutidas no anúncio são ignoradas).

### 3 ideias rejeitadas

1. **Bullets "plausíveis" com métricas inventadas** (JobNavigator) e "quantifique tudo com números" (resumeop). Contradizem a regra nº 1; mesmo com revisão humana, normalizam a invenção.
2. **Confiar só no prompt para veracidade ou tamanho** (CareerProof, ResumeEngine, resume-tailor-app, crewAI). O sartor documenta o modelo ignorando "~6 bullets" e devolvendo 25 bullets em 3 páginas.
3. **Raspagem logada do LinkedIn ou proxy** (JobNavigator, crewAI). Frágil, contra os termos de uso e arriscado para a conta do usuário. O texto colado cobre ~100% dos casos.

Também ficaram de fora: LaTeX como formato canônico (bugs de escape) e o score 0–100 com rótulo "STRONG_FIT" sem explicação (falsa precisão). O score daqui mostra pesos e fórmula.
