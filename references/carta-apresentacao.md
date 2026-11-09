# Carta de apresentação (só sob pedido)

Curta, específica e com as mesmas regras de fato do currículo. Até 250 palavras, no idioma da vaga, no mesmo posicionamento escolhido para o currículo.

## Estrutura (4 blocos)

1. **Abertura (1 a 2 frases):** a vaga pelo nome e por que esta empresa, citando algo concreto do anúncio (produto, domínio, stack). Nada de "venho por meio desta".
2. **Prova principal (2 a 3 frases):** o resultado mais forte do perfil para o requisito nº 1 da vaga, com a métrica (ex.: smoke de 1 h 30 min para 7 a 15 min; registro de bug −85%).
3. **Segunda prova ou ponte (2 frases):** o segundo requisito mais importante, ou a ponte para o domínio da empresa (ex.: fintech → experiência em crédito consignado na Função Sistemas).
4. **Fechamento (1 a 2 frases):** disponibilidade (remoto / Grande Recife), convite para conversar. Se houver uma lacuna óbvia que a vaga pede, pode reconhecê-la com o plano para cobri-la (sem prometer prazos).

## Formato para o verificador

```markdown
<!-- cv-tailoring · idioma: pt · tipo: carta · vaga: <cargo> · <empresa> -->
# Samuel V. Cordeiro
Recife, PE | (87) 99917-0472 | ssamuelkaka548@gmail.com | linkedin.com/in/samuelvcordeiro | github.com/yssamael

## Carta
Bloco 1. <!-- fonte: 4.1#4 -->

Bloco 2. <!-- fonte: 4.1#10, 11b#8 -->

Bloco 3. <!-- fonte: 4.2#2 -->

Bloco 4. <!-- fonte: 1#4 -->
```

Rode `python scripts/verificar_fatos.py carta.md` (sem `--aderencia`: a carta não precisa de 8 a 15 palavras-chave). Para PDF, `python scripts/render.py carta.md`.

## Não fazer

- Repetir o currículo em prosa.
- Elogios genéricos à empresa ("empresa líder e inovadora").
- Motivo de saída de empregos anteriores, salário, pretensão.
- Termos proibidos do perfil (as mesmas regras do SKILL.md).
- Na carta, Jira pode aparecer só como "ferramentas de gestão como Linear", nunca como experiência com Jira.
