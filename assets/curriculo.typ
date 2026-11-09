// Template de currículo da skill cv-tailoring.
// Uma coluna, sem tabelas nem cabeçalho/rodapé de página: texto 100% extraível por ATS.
// O conteúdo chega como JSON em sys.inputs.dados (gerado por scripts/render.py);
// strings são desenhadas literalmente, então nenhum caractere do currículo é interpretado.

#let dados = json(bytes(sys.inputs.at("dados")))
#let estilo = dados.estilo

#set document(title: dados.nome + " · " + dados.titulo_doc, author: dados.nome)
#set page(paper: "a4", margin: (x: estilo.margem_x * 1cm, y: estilo.margem_y * 1cm))
#set text(font: ("Libertinus Serif", "New Computer Modern"), size: estilo.fonte * 1pt, lang: dados.idioma, hyphenate: false)
#set par(justify: false, leading: 0.48em, spacing: 0.5em)
#set list(indent: 0.55em, body-indent: 0.45em, spacing: 0.38em, marker: [•])
#show link: set text(fill: rgb("#1a1a1a"))
#show link: underline.with(offset: 1.6pt, stroke: 0.4pt)

#let corridas(rs) = {
  for r in rs {
    let t = r.t
    let c = if r.at("u", default: none) != none { link(r.u, t) } else { t }
    if r.at("b", default: false) { c = strong(c) }
    if r.at("i", default: false) { c = emph(c) }
    c
  }
}

#let linha-dupla(esq, dir) = grid(
  columns: (1fr, auto),
  column-gutter: 1em,
  esq, align(right, dir),
)

// Cabeçalho
#align(center)[
  #text(size: estilo.fonte * 2.2pt, tracking: 0.02em, smallcaps(dados.nome))
  #v(-0.55em)
  #if dados.headline != none {
    text(size: estilo.fonte * 1.08pt, corridas(dados.headline))
    v(-0.2em)
  }
  #text(size: estilo.fonte * 0.93pt)[
    #dados.contato.map(c => corridas(c)).join([ | ])
  ]
]

#for secao in dados.secoes {
  v(estilo.respiro * 0.55em)
  block(below: 0.5em, sticky: true)[
    #text(size: estilo.fonte * 1.12pt, weight: "bold", smallcaps(secao.titulo))
    #v(-0.42em)
    #line(length: 100%, stroke: 0.55pt)
  ]
  for bloco in secao.blocos {
    if bloco.tipo == "entrada" {
      block(above: 0.5em, below: 0.32em, breakable: false, sticky: true)[
        #linha-dupla(strong(corridas(bloco.titulo)), corridas(bloco.data))
        #if bloco.org != none {
          v(-0.12em)
          text(size: estilo.fonte * 0.95pt, linha-dupla(emph(corridas(bloco.org)), emph(corridas(bloco.local))))
        }
      ]
    } else if bloco.tipo == "lista" {
      list(..bloco.itens.map(i => corridas(i)))
    } else if bloco.tipo == "rotulado" {
      block(above: 0.3em, below: 0.3em)[
        #for item in bloco.itens [
          #strong(item.rotulo): #corridas(item.texto) \
        ]
      ]
    } else {
      par(corridas(bloco.corridas))
    }
  }
}
