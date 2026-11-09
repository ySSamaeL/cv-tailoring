# Formato canônico do currículo (Markdown)

Todo currículo nasce neste formato. Ele é lido por `scripts/render.py` (PDF) e por
`scripts/verificar_fatos.py` (checagem de fatos), e é colado tal qual num Claude Doc
no Cowork. Não invente marcação nova: o parser só entende o que está aqui.

```markdown
<!-- cv-tailoring · idioma: pt · posicionamento: 3.1 · vaga: <cargo> · <empresa> -->
# Samuel V. Cordeiro
> Analista de QA · Playwright e TypeScript · iGaming
Recife, PE | (87) 99917-0472 | ssamuelkaka548@gmail.com | linkedin.com/in/samuelvcordeiro | github.com/yssamael

## Resumo
Duas a quatro frases. <!-- fonte: 2#1, 11#1, 4.1#7 -->

## Experiência Profissional

### Analista de QA | abr 2026 – atual
Grupo Esportes Gaming Brasil (Grupo EGB) | Recife, PE
- Verbo no passado + o que fez + resultado, com **termo exato da vaga** em negrito. <!-- fonte: 4.1#10, 11b#8 -->

## Projetos e Premiações

### Hackathon EDScript (Grupo EGB): 1º lugar | 2026
- Uma linha de contexto e resultado. <!-- fonte: 5#2 -->

## Formação

### Tecnólogo em Análise e Desenvolvimento de Sistemas | ago 2026 – dez 2028 (previsão)
CESAR School | Recife, PE

## Habilidades
- **Testes**: termo, termo, termo
- **Ferramentas**: termo, termo
- **Idiomas**: Português (nativo), Inglês (avançado)
```

## Regras do formato

| Elemento | Sintaxe | Observação |
| --- | --- | --- |
| Metadados | `<!-- cv-tailoring · idioma: pt|en · ... -->` na 1ª linha | `idioma` define hifenização e é conferido pelo verificador. |
| Nome | `# Nome` | Sempre "Samuel V. Cordeiro". |
| Headline | `> Cargo · termo · termo` logo abaixo do nome | Cargo real do perfil + 2 ou 3 termos da vaga com cobertura, separados por ` · `. Cada termo é checado como habilidade. |
| Contato | linha logo abaixo do nome, itens separados por ` \| ` | Ordem: cidade, telefone, e-mail, LinkedIn, GitHub. E-mail, LinkedIn e GitHub viram links sozinhos. Em inglês: `Recife, Brazil` e telefone `+55 87 99917-0472`. |
| Seção | `## Título` | Use os títulos padrão do idioma (ver `idioma-pt.md` / `idioma-en.md`). |
| Entrada | `### Cargo ou título \| data` e, na linha seguinte, `Organização \| Local` | A data fica à direita. A 2ª linha é opcional (projetos não precisam). |
| Bullet | `- texto <!-- fonte: ID, ID -->` | Todo bullet cita a(s) linha(s) do perfil. Sem citação o verificador tenta achar sozinho e exige semelhança maior. |
| Parágrafo | linhas soltas dentro da seção | Usado no Resumo. Também cita fontes. |
| Habilidades | `- **Rótulo**: item, item` | Vira linha rotulada sem marcador, como na referência. Cada item precisa existir no perfil ou no léxico com cobertura. |
| Negrito / itálico / link | `**x**`, `*x*`, `[x](url)` | Negrito só nos termos da vaga e nos números de resultado: no máximo 2 ou 3 por bullet. |

## IDs de fonte

`<seção>#<ordem>`: a ordem da linha dentro da seção do perfil-mestre, contando só
linhas com conteúdo (cabeçalhos e separadores de tabela não contam). Exemplos:
`4.1#10` (bullet do repositório de automação), `11b#8` (métrica do smoke).
Para listar os IDs:

```bash
python scripts/aderencia.py vaga.json            # a tabela já traz o ID de cada evidência
python -c "import sys; sys.path.insert(0,'scripts'); from _comum import carregar_perfil; [print(l.id, l.texto[:100]) for l in carregar_perfil().linhas]"
```

Também vale `L85` (número da linha no arquivo), mas os IDs de seção são mais estáveis quando o perfil cresce.
