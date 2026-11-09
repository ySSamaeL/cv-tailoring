# Design da skill cv-tailoring

Fase 2 do projeto. Parte da proposta original (`docs/origem/prompt-claude-code-cv-tailoring.md`) e ajusta o que a pesquisa (`docs/pesquisa.md`) mostrou. O princípio que guia tudo veio do sartor: **o modelo escolhe e reescreve; o código confere.** Tudo que pode ser aritmética ou busca (cobertura, números, termos proibidos, uma página) é script determinístico; o modelo fica com o julgamento (qual ângulo, qual bullet, qual palavra).

## Estrutura do repositório

```
cv-tailoring/
  SKILL.md                         gatilho, regras invioláveis, fluxo em 5 etapas, mapa de referências
  requirements.txt                 typst + pypdf (só o render precisa)
  references/
    perfil-mestre.md               fonte da verdade (intacto; a skill nunca edita)
    conceitos.json                 léxico: variantes PT/EN de vaga -> termo do perfil que prova cobertura   [novo]
    dicionario-en-pt.txt           ponte EN->PT para o verificador comparar bullets em inglês             [novo]
    glossario-vagas.md             equivalências PT/EN para humanos e para a reescrita
    ats-playbook.md                regras de ATS e de leitura humana, com fontes
    carta-apresentacao.md          estrutura da carta (sob pedido)
    checklist-manual.md            versão manual dos scripts, para Cowork sem execução de código           [novo]
    modelos/
      formato-canonico.md          a gramática do Markdown que render e verificador leem                   [novo]
      3.1 ... 3.5-*.md             um esqueleto por posicionamento: ordem, bullets por ID, habilidades
      idioma-pt.md, idioma-en.md   títulos de seção, datas, cargos e estilo por idioma
  scripts/
    _comum.py                      normalização, perfil em linhas com ID, léxico                          [novo]
    _curriculo.py                  parser do Markdown canônico (compartilhado)                            [novo]
    extrair_vaga.py                URL ou texto -> vaga.json
    aderencia.py                   vaga.json x perfil -> aderencia.md + aderencia.json
    verificar_fatos.py             curriculo.md -> aprovado/reprovado, linha a linha
    render.py                      curriculo.md -> PDF (Typst), auditoria de uma página, prévia PNG
  assets/curriculo.typ             template Typst de uma coluna                                           [novo]
  historico/vagas.md               uma linha por vaga; pastas <empresa>-<cargo>-<data>/ ao lado
  evals/
    vagas/                         4 anúncios (a, b, c e o bloqueio d)
    resultados/<vaga>/             saída da skill para cada eval
    rodar_evals.py                 juiz determinístico; escreve a tabela em checks.md                     [novo]
    checks.md                      critérios e resultados
  tests/test_skill.py              40 testes, 23 deles de fato inventado que tem de reprovar               [novo]
  docs/                            pesquisa.md, design.md, sugestoes-perfil.md, origem/
  README.md
```

### Mudanças em relação à proposta

| Mudança | Motivo |
| --- | --- |
| `conceitos.json` separado do glossário | O glossário é para humanos; os scripts precisam de dados estruturados com o termo do perfil que prova cada conceito. Um teste garante que todo termo de evidência existe no perfil. |
| IDs de fonte `seção#ordem` em todo bullet | Ideia central dos repositórios mais robustos (sartor, imprintcv, resumery): rastreabilidade vira checagem de pertencimento, não opinião. Como o perfil não pode ganhar IDs (fica intacto), o ID é derivado da posição da linha na seção. |
| Template em `assets/` e dados passados como JSON | Strings chegam ao Typst como dados, não como marcação: nenhum caractere do currículo (`#`, `$`, `_`, `@`) quebra a compilação. Evita a classe de bug de escape que o LaTeX tem (NullSpace). |
| `checklist-manual.md` | O Cowork pode não ter execução de código; a skill precisa funcionar degradada, dizendo que a verificação foi manual. |
| `tests/` com casos negativos | Um verificador que só vê currículos bons não prova nada. |
| `evals/rodar_evals.py` | Juiz reprodutível: os currículos são saída do modelo, mas a avaliação é código. |
| Perfil só em `references/` | Uma cópia só; a raiz não guarda outra versão que possa divergir. |

## Fluxo

```
vaga (link ou texto)
   │  extrair_vaga.py  ── URL falhou (login/JS)? ── pede texto colado
   ▼
vaga.json  ── Claude revisa campos e "revisar"
   │  aderencia.py
   ▼
aderencia.md  ── bloqueios → requisito × perfil (ID + trecho) → palavras-chave → recomendação
   │
   ■ PARA: espera o ok do usuário
   ▼
Claude escreve curriculo.md (molde do posicionamento + glossário + formato canônico, fonte em cada bullet)
   │  verificar_fatos.py  ── FALHA? corrige e repete
   │  render.py           ── > 1 página? corta por prioridade e repete
   ▼
Claude Code: historico/<empresa>-<cargo>-<data>/curriculo.{md,pdf}
Cowork:      Claude Doc com o mesmo Markdown
   │
   ▼
historico/vagas.md + até 3 sugestões para o perfil (nunca edita)
```

## Decisões de cada script

**extrair_vaga.py.** Heurístico e só com biblioteca padrão. Para URL: JSON-LD `JobPosting` quando existe (Greenhouse, Lever, muitos ATS), `__NEXT_DATA__` na Gupy, senão HTML → texto. **LinkedIn não é buscado**: os termos de uso (§8.2) e o robots.txt proíbem acesso automatizado, então o script sai com código 4 e a skill pede o texto colado. O mesmo código 4 vale para muro de login ou página com menos de 400 caracteres (padrão do resumery). Detecta idioma, senioridade, modelo de trabalho, cidade, relocação (ignorando negações), seções de obrigatórios/desejáveis e palavras-chave pelo léxico, preferindo a forma canônica quando o anúncio a usa.

**aderencia.py.** Para cada requisito, encontra os conceitos e procura a evidência no perfil por prioridade de seção (experiência > métricas > projetos > competências). Quando o requisito nomeia ferramentas ("Selenium ou Cypress"), elas pesam mais que o conceito genérico (automação), salvo "ou similar". Score = média ponderada (obrigatório 2, desejável 1; cobre 1, parcial 0,5), mostrado com a fórmula, nunca como verdade absoluta. Bloqueios: localidade, senioridade sênior, e dois ou mais obrigatórios sem cobertura (um só vira ressalva, porque anúncios listam "obrigatórios" generosamente).

**verificar_fatos.py.** Seis camadas: (1) fonte citada existe e se parece com o bullet (radicais de 5 letras + conceitos + números + ponte EN→PT, limiar 0,40 em PT e 0,25 em EN); sem citação, procura a melhor linha e exige mais; (2) todo número do bullet está nas linhas citadas (1.990 = 1,990; 27 mil = 27k; "três" = 3); (3) guarda de nomes próprios, siglas, CamelCase e termos com dígito, que precisam existir no perfil ou no léxico com cobertura; (4) termos proibidos do perfil e conceitos `no_cv` ou sem cobertura; (5) CI/CD só com qualificador; (6) escalada de alegação (liderei, mentorei, arquitetei, fundei, 1º lugar, 100%) exige o mesmo papel na fonte. Com `--aderencia`: idioma igual ao da vaga e 8 a 15 palavras-chave técnicas com cobertura.

**render.py.** Typst via pacote Python (sem binário, sem LaTeX). Escada curta de densidade (10,5 → 9,5 pt; nunca menos). Se não couber, falha e diz o que cortar; quem corta é o modelo, por prioridade do molde (a ordem de corte vem do sartor e da skill do Codex). Audita: páginas, texto extraível (nome e e-mail no texto do PDF, prova de leitura por ATS) e preenchimento (aviso abaixo de 85%, como no resumery).

## Visual

Uma coluna inspirada no currículo de referência que o Samuel enviou: nome em versalete centralizado, contato numa linha com separadores, títulos de seção em versalete com filete, cargo em negrito à esquerda e data à direita, organização em itálico com o local à direita, bullets compactos e habilidades em linhas rotuladas sem marcador. Fonte Libertinus Serif (embutida no Typst). Sem tabelas, colunas, ícones, cabeçalho ou rodapé de página.

## Limites conhecidos

- A semelhança lexical não entende sentido: um bullet pode citar a fonte certa e ainda distorcer o fato sem trocar número, nome nem verbo de papel. A camada de escalada cobre os casos mais comuns; o resto depende da revisão do modelo e do usuário. Por isso a etapa 3 pede para olhar o PNG e o texto antes de entregar.
- A extração de vaga é heurística; o JSON é sempre revisado pelo modelo.
- O léxico cobre QA e frontend. Vagas de outras áreas geram muitos requisitos "revisar", que o modelo julga à mão com evidência.
