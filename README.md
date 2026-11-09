# cv-tailoring

Skill do Claude que lê uma vaga (link do LinkedIn, Gupy, site da empresa ou texto colado) e adapta o currículo do Samuel a ela, **usando só fatos do perfil-mestre**. Antes de escrever qualquer currículo, ela faz uma análise de aderência com evidência e para para você aprovar. Depois gera um currículo de uma página, confere cada linha contra o perfil e entrega PDF (Claude Code) ou Claude Doc (Cowork).

```
vaga ──► análise de aderência ──► [você aprova] ──► currículo .md ──► verificador ──► PDF / Claude Doc ──► histórico
```

## O que tem aqui

| Pasta | Conteúdo |
| --- | --- |
| `SKILL.md` | A skill: gatilho, regras invioláveis, fluxo em 5 etapas. |
| `references/perfil-mestre.md` | **A fonte da verdade.** Tudo que pode ir para um currículo. |
| `references/` | Léxico de conceitos, glossário PT/EN, playbook de ATS, modelos por posicionamento e idioma, carta, checklist manual. |
| `scripts/` | `extrair_vaga.py`, `aderencia.py`, `verificar_fatos.py`, `render.py`, `empacotar.py`. |
| `assets/curriculo.typ` | Template do PDF (uma coluna, ATS-friendly). |
| `historico/` | Uma linha por vaga em `vagas.md` e uma pasta por candidatura. |
| `evals/` | 4 vagas de teste, juiz automático e resultados. |
| `tests/` | 40 testes, 23 deles com fatos inventados que o verificador tem de reprovar. |
| `docs/` | Pesquisa (fase 1), design (fase 2), sugestões para o perfil. |

## Instalação

Requisitos: Python 3.11+ e duas dependências.

```bash
pip install -r requirements.txt     # typst e pypdf; não precisa de LaTeX nem do binário do Typst
python -m unittest discover -s tests
```

### Claude Code

O Claude Code carrega skills pessoais de `~/.claude/skills/<nome>/`. Para editar o repositório e a skill ver as mudanças na hora, crie um link para esta pasta em vez de copiar.

Windows (PowerShell; *junction* não exige administrador):

```powershell
New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\cv-tailoring" -Target "C:\Users\ssamu\OneDrive\Desktop\repos\cv-tailoring"
```

macOS / Linux:

```bash
ln -s ~/repos/cv-tailoring ~/.claude/skills/cv-tailoring
```

Abra uma sessão nova do Claude Code e confira com `/skills` que `cv-tailoring` aparece. Com o link, o histórico das vagas é gravado dentro deste repositório.

### Cowork / claude.ai

```bash
python scripts/empacotar.py          # gera dist/cv-tailoring.zip
```

Em claude.ai: **Settings → Capabilities → Skills → Upload skill** (em português, Configurações → Capacidades), e escolha `dist/cv-tailoring.zip`. Precisa de plano pago com execução de código ativada. O zip já vem com a pasta `cv-tailoring/` na raiz, como o upload exige. O zip leva `SKILL.md`, `references/` (com o perfil-mestre), `scripts/` e `assets/`. Não leva histórico, evals, testes nem docs. Lá, o currículo sai como Claude Doc; se o ambiente tiver execução de código, a skill roda os mesmos scripts, senão segue `references/checklist-manual.md`. **Reenvie o zip sempre que mudar o perfil-mestre**, porque a cópia do Cowork não se atualiza sozinha.

## Como usar

Cole a vaga e peça o currículo:

> Adapta meu currículo para esta vaga: https://www.linkedin.com/jobs/view/1234567890/

> Vale a pena aplicar? [texto da vaga colado]

> Tailor my resume for this job: [texto em inglês]

1. **Link do LinkedIn:** a skill **não** abre o link: os termos de uso do LinkedIn (§8.2) e o robots.txt proíbem acesso automatizado, mesmo à página pública, e insistir põe sua conta em risco. Ela pede que você abra a vaga no navegador, selecione todo o texto e cole. Links da Gupy, Greenhouse, Lever e páginas de carreira são lidos direto; se a página não entregar o anúncio, ela também pede o texto.
2. **Análise de aderência:** bloqueios (localidade, senioridade, obrigatório sem cobertura), tabela requisito × perfil com a evidência exata, palavras-chave que entram e as que ficam de fora, recomendação e score. **Ela para aqui** até você dizer "ok" (ou trocar o posicionamento).
3. **Currículo:** escolhe um dos cinco posicionamentos, seleciona e reescreve os bullets com o vocabulário da vaga, passa no verificador e renderiza uma página. No Claude Code: `historico/<empresa>-<cargo>-<data>/curriculo.pdf`.
4. **Extras sob pedido:** "faz a carta também", "que perguntas podem cair na entrevista?", "me dá o texto para os campos da Gupy" (a Gupy ranqueia pelos campos Experiência e Habilidades, não pelo PDF).
5. **Registro:** a linha em `historico/vagas.md` e até 3 sugestões para o perfil.

Os scripts também rodam sozinhos:

```bash
python scripts/extrair_vaga.py --texto vaga.txt -o vaga.json
python scripts/aderencia.py vaga.json -o aderencia.md --json aderencia.json
python scripts/verificar_fatos.py curriculo.md --aderencia aderencia.json
python scripts/render.py curriculo.md --png
```

## Como manter o perfil-mestre

- **Toda conquista nova entra primeiro no perfil**, nunca direto no currículo: mesmo formato (Contexto → Ação → Resultado + tags), na seção certa. Métrica nova só depois de medida, com fonte na 11b.
- Se você inserir linhas no meio de uma seção, os IDs (`4.1#10`) daquela seção mudam. Os currículos já gerados não quebram (estão prontos), mas, para regenerar um antigo, rode o verificador de novo: ele aponta fonte inexistente ou pouco parecida.
- Ferramenta nova (ex.: começou a usar Jira): acrescente no perfil **e** confira `references/conceitos.json`. Se o conceito tem `"no_cv": true`, troque para `false` e ponha o termo do perfil em `"cobre"`. `python -m unittest discover -s tests` confere se todo termo de evidência existe no perfil.
- Depois de mudar o perfil, rode `python evals/rodar_evals.py` para ver se os quatro evals continuam passando. No Cowork, reenvie o zip.
- Sugestões que a skill encontrou até agora: `docs/sugestoes-perfil.md`.

## Como atualizar o histórico

`historico/vagas.md` tem uma linha por candidatura. A skill preenche data, empresa, vaga, ângulo, score e recomendação; a coluna **Resultado** é sua: `enviado`, `entrevista`, `recusado`, `proposta`. Quando algo der certo ou errado, anote o aprendizado; se ele revelar algo seu que não está no perfil, leve para o perfil.

## Privacidade

O perfil-mestre e o histórico têm dados pessoais (e-mail, empregadores, candidaturas). Mantenha este repositório **privado**; não faça push para um remoto público. O currículo de referência de terceiros (`curriculo meu amigo referencia.pdf`) está no `.gitignore` e não é versionado.
