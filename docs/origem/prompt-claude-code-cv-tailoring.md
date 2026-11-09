# Prompt para o Claude Code: criar o repositório e a skill `cv-tailoring`

> Cole tudo abaixo da linha como primeira mensagem de uma sessão do Claude Code aberta numa pasta vazia (ex.: `~/repos/cv-tailoring`). Antes, copie o `perfil-mestre.md` para essa pasta. Se tiver a skill `skill-creator` disponível, a sessão vai usá-la; se não, segue a especificação de Agent Skills descrita no prompt.

---

Você vai criar, neste repositório, uma skill de Claude chamada `cv-tailoring` que adapta o meu currículo a cada vaga de emprego que eu enviar. Trabalhe em três fases, na ordem: pesquisa, projeto, implementação com testes. Não pule a pesquisa. Ao final de cada fase, me mostre um resumo curto e espere meu ok antes de seguir.

## Contexto

- Eu sou QA Analyst (iGaming, automação Playwright/TypeScript, monitoramento, agentes de IA) buscando vagas de QA Analyst Júnior, QA Engineer, QA Automation/SDET e, eventualmente, desenvolvimento frontend. Aplico a vagas em português e em inglês.
- Já existe uma fonte da verdade: o arquivo `perfil-mestre.md`, que está na raiz desta pasta. Ele contém tudo que posso oferecer (experiências em formato Contexto → Ação → Resultado com tags, cinco posicionamentos de resumo profissional, skills por nível, soft skills com evidência, métricas medidas, regras do que não dizer, pendências e um histórico de vagas vazio). Leia-o inteiro antes de qualquer coisa. Ele é a única fonte permitida de fatos sobre mim. A skill nunca inventa, infla ou promove nível de skill por causa de uma vaga.
- A skill vai rodar em dois lugares: no Claude Code (saída em arquivo) e no Cowork/claude.ai (saída em Claude Docs). O SKILL.md precisa funcionar nos dois: o currículo é sempre gerado primeiro como Markdown canônico e só depois convertido para o formato do ambiente.
- Regras fixas que vêm do perfil e que a skill tem que respeitar sempre: usar "iGaming" e nunca "apostas" ou "betting"; não citar a situação da matrícula na UFRPE (listar só "Bacharelado em Sistemas de Informação, UFRPE, 2024" ou omitir); não chamar certificados de participação de certificação; não dizer que CI/CD está rodando; não dizer que liderei equipe de QA; manter nomes de incidentes, hosts e detalhes de infra do empregador fora do currículo; usar só métricas que estão na seção 11/11b do perfil.

## Fase 1: pesquisa (antes de escrever qualquer código)

Pesquise na web e, quando for repositório público, clone em `/tmp` e leia o código e os prompts. Quero que você aprenda com o que já existe em vez de reinventar. Pontos de partida obrigatórios:

1. **Repositórios de tailoring com agentes** (tópico `resume-tailoring` no GitHub). Em especial: `NullSpace-BitCradle/ats-resume-agent` (agente para Claude Code com saída LaTeX), `ledq/resumery` (agentes com "experience bank" e LaTeX), `GAaronZhao/Resume-Pilot` (workspace local com tailoring revisável), `vmlgtm/imprintcv` (verificação determinística de fatos e Typst), `tristanheilman/sartor` e `wyl000bdml-sys/CareerProof` (cada linha rastreável a uma experiência real), `devo-id/ResumeEngine` (perfil-mestre → currículo), `stevenha75/codex-resume-tailoring-skill` (skill com PDF de uma página verificado), `anshketchum/resumeop` (banco de experiências + RenderCV). Para cada um, anote: como extraem requisitos da vaga, como pontuam aderência, como impedem alucinação, como renderizam, o que vale copiar e o que não vale.
2. **Formatos e renderizadores de currículo**: RenderCV (YAML → PDF, bom para engenharia), JSON Resume (schema + temas), Reactive Resume, Typst. Decida qual usar como renderizador para o Claude Code e justifique. Critério: instalação simples, template limpo de uma coluna, bom para ATS, fácil de parametrizar por idioma.
3. **Boas práticas de ATS e de leitura humana**, com fontes de 2025/2026: correspondência por termo exato (se a vaga diz "Playwright", o currículo diz "Playwright", não "framework de automação"); 8 a 15 palavras-chave reais tecidas em bullets e numa seção de Skills, sem keyword stuffing; cabeçalhos de seção padrão (Experience, Skills, Education); uma coluna, sem tabelas nem sidebars; verbos de ação no início do bullet; resultado quantificado; uma página para perfil júnior. Registre também o que recrutadores de tecnologia olham nos primeiros segundos (cargo atual, empresa, stack, resultado mais forte).
4. **Vocabulário de vagas de QA e frontend em PT-BR e EN**: monte um glossário de termos equivalentes que as vagas usam (QA Analyst, Analista de Testes, Analista de Qualidade, Test Engineer, SDET, QA Automation, Quality Engineer; teste funcional, regressão, smoke, E2E, BDD, Gherkin, shift-left, test plan, test case, bug tracking, CI/CD, observability, etc.) para que a skill traduza o meu perfil para as palavras exatas de cada anúncio sem mudar o fato por trás.
5. **Especificação de Agent Skills** (SKILL.md com frontmatter `name` e `description`, corpo com até ~500 linhas, divulgação progressiva via pasta `references/`, `scripts/` para o que é determinístico). Se a skill `skill-creator` estiver disponível nesta sessão, use-a para estruturar, testar e otimizar a descrição de gatilho.

Entregue a fase 1 como `docs/pesquisa.md`: tabela comparativa dos repositórios, decisão de renderizador, lista de regras de ATS com fonte, glossário PT/EN e as 5 ideias que você vai adotar e as 3 que vai rejeitar, com motivo.

## Fase 2: projeto

Proponha, em `docs/design.md`, a estrutura do repositório e o fluxo da skill. Minha proposta inicial, ajuste com o que aprendeu na pesquisa:

```
cv-tailoring/
  SKILL.md                      gatilho, fluxo em etapas, regras, formatos de saída
  references/
    perfil-mestre.md            fonte da verdade (o arquivo que já está aqui)
    ats-playbook.md             regras de ATS e de leitura humana, com fontes
    glossario-vagas.md          equivalências PT/EN de termos de QA e frontend
    modelos/                    esqueleto de currículo por posicionamento (5) e por idioma (2)
    carta-apresentacao.md       estrutura de cover letter curta, se eu pedir
  scripts/
    extrair_vaga.py             URL ou texto → JSON com título, empresa, local, modelo de trabalho,
                                senioridade, obrigatórios, desejáveis, palavras-chave, idioma
    aderencia.py                JSON da vaga × perfil-mestre → tabela cobre/parcial/lacuna com evidência,
                                score e os três bloqueios (local, senioridade, obrigatório sem cobertura)
    verificar_fatos.py          cada bullet do currículo gerado → linha de origem no perfil-mestre;
                                falha se algum bullet não tiver origem ou se contiver termos proibidos
    render.py                   Markdown canônico → formato do renderizador escolhido → PDF
  historico/
    vagas.md                    uma linha por vaga adaptada (data, empresa, ângulo, score, resultado)
    <empresa>-<cargo>-<data>/   vaga original, análise de aderência, currículo .md e .pdf
  evals/
    vagas/                      3 anúncios reais ou realistas (ver fase 3)
    checks.md                   critérios objetivos de aprovação
  README.md                     instalação no Claude Code e no Cowork, uso, manutenção do perfil
```

Fluxo da skill, em etapas com parada para aprovação:

1. **Entrada**: eu colo o texto da vaga ou um link. A skill detecta o idioma e extrai os campos (script ou leitura direta quando o script não der conta).
2. **Análise de aderência** (sempre antes do currículo): tabela do que a vaga pede × o que o perfil cobre, com a evidência exata (qual bullet, qual métrica), marcando cobre / parcial / lacuna. Primeiro checa os três bloqueios: localidade e modelo de trabalho (remoto em qualquer lugar; presencial ou híbrido só na Grande Recife; outra cidade só com relocação custeada), senioridade (alvo júnior, mas não descartar "QA Analyst" sem nível ou pleno quando o escopo couber: sinalizar, não vetar) e requisito obrigatório sem nenhuma cobertura. Termina com recomendação: aplicar, aplicar com ressalvas, não aplicar. Para e espera meu ok.
3. **Currículo**: escolhe um dos cinco posicionamentos da seção 3 do perfil, reordena seções pelo que a vaga valoriza, seleciona os bullets por tag e aderência, reescreve usando as palavras exatas do anúncio (via glossário) sem mudar o fato, limita a uma página, escreve no idioma da vaga, inclui seção de Skills com as 8 a 15 palavras-chave que eu de fato tenho. Roda `verificar_fatos.py`. No Claude Code, gera `.md` e `.pdf`; no Cowork, cria um Claude Doc a partir do mesmo `.md`.
4. **Extras sob pedido**: carta de apresentação curta no mesmo ângulo; lista de perguntas prováveis de entrevista com a resposta-base apontando para o bullet do perfil.
5. **Registro**: adiciona a linha em `historico/vagas.md`, salva a pasta da vaga, e sugere no máximo 3 enriquecimentos para o perfil-mestre se a vaga revelou algo que eu tenho mas não está escrito (nunca edita o perfil sozinha; propõe).

Regras do SKILL.md que não são negociáveis: nenhum fato fora do perfil-mestre; toda métrica rastreável à seção 11/11b; palavras exatas da vaga só quando a competência existir; termos proibidos ("apostas", "betting", status da UFRPE, "certificação" para participação, "liderei equipe de QA", nomes de INC, hosts); se a vaga pedir algo que não tenho (ISTQB, Cypress em produção, Java), vai para a coluna de lacuna da análise, nunca para o currículo; tailoring moderado, sem copiar frases inteiras do anúncio.

## Fase 3: implementação e testes

1. Implemente a estrutura aprovada. Scripts em Python 3 com dependências mínimas e `uv`/`requirements.txt`. O `verificar_fatos.py` tem que ser determinístico: compara cada bullet gerado com as linhas do perfil por similaridade e por sobreposição de números e termos, e falha explicitamente listando o bullet sem origem.
2. Escreva três anúncios de teste em `evals/vagas/`, realistas e diferentes entre si: (a) QA Analyst Júnior, PT-BR, híbrido em Recife, pede testes manuais, API, SQL e Jira; (b) QA Automation Engineer, EN, remoto, pede Playwright ou Cypress, TypeScript, CI/CD e inglês; (c) Desenvolvedor Frontend Júnior, PT-BR, remoto, pede React, Next.js, Tailwind e Figma. Inclua uma quarta de bloqueio: presencial em São Paulo sem relocação, para provar que a análise recomenda não aplicar.
3. Rode a skill nas quatro vagas e verifique em `evals/checks.md`: zero ocorrências de termos proibidos; 100% dos bullets com origem no perfil; 8 a 15 palavras-chave da vaga presentes e todas com cobertura real; uma página; idioma correto; análise de aderência entregue antes do currículo; o caso de São Paulo recomendando não aplicar. Mostre os resultados numa tabela.
4. README com: como instalar no Claude Code (pasta em `~/.claude/skills/cv-tailoring` ou symlink) e no Cowork (zipar e enviar como skill pessoal); como usar ("cole a vaga e peça o currículo"); como manter o perfil-mestre (toda nova conquista entra lá primeiro, nunca direto no currículo); como atualizar o histórico.
5. Commits pequenos com Conventional Commits. Não faça push sem eu pedir.

## O que eu espero ver ao final

Um repositório pronto para uso, com a skill instalável nos dois ambientes, os três documentos (`pesquisa.md`, `design.md`, `README.md`), os quatro evals passando e o `perfil-mestre.md` intacto em `references/` (você não altera o conteúdo dele; se achar erro ou lacuna, lista em `docs/sugestoes-perfil.md`).

Comece pela fase 1 e me mostre o `docs/pesquisa.md` antes de seguir.
