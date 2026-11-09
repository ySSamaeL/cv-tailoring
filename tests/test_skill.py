"""Testes dos scripts da skill. Rodar com: python -m unittest discover -s tests -v

A maior parte são casos negativos: currículos com fatos inventados que o
verificador TEM de reprovar. Se algum destes passar, a skill pode alucinar.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from _comum import carregar_conceitos, carregar_perfil, contem_termo, numeros  # noqa: E402
from aderencia import analisar  # noqa: E402
from extrair_vaga import extrair  # noqa: E402
from verificar_fatos import verificar  # noqa: E402

PERFIL = carregar_perfil()
CABECALHO_PT = "<!-- cv-tailoring · idioma: pt -->\n# Samuel V. Cordeiro\nRecife, PE | ssamuelkaka548@gmail.com\n\n"
CABECALHO_EN = "<!-- cv-tailoring · idioma: en -->\n# Samuel V. Cordeiro\nRecife, Brazil | ssamuelkaka548@gmail.com\n\n"
ENTRADA_PT = "## Experiência Profissional\n\n### Analista de QA | abr 2026 – atual\nGrupo Esportes Gaming Brasil (Grupo EGB) | Recife, PE\n"
ENTRADA_EN = "## Experience\n\n### QA Analyst | Apr 2026 – Present\nGrupo Esportes Gaming Brasil (Grupo EGB) | Recife, Brazil\n"


def cv_pt(*bullets: str, extra: str = "") -> str:
    return CABECALHO_PT + ENTRADA_PT + "".join(f"- {b}\n" for b in bullets) + extra


def cv_en(*bullets: str, extra: str = "") -> str:
    return CABECALHO_EN + ENTRADA_EN + "".join(f"- {b}\n" for b in bullets) + extra


def falhas(md: str) -> list[str]:
    rel = verificar(md, perfil=PERFIL)
    return [f for u in rel["unidades"] for f in u["falhas"]] + rel["gerais"]


class BulletsVerdadeiros(unittest.TestCase):
    def test_bullet_fiel_pt(self):
        md = cv_pt(
            "Estruturei a gestão de defeitos no Linear, com boards de bugs pré-produção, incidentes de produção "
            "e relatórios de teste: 277 incidentes catalogados por fluxo. <!-- fonte: 4.1#7 -->"
        )
        self.assertEqual(falhas(md), [])

    def test_bullet_fiel_en_com_metricas(self):
        md = cv_en(
            "Cut bug reporting from 30 to 4 min (−85%) and BDD test planning from 3 h to 18 min (−90%) "
            "with five Claude skills integrated with Linear. <!-- fonte: 4.1#15, 11b#3, 11b#4 -->"
        )
        self.assertEqual(falhas(md), [])

    def test_curriculos_dos_evals_aprovados(self):
        for pasta in sorted((RAIZ / "evals" / "resultados").glob("*")):
            cv = pasta / "curriculo.md"
            if cv.exists():
                ad = json.loads((pasta / "aderencia.json").read_text(encoding="utf-8"))
                rel = verificar(cv.read_text(encoding="utf-8"), ad, PERFIL)
                with self.subTest(pasta.name):
                    self.assertTrue(rel["aprovado"], [u["falhas"] for u in rel["unidades"] if u["falhas"]] + rel["gerais"])


class FatosInventados(unittest.TestCase):
    def assertReprova(self, md: str, trecho: str):
        f = falhas(md)
        self.assertTrue(any(trecho.lower() in x.lower() for x in f), f"esperava falha com '{trecho}', veio: {f}")

    def test_metrica_inflada(self):
        self.assertReprova(cv_pt("Reduzi em 95% o tempo de registro de incidentes com agentes de IA integrados ao Linear. <!-- fonte: 11b#3 -->"), "número")

    def test_numero_sem_fonte_em_ingles(self):
        self.assertReprova(cv_en("Built synthetic monitoring that ran 50,000 checks in 5 weeks. <!-- fonte: 11b#10 -->"), "número")

    def test_ferramenta_que_nao_usa_jira(self):
        self.assertReprova(cv_pt("Registrei e acompanhei bugs no Jira com evidências por cenário. <!-- fonte: 4.1#7 -->"), "jira")

    def test_cypress_em_producao(self):
        self.assertReprova(cv_en("Maintained the Cypress end-to-end suite for 3 brands. <!-- fonte: 4.1#10 -->"), "cypress")

    def test_lacuna_docker_kubernetes(self):
        self.assertReprova(cv_pt("Containerizei a suíte de automação com Docker. <!-- fonte: 4.1#10 -->"), "docker")

    def test_bullet_sem_origem(self):
        self.assertReprova(cv_pt("Implantei programa de testes de acessibilidade em aplicativos de varejo para 12 clientes."), "")

    def test_alegacao_sem_fonte_e_sem_citacao(self):
        self.assertReprova(cv_en("Spearheaded the company-wide migration of 40 microservices to a new cloud provider."), "sem origem")

    def test_fonte_inexistente(self):
        self.assertReprova(cv_pt("Automatizei o smoke crítico com Playwright. <!-- fonte: 4.1#99 -->"), "fonte inexistente")

    def test_fonte_errada_pouco_parecida(self):
        self.assertReprova(cv_pt("Automatizei o smoke crítico com Playwright e TypeScript. <!-- fonte: 4.7#3 -->"), "pouco parecido")

    def test_mentoria_inventada(self):
        self.assertReprova(cv_pt("Mentorei desenvolvedores em boas práticas de código e revisão. <!-- fonte: 4.1#24 -->"), "escalada")

    def test_lideranca_de_equipe_de_qa(self):
        self.assertReprova(cv_pt("Liderei a equipe de QA em 3 marcas de iGaming. <!-- fonte: 4.1#4 -->"), "liderou equipe de qa")

    def test_lideranca_em_ingles(self):
        self.assertReprova(cv_en("Led a QA team covering 3 iGaming brands. <!-- fonte: 4.1#4 -->"), "")

    def test_apostas(self):
        self.assertReprova(cv_pt("Testei três plataformas de apostas esportivas. <!-- fonte: 4.1#4 -->"), "igaming")

    def test_betting(self):
        self.assertReprova(cv_en("Tested three betting platforms. <!-- fonte: 4.1#4 -->"), "igaming")

    def test_ci_cd_rodando(self):
        self.assertReprova(cv_pt("Integrei o smoke ao pipeline de CI/CD com GitHub Actions. <!-- fonte: 4.1#23 -->"), "qualificador")

    def test_certificacao(self):
        self.assertReprova(cv_pt("Certificação em Machine Learning na AWS (UFRPE, 2024). <!-- fonte: 7#2 -->"), "certificação")

    def test_nome_de_incidente(self):
        self.assertReprova(cv_pt("Identifiquei 85 jogos com erro em 27 provedores (INC-149). <!-- fonte: 4.1#17 -->"), "incidente interno")

    def test_host_interno(self):
        self.assertReprova(cv_pt("Monitorei a disponibilidade de painel.interno.com.br. <!-- fonte: 4.1#12 -->"), "host")

    def test_tecnologia_com_ponto_net_nao_e_host(self):
        md = cv_pt("Atuei em aplicações web ASP.NET MVC com Microsoft SQL Server para bancos e fintechs. <!-- fonte: 4.2#2 -->")
        self.assertFalse(any("Host" in f for f in falhas(md)))

    def test_ufrpe_em_andamento(self):
        md = CABECALHO_PT + "## Formação\n\n### Bacharelado em Sistemas de Informação | 2024 – atual\nUFRPE | Recife, PE\n"
        self.assertReprova(md, "ufrpe")

    def test_habilidade_sem_lastro(self):
        md = cv_pt(extra="\n## Habilidades\n- **Ferramentas**: Playwright, Selenium, Kubernetes\n")
        self.assertReprova(md, "selenium")

    def test_nome_proprio_inventado(self):
        self.assertReprova(cv_pt("Automatizei o smoke crítico com Playwright e Katalon Studio. <!-- fonte: 4.1#10 -->"), "katalon")

    def test_headline_inflada(self):
        md = CABECALHO_PT.replace("Recife, PE", "> Analista de QA Sênior · Cypress e Selenium\nRecife, PE")
        self.assertReprova(md, "senioridade")

    def test_idioma_trocado(self):
        md = CABECALHO_EN + ENTRADA_EN + "- Automatizei o smoke crítico com Playwright e TypeScript nas três marcas. <!-- fonte: 4.1#10 -->\n"
        self.assertReprova(md, "idioma")


class Aderencia(unittest.TestCase):
    def analisar_vaga(self, nome: str) -> dict:
        texto = (RAIZ / "evals" / "vagas" / nome).read_text(encoding="utf-8")
        return analisar(extrair(texto), PERFIL)

    def test_sao_paulo_presencial_nao_aplicar(self):
        res = self.analisar_vaga("d-qa-presencial-sao-paulo.txt")
        self.assertEqual(res["recomendacao"], "não aplicar")
        self.assertTrue(any("Localidade" in b for b in res["bloqueios"]))

    def test_recife_hibrido_aplicar(self):
        res = self.analisar_vaga("a-qa-analyst-jr-recife.txt")
        self.assertEqual(res["bloqueios"], [])
        self.assertIn(res["recomendacao"], ("aplicar", "aplicar com ressalvas"))

    def test_jira_e_istqb_fora_do_cv(self):
        res = self.analisar_vaga("a-qa-analyst-jr-recife.txt")
        fora = {p["conceito"] for p in res["palavras_chave"] if not p["usar_no_cv"]}
        self.assertTrue({"jira", "istqb"} <= fora)

    def test_ferramenta_pedida_conta_mais_que_conceito(self):
        res = self.analisar_vaga("d-qa-presencial-sao-paulo.txt")
        req = next(r for r in res["requisitos"] if "Selenium" in r["texto"])
        self.assertEqual(req["status"], "parcial")

    def test_remoto_em_qualquer_lugar(self):
        vaga = {"titulo": "QA Analyst", "modelo_trabalho": "remoto", "local": "São Paulo", "senioridade": "junior",
                "obrigatorios": ["Playwright"], "desejaveis": [], "palavras_chave": []}
        self.assertEqual(analisar(vaga, PERFIL)["bloqueios"], [])

    def test_senior_bloqueia(self):
        vaga = {"titulo": "Senior QA", "modelo_trabalho": "remoto", "local": None, "senioridade": "senior",
                "obrigatorios": ["Playwright"], "desejaveis": [], "palavras_chave": []}
        self.assertEqual(analisar(vaga, PERFIL)["recomendacao"], "não aplicar")

    def test_relocacao_vira_ressalva(self):
        vaga = {"titulo": "QA", "modelo_trabalho": "presencial", "local": "Curitiba", "relocacao_oferecida": True,
                "senioridade": "junior", "obrigatorios": ["Playwright"], "desejaveis": [], "palavras_chave": []}
        res = analisar(vaga, PERFIL)
        self.assertEqual(res["bloqueios"], [])
        self.assertTrue(any("relocação" in r for r in res["ressalvas"]))


class Extracao(unittest.TestCase):
    def test_idiomas(self):
        for nome, idioma in [("a-qa-analyst-jr-recife.txt", "pt"), ("b-qa-automation-en-remote.txt", "en")]:
            texto = (RAIZ / "evals" / "vagas" / nome).read_text(encoding="utf-8")
            self.assertEqual(extrair(texto)["idioma"], idioma)

    def test_modelo_e_local(self):
        texto = (RAIZ / "evals" / "vagas" / "d-qa-presencial-sao-paulo.txt").read_text(encoding="utf-8")
        vaga = extrair(texto)
        self.assertEqual((vaga["modelo_trabalho"], vaga["local"], vaga["relocacao_oferecida"]), ("presencial", "São Paulo", False))

    def test_linkedin_nao_e_buscado(self):
        from extrair_vaga import FalhaBusca, texto_da_url
        with self.assertRaises(FalhaBusca) as ctx:
            texto_da_url("https://www.linkedin.com/jobs/search/?currentJobId=4012345678")
        self.assertIn("4012345678", str(ctx.exception))

    def test_gupy_next_data(self):
        from extrair_vaga import nextdata_vaga
        desc = "<p>Requisitos</p><ul><li>Experiência com testes manuais</li></ul>" + "x" * 200
        pagina = '<script id="__NEXT_DATA__" type="application/json">' + json.dumps(
            {"props": {"pageProps": {"job": {"name": "Analista de QA", "description": desc}}}}) + "</script>"
        self.assertEqual(nextdata_vaga(pagina)["name"], "Analista de QA")

    def test_relocacao_negada_nao_conta(self):
        # "Não oferecemos ajuda de custo para mudança" não é oferta de relocação
        texto = (RAIZ / "evals" / "vagas" / "d-qa-presencial-sao-paulo.txt").read_text(encoding="utf-8")
        self.assertFalse(extrair(texto)["relocacao_oferecida"])


class Lexico(unittest.TestCase):
    def test_evidencias_existem_no_perfil(self):
        texto = PERFIL.texto_dobrado
        for c in carregar_conceitos():
            for termo in c["cobre"] + c["parcial"]:
                with self.subTest(conceito=c["id"], termo=termo):
                    self.assertTrue(contem_termo(texto, termo))

    def test_numeros_normalizados(self):
        self.assertEqual(numeros("1.990 reviews e 27 mil verificações"), {"1990", "27000"})
        self.assertEqual(numeros("1,990 reviews and 27k checks"), {"1990", "27000"})


if __name__ == "__main__":
    unittest.main()
