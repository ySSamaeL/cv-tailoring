# Evals da skill cv-tailoring

Quatro vagas fictícias em `evals/vagas/`, escolhidas para exercitar os quatro caminhos da skill:

| Vaga | Por que existe | Resultado esperado |
| --- | --- | --- |
| (a) Analista de QA Júnior, PT-BR, híbrido em Recife | Caminho principal: testes manuais, API, SQL e Jira (que é lacuna) | Aplicar; Jira e ISTQB fora do currículo; posicionamento 3.1 |
| (b) QA Automation Engineer, EN, remoto | Inglês, Playwright ou Cypress, CI/CD (planejado, não rodando) | Aplicar; currículo em inglês; CI/CD só com "planned"; Cypress e Docker fora |
| (c) Desenvolvedor Frontend Júnior, PT-BR, remoto | Posicionamento de engenharia; responsividade, acessibilidade e Jest são lacunas | Aplicar; freelance GAM abre a Experiência; lacunas fora |
| (d) Analista de Testes Júnior, presencial em São Paulo, sem relocação | Bloqueio de localidade | **Não aplicar**; nenhum currículo gerado |

## Critérios objetivos de aprovação

1. **Análise antes do currículo:** `aderencia.md` existe com Bloqueios, tabela Requisitos × perfil e Recomendação (a skill para e espera o ok antes da etapa 3).
2. **Recomendação correta:** (a), (b) e (c) aplicar ou aplicar com ressalvas; (d) não aplicar.
3. **Zero termos proibidos:** apostas/betting, certificação, liderança de equipe de QA, INC-xxx, jargão de fatia, sênior, status da UFRPE.
4. **100% dos bullets e parágrafos com origem** no perfil-mestre, aprovados pelo verificador (origem, números, nomes próprios, escalada).
5. **8 a 15 palavras-chave técnicas da vaga** presentes, todas com cobertura real; nenhuma palavra-chave de lacuna.
6. **Uma página** no PDF renderizado.
7. **Idioma** do currículo igual ao da vaga.
8. **Verificador aprovado** (`verificar_fatos.py` sem nenhuma FALHA).

Além disso, `tests/test_skill.py` tem 23 currículos com fatos inventados que o verificador **tem de reprovar** (métrica inflada, Jira, Cypress, Docker, mentoria inventada, liderança de equipe de QA, apostas, CI/CD rodando, certificação, INC, host, UFRPE em andamento, ferramenta inexistente no perfil, idioma trocado, headline inflada...).

## Como rodar

```bash
python evals/rodar_evals.py              # julga os 4 evals e atualiza a tabela abaixo
python -m unittest discover -s tests -v  # testes positivos e negativos
```

Os currículos em `evals/resultados/<vaga>/curriculo.md` foram escritos seguindo o SKILL.md (etapas 1 a 3); o script só julga.

## Resultados

<!-- resultados:inicio -->
| Vaga | Análise antes do CV | Recomendação | Termos proibidos | Bullets com origem | Palavras-chave (8–15, todas cobertas) | Uma página | Idioma | Verificador |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| a-qa-analyst-jr-recife | ✅ | ✅ aplicar (94) | ✅ 0 | ✅ 13/13 | ✅ 15 | ✅ 1 (86%) | ✅ pt | ✅ |
| b-qa-automation-en-remote | ✅ | ✅ aplicar (88) | ✅ 0 | ✅ 13/13 | ✅ 15 | ✅ 1 (86%) | ✅ en | ✅ |
| c-frontend-jr-remoto | ✅ | ✅ aplicar (88) | ✅ 0 | ✅ 13/13 | ✅ 10 | ✅ 1 (86%) | ✅ pt | ✅ |
| d-qa-presencial-sao-paulo | ✅ | ✅ não aplicar (85) | n/a (sem currículo) | n/a | n/a | n/a | n/a | n/a |

**4 de 4 evals aprovados.**
<!-- resultados:fim -->
