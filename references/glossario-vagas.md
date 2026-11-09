# Glossário de vagas: PT-BR ⇄ EN ⇄ perfil

Serve para traduzir o vocabulário do anúncio para o fato do perfil **sem mudar o fato**. A coluna "No perfil" diz o que sustenta o termo e como escrevê-lo; "lacuna" significa que o termo nunca vai para o currículo. A versão que os scripts leem é `conceitos.json` (mesmo conteúdo, estruturado).

## Cargos e senioridade

| Conceito | PT-BR | EN | No perfil / como usar |
| --- | --- | --- | --- |
| QA genérico | Analista de QA, Analista de Testes, Analista de Qualidade de Software, Testador | QA Analyst, Software Tester, Tester, QA Engineer | Cargo real: **Analista de QA** (EGB), **QA Tester Júnior** (Função Sistemas). "Analista de Qualidade" sozinho pode ser qualidade industrial: diga "de Software". |
| QA de automação | Analista de Automação de Testes, QA Automation | QA Automation Engineer, Test Automation Engineer, SDET | Não é o cargo dele: alinhar pela headline e pelo resumo (posicionamento 3.2), nunca trocando o título. SDET indica papel mais forte em código. |
| Engenharia de qualidade | Engenheiro(a) de Qualidade, Engenheiro(a) de Testes | Quality Engineer, Test Engineer, QE | Idem: o perfil diz "QA Analyst que opera como engenheiro de qualidade" (2#1). |
| Senioridade | Júnior/Jr, Pleno/Pl, Sênior/Sr, Estagiário, Trainee | Junior/Jr., Entry-level, Associate; Mid-level; Senior | Alvo: júnior. Pleno ≈ Mid-level (sem tradução direta). Sênior bloqueia. |

## Técnicas e processo de teste

| Conceito | PT-BR | EN | No perfil / como usar |
| --- | --- | --- | --- |
| Teste funcional | teste funcional, testes manuais, validação funcional | functional testing, manual testing | Cobre: 4.1#2, 4.2#2. |
| Regressão | (testes de) regressão | regression testing | Cobre: 8#1. |
| Smoke / sanity | smoke test, teste de fumaça, sanity | smoke testing, sanity testing | Cobre: 4.1#6, 4.1#10, 11b#8. Vagas em PT costumam manter o termo em inglês. |
| Ponta a ponta | E2E, ponta a ponta | end-to-end (E2E) | Cobre: 4.1#10. Escreva as duas formas: "testes E2E (ponta a ponta)". |
| Exploratório | teste exploratório | exploratory testing | Cobre: 8#1. |
| BDD / Gherkin | BDD, Gherkin, cenários Dado/Quando/Então | BDD, Gherkin, Given/When/Then | Cobre: 4.1#6. **Cucumber** (o runner) é lacuna. |
| TDD | TDD, desenvolvimento orientado a testes | TDD, test-driven development | Lacuna. |
| Shift-left | shift-left, qualidade desde o início | shift-left testing | Cobre: "em parceria com o time de desenvolvimento desde a concepção das soluções" (4.1#2). |
| Plano / estratégia | plano de testes, estratégia de testes | test plan, test strategy | Cobre: 4.1#6, 4.1#2; plano em 18 min (11b#4). |
| Caso / cenário | caso de teste, cenário de teste, roteiro | test case, test scenario, test script | Cobre: cenários positivos, negativos e de borda (4.1#2). |
| Requisitos | análise de requisitos, critérios de aceitação, regras de negócio | requirements analysis, acceptance criteria | Cobre: 4.1#2. |
| Baseado em risco | testes baseados em risco, análise de risco | risk-based testing | Cobre: 8#1. |
| Gestão de defeitos | gestão de defeitos, report/abertura de bugs, bug tracking | bug tracking, defect management, bug reporting | Cobre: boards do Linear e roteamento bug × incidente (4.1#7). |
| Incidentes | gestão de incidentes, post-mortem, causa raiz | incident management, post-mortem, root cause analysis | Cobre: post-mortem (4.1#6), 277 incidentes (4.1#7). "RCA" formal: escrever "post-mortem". |
| Homologação | homologação, ambiente de homologação (HML), validação com o negócio | UAT, staging validation, acceptance testing | Cobre: 4.1#19, 8#1. "Homologação" ≈ staging + UAT; traduza pelo contexto. |
| Produção | produção (PRD) | production | — |
| Release | teste de release, go-live | release testing | Cobre: releases do app (4.1#6). |
| Métricas | métricas de qualidade, indicadores, KPIs | quality metrics, KPIs | Cobre: métrica pré × pós-release (4.1#7), roadmap (4.1#23). |
| Documentação | documentação de testes, evidências, relatórios | test documentation, test reports | Cobre: 120 artefatos (4.1#6, 11b#12). |

## Automação, API, dados

| Conceito | PT-BR | EN | No perfil / como usar |
| --- | --- | --- | --- |
| Automação | automação de testes, testes automatizados | test automation, automated testing | Cobre: 4.1#10. |
| Playwright | Playwright | Playwright | Domínio (8#2). |
| Cypress / Selenium / Puppeteer | — | — | **Lacuna no currículo** (Cypress só avaliado). Na vaga "Playwright ou Cypress", escreva Playwright. |
| Page Objects | Page Objects, POM | Page Object Model | Cobre: 8#2. |
| Testes de API | testes de API, testes de integração | API testing, integration testing | Cobre: 4.2#2. Postman e Hurl (8#7). |
| Testes de contrato | testes de contrato | contract testing, Pact | Parcial (contrato OpenAPI, 4.1#13): não escrever "contract testing". |
| Testes de carga | testes de carga, performance, estresse | load, performance, stress testing; k6, JMeter, Gatling | **Lacuna.** "Equipe de Performance" é o nome do time, não teste de carga. |
| Mobile | testes mobile, em dispositivos | mobile testing | Cobre: app Android e web mobile (4.1#4), Maestro (4.1#18), Appium Inspector (8#11). iOS é lacuna. |
| CI/CD | CI/CD, integração/entrega contínua, pipelines | CI/CD, continuous integration/delivery | **Planejado** (4.1#23, 8#13). Só com "planejado"/"planned". GitHub Actions idem; Jenkins, GitLab CI etc. são lacuna. |
| Observabilidade | observabilidade, monitoramento, alertas | observability, monitoring, alerting | Cobre: Monitor 24/7 (4.1#12), v2 (4.1#13). |
| Monitoramento sintético | monitoramento sintético, checks sintéticos | synthetic monitoring, synthetic checks | Cobre: 8#4. Grafana, Datadog, New Relic são lacuna; Sentry é parcial (stack do freelance). |
| SQL | SQL, banco de dados, consultas | SQL, databases, queries | Cobre: validação em banco (4.2#2), Microsoft SQL Server, Postgres. MySQL, Oracle e NoSQL são lacuna. |
| Ferramenta de gestão | Jira, Azure DevOps, TestRail, Zephyr, Xray | same | **Lacuna no currículo.** Equivalente real: Linear (8#7). Xray e Zephyr são add-ons do Jira. |
| IA aplicada | agentes de IA, LLM, automação com IA | AI agents, LLM-based automation, AI-assisted testing | Cobre: 5 skills de Claude (4.1#15), executor Gherkin via Playwright MCP (4.1#16), MCP (8#6). |

## Frontend

| Conceito | PT-BR | EN | No perfil / como usar |
| --- | --- | --- | --- |
| React / Next.js / TypeScript | React, Next.js, TypeScript | same | Cobre: 4.3#4, 4.3#8, 4.1#11. |
| Tailwind | Tailwind (CSS) | Tailwind CSS | Parcial: usado no Mais Conhecimento (4.3#4), nível Familiar. Pode aparecer, sem adjetivo de domínio. |
| Componentes | componentização, componentes reutilizáveis, shadcn/ui, Radix, Material UI | component-based architecture, reusable components | Cobre: Radix/shadcn (4.3#4), Material-UI (4.3#7). |
| Design system | design system | design system | Cobre: painel de QA com design system documentado (4.1#11). |
| Figma | Figma, protótipos | Figma, prototyping | Cobre: protótipo do Figma → código (4.3#4). |
| Responsividade | responsividade, layout responsivo, mobile-first | responsive design | **Lacuna** (não há registro de implementação). |
| Acessibilidade | acessibilidade, a11y, WCAG | accessibility, a11y, WCAG | **Lacuna para web.** O projeto de Libras (4.5#2) é impacto social: cite pelo nome, sem "acessibilidade web". |
| Testes de frontend | testes unitários, Jest, Testing Library | unit tests, Jest, React Testing Library | **Lacuna** (Jest aparece só como stack de repositório mantido). |
| Backend de apoio | Node.js, Express, APIs REST | same | Cobre: 4.3#9, 4.3#10, 8#9. |

## Domínio

| Vaga diz | Escrever no currículo |
| --- | --- |
| apostas, apostas esportivas, casa de apostas, bets, betting, sportsbook, cassino | **iGaming** (sportsbook e cassino online são aceitos como subdomínio) |
| fintech, bancário, meios de pagamento, crédito | "aplicações para bancos e fintechs", "crédito consignado privado" (4.2#2); PIX e KYC (4.1#4) |
