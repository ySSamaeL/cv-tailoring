# Playbook de ATS e leitura humana

Regras que a skill aplica na etapa 3. Cada uma traz a fonte e o grau de confiança; o levantamento completo está em `docs/pesquisa.md`. Quando uma regra daqui conflitar com as regras invioláveis do SKILL.md (fatos), os fatos vencem.

## Para o software (ATS)

| # | Regra | Como a skill aplica | Fonte |
| --- | --- | --- | --- |
| 1 | **Termo exato da vaga.** Currículos com o título exato da vaga tiveram ~10,6× mais convites para entrevista. | Palavras-chave na forma do anúncio ("Playwright", "testes de API"), **só** quando o perfil tem a competência. Na dúvida entre formas, escreva as duas: "testes E2E (ponta a ponta)". | Jobscan, *ATS resume*, abr/2026 — https://www.jobscan.co/blog/ats-resume/ |
| 2 | **8 a 15 palavras-chave reais**, cada uma sustentada por um bullet e repetida em Habilidades. Sem keyword stuffing: o recrutador confere se há exemplo por trás. | O verificador conta as palavras-chave técnicas da vaga presentes (mínimo 8, aviso acima de 15) e reprova as sem cobertura. | Jobscan 2026; Gupy, *Como funciona a ordenação*, dez/2025 — https://www.gupy.io/blog-do-emprego/como-funciona-a-ordenacao-da-gupy |
| 3 | **Títulos de seção padrão:** Experience / Skills / Education; em PT, Experiência (Profissional) / Habilidades / Formação. | `references/modelos/idioma-pt.md` e `idioma-en.md`. | Jobscan 2026; Gupy 2025 (ranqueia pelos campos "Experiência" e "Habilidades") |
| 4 | **Uma coluna, sem tabelas, caixas de texto ou gráficos.** Duas colunas podem embaralhar o parser. | Template Typst de uma coluna; habilidades em linhas de texto, não em tabela. | Jobscan 2026; Ladders 2018 |
| 5 | **Nada essencial em cabeçalho/rodapé de página.** | Nome e contato ficam no corpo da página; o template não usa header/footer. | Conselho comum de ATS; *sem fonte primária encontrada* |
| 6 | **PDF com texto real** (nunca imagem) ou .docx; se o anúncio pedir formato, usar o pedido. | `render.py` confere que nome e e-mail aparecem no texto extraído do PDF. | Jobscan 2026 |
| 7 | **Autoteste:** copiar o texto do PDF para um editor simples; se cargo, datas ou habilidades saírem embaralhados, corrigir o layout. | Feito pelo `render.py` (extração com pypdf, ordem e acentos). | Blogs de 2025/2026 (secundário) |

## Para a pessoa (recrutador)

| # | Regra | Como a skill aplica | Fonte |
| --- | --- | --- | --- |
| 8 | **~7,4 s na primeira leitura.** Venceram layouts simples, títulos claros, leitura em F/E, cargos em negrito e conquistas em bullets; perderam poluição visual, frases longas e colunas. | Visual da referência: cargo em negrito, data à direita, bullets curtos. | Ladders, eye-tracking, via HR Dive, nov/2018 — https://www.hrdive.com/news/eye-tracking-study-shows-recruiters-look-at-resumes-for-7-seconds/541582/ |
| 9 | **O olho vai para: nome, cargo e empresa atuais, cargo e empresa anteriores, datas, formação.** | Headline logo abaixo do nome (`> Analista de QA · Playwright e TypeScript`), experiência atual primeiro e resultado numérico mais forte no 1º bullet. | Ladders 2012/2018 (lista de elementos do estudo de 2012, não reaberto); headline é inferência nossa |
| 10 | **Verbo de ação no início, resultado com número.** | Bullets começam com verbo no pretérito; comparativo antes → depois (nota da seção 11b do perfil). | Harvard Career Services, 2025 — https://careerservices.fas.harvard.edu/blog/2025/08/14/45-rare-action-verbs-for-your-resume-with-examples/ |
| 11 | **Fórmula XYZ:** "realizei X, medido por Y, fazendo Z". | Molde de reescrita dos bullets. | Laszlo Bock (Google), 2014; antiga, mas ainda muito citada |
| 12 | **Uma página para júnior.** | `render.py` falha acima de 1 página. | Guias de Harvard 2022–2024; *sem fonte primária de 2025/2026* |
| 13 | **Negrito com parcimônia:** 2 a 3 termos por bullet (termo da vaga e número). | Regra do formato canônico. | Prática editorial; ver regra 8 |

## Brasil: Gupy e LinkedIn

- **Gupy** (fontes oficiais, nov–dez/2025): agentes de IA comparam os **campos Experiência e Habilidades** do perfil do candidato com os requisitos e geram uma lista **ordenada**. Não eliminam ninguém; só as perguntas eliminatórias da empresa eliminam. A Gupy lê contexto, não só palavra exata, e ignora nome, CPF e e-mail. Ela recomenda preencher até 30 habilidades e descrever cada experiência com responsabilidades, entregas, ferramentas e resultados. **Consequência:** além do PDF, a skill entrega o texto para colar nesses campos (etapa 4). Fontes: https://www.gupy.io/blog-do-emprego/ia-da-gupy e o artigo de ordenação acima. Atenção: frases como "97% dos currículos são reprovados pela IA" circulam como marketing e **não foram verificadas**.
- **LinkedIn Easy Apply** envia o perfil do LinkedIn e, opcionalmente, o currículo anexado. Mantenha headline e Skills do LinkedIn coerentes com o currículo; o perfil-mestre já aponta que o LinkedIn atual está desatualizado (seção 12). Como o LinkedIn ranqueia candidatos **não foi confirmado** numa fonte de 2025/2026.

## O que a skill não faz, mesmo que "funcione" no ATS

- Texto branco escondido, lista de palavras-chave sem contexto, cópia de frases inteiras do anúncio.
- Título de cargo trocado para o da vaga (o cargo real fica; o alinhamento vai na headline e no resumo).
- Termo da vaga sem lastro no perfil, ainda que "só para passar no filtro".
