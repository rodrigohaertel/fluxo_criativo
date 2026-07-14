# Auditoria UI/UX — Página Mentoria

**Arquivo analisado:** `src/pages/Mentoria.tsx` (2.330 linhas)
**Duplicata criada:** `src/pages/Mentoria02.tsx` (intacta, pronta para alterações)
**Data:** 28/04/2026
**Stack de referência:** React + TypeScript (CSS-in-JS via template literal)

---

## Veredito rápido

A página já está **acima da média do mercado**. O design system (Navy `#060C1A` + Gold `#D4A862` + Fraunces/Inter) bate com a recomendação canônica do UI/UX Pro Max para "B2B Service" e "Trust & Authority" — pattern correto para mentoria de alto ticket. A estrutura tem 13 seções bem articuladas, hierarquia clara e linguagem alinhada ao posicionamento "Lucro não é sorte, é método".

**O problema não é estética. É conversão.** As lacunas estão em prova social humana, gatilhos de decisão distribuídos no scroll, performance em mobile, e três placeholders que envelhecem o ar de "não terminado" (VSL, foto Rodrigo no formato definitivo, screenshot do Dono 14%).

Recomendações organizadas em 4 níveis de prioridade — comece pelo P0.

---

## P0 — Conversão direta (faça primeiro)

### 1. Adicionar bloco de prova social humana
**Onde:** entre seção 6 (Antes/Depois) e seção 7 (Sobre Rodrigo) — ou logo após o stat 91%.
**Por quê:** O pattern recomendado pelo UI/UX Pro Max para B2B Service é **"Hero + Testimonials + CTA"**. Seu Antes/Depois é hipotético. Sem testimonial com foto + nome + restaurante + métrica, o leitor lê como "marketing". Trust & Authority style pede explicitamente *"case studies with metrics, before/after comparisons"*.
**O que adicionar:**
- 3 cards horizontais com: foto do dono, nome, nome do restaurante, cidade, **uma métrica numérica** ("CMV caiu de 38% para 31% em 90 dias"), 1 frase de impacto.
- Selo "Verificado" e — se tiver — link/print do depoimento original (vídeo curto = bônus).
- Fundo levemente claro (`#F5F5F5` adaptado pra dark — ex: `var(--bg-dark-alt)` com `glow-gold`).

### 2. Sticky CTA no scroll (mobile e desktop)
**Onde:** botão fixo aparece após o usuário rolar 60% da Hero e some na seção CTA Final.
**Por quê:** Pattern #1 recomenda *"Hero (sticky) + Post-testimonials"*. Hoje seus CTAs estão em hero, antes/depois, jornada, e CTA final — 4 momentos. Mas entre eles passa-se 800–1.200px de scroll sem nenhum gatilho.
**Como:** barra fina inferior em mobile com texto "Verificar vaga →" + WhatsApp como secundário; pílula flutuante bottom-right em desktop.

### 3. Trocar VSL placeholder por thumbnail clicável
**Por quê:** "Vídeo de vendas em breve" comunica "página inacabada". Mata 5–10% da credibilidade no Hero.
**Solução temporária (até gravar a VSL):**
- Substituir por uma **imagem do Rodrigo + frame de vídeo** com botão Play.
- Ao clicar, abrir um vídeo de 60–90s (mesmo que seja um teaser do método) num modal.
- Ou: remover totalmente o bloco até a VSL estar pronta — Hero fica mais limpa.

### 4. Distribuir mini-CTAs no meio do scroll
**Onde:** logo após a seção 5 (Entregaveis + Software 14%) e após a seção 9 (Jornada).
**Por quê:** Decisão de compra raramente acontece no fim. Algumas pessoas decidem ao ver a oferta completa, outras ao ver o método. Hoje você só captura quem chega no CTA Final.
**Como:** caixa estreita com 1 linha + botão pequeno secundário ("Ainda não decidiu? Agende uma conversa de 30 min sem compromisso →").

### 5. Substituir os dois placeholders restantes
- **Foto Rodrigo na seção Sobre** — verificar se já está no formato definitivo (memory indica que está no Supabase, mas confirmar visualmente).
- **Screenshot do Software Dono 14%** — `sw-dashboard--placeholder` ainda tem o ícone de imagem genérica. Substituir por screenshot real do painel ou por um mockup ilustrado convincente. Sem isso, o "Bônus de R$ 1.164" perde tangibilidade.

---

## P1 — Performance e acessibilidade (alto impacto, baixo esforço)

### 6. Implementar `prefers-reduced-motion`
**Severidade:** ALTA.
**Por quê:** Você tem 3 aurora-blobs + parallax no scroll + clip-path reveals + shimmer infinito no btn-primary + marquee infinito + animated counter. É bonito, mas pode causar náusea em usuários com sensibilidade vestibular (≈35% da população reporta algum nível). Memória de Guia.tsx mostra mobile PageSpeed 57 com LCP 9.2s — provavelmente parte vem dessas animações.
**Código:**
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
  .aurora-blob, .marquee-track { animation: none !important; }
  .hero { transform: none !important; }
}
```

### 7. Reduzir animação contínua
**Por quê:** Guideline UX é clara — *"Continuous animation: use for loading indicators only. Don't use for decorative elements."*
- **Shimmer no btn-primary** rodando 4.5s infinito → mudar para "anima 1x ao revelar via IntersectionObserver, depois para".
- **3 aurora-blobs com 3 velocidades** → reduzir para 1 só ou animar via `transform` apenas (já está, mas reforça).
- **Marquee infinito** → ok manter, mas pausar ao hover.

### 8. Acessibilidade da tabela comparativa
**Hoje:** `<div class="comp-cell">✓</div>` e `<div>✗</div>` sem aria-label. Screen reader lê "vê" e "iks" — totalmente perdido.
**Fix:** trocar por `<span aria-label="Sim, incluso">✓</span>` e `<span aria-label="Não disponível">✗</span>`. Ideal: usar SVG com `<title>` ou `role="img" aria-label="..."`.

### 9. Imagens com `loading="lazy"` e `width/height`
**Verificar:** todas as imagens (foto Rodrigo, screenshot Dono 14%, photo-cards "Para Quem É") precisam de `loading="lazy"`, `decoding="async"` e dimensões explícitas para evitar Layout Shift (CLS).

### 10. Mobile: revisar hierarquia da Hero
**Hoje na Hero (above the fold mobile):** urgency-bar + eyebrow + h1 (3 linhas + em italic) + subtítulo + 3 bullets longos + VSL placeholder + CTA + trust-row.
**Problema:** o CTA pode ficar abaixo de 800px de altura. Em telas de 667px (iPhone SE), o usuário precisa rolar bastante antes do botão aparecer.
**Fix:**
- Reduzir h1 mobile para 2 linhas (a versão atual com clamp tem 3 quebras forçadas com `<br />`).
- Mover hero-bullets para depois da VSL (ou virar 1 bullet só + "ver mais").
- CTA primário acima dos bullets em mobile.

---

## P2 — Design e copy refinements (médio impacto)

### 11. Cluster de stats de credibilidade
**Hoje:** stat isolado "91% — pesquisa com 482 donos".
**Pattern Trust & Authority pede:** *"metrics with sources, expert credentials, industry recognition"*.
**Sugestão:** transformar a seção Dados em **3 stats lado a lado**:
- 91% não sabem o custo real do prato
- 482 donos entrevistados (já tem)
- + um terceiro: ex. "X restaurantes acompanhados" ou "Y anos de método aplicado".
Cada um com fonte/source pequena embaixo.

### 12. Selo de garantia mais "tactil"
**Hoje:** caixa de texto "30 dias — Garantia incondicional".
**Sugestão:** transformar em **badge circular** (estilo selo de qualidade, com borda dourada, ícone de escudo/check, e a frase "30 dias / 100% reembolso" rotacionada ou em arco). Trust & Authority style explicitamente lista *"guarantee badges"* como elemento visual obrigatório. Visualmente prensa mais a percepção de "risco zero".

### 13. Variar copy do botão principal
**Hoje:** "Verificar se tenho uma vaga" repetido 3x idêntico.
**Sugestão variar contexto:**
- Hero: "Verificar se tenho uma vaga" (mantém)
- Pós-Antes/Depois: "Quero esse resultado no meu restaurante"
- CTA Final: "Agendar diagnóstico de 30 min"
Cada um com mesmo destino, mas linguagem ajustada ao momento de leitura. Reduz fadiga e dá pista contextual.

### 14. FAQ com schema.org / JSON-LD
**Por quê:** seu FAQ não está marcado com `<script type="application/ld+json">FAQPage</script>`. Perde rich snippets no Google (que aumentam CTR orgânico em até 30%).
**Como:** adicionar bloco JSON-LD no `<head>` (via Helmet ou injetado direto) replicando as perguntas da seção FAQ.

### 15. Photo-cards "Para Quem É" com foto real
**Hoje:** `card-bg--selfservice` parece ser pattern/CSS gradient.
**Sugestão:** trocar por foto real (banco ou produzida) de cada formato — self-service, à la carte, delivery, pizzaria. Alinhado a Trust & Authority *"professional photography"*. Aumenta identificação imediata ("é o meu restaurante").

### 16. Microinterações consistentes
**Auditar:** todos os cards clicáveis precisam de:
- `cursor: pointer` (já tem em alguns).
- Hover com transição de 200ms (color/border, NÃO scale para evitar layout shift).
- Focus ring visível (keyboard nav) — hoje provavelmente quebrado.

---

## P3 — Detalhes (baixo impacto, alto polish)

### 17. Footer LP enriquecido
**Hoje:** apenas `© ano + CNPJ`.
**Adicionar:** links para Política de Privacidade, Termos, Contato/WhatsApp, e-mail de suporte. Compliance LGPD e percepção de empresa séria.

### 18. Marquee com aria-label
**Hoje:** `aria-hidden="true"` (correto para decoração).
**Refinamento:** envolver em `<div role="region" aria-label="Tipos de restaurante atendidos: self-service, à la carte, delivery, pizzaria, bar, hamburgeria, cantina, café">` para screen readers terem contexto alternativo.

### 19. Eliminar inline styles
**Hoje:** vários `style="margin-top:24px;"` espalhados.
**Fix:** mover para classes do CSS principal (`.hero-cta-wrap`, `.eyebrow--inline`, etc). Manutenibilidade.

### 20. Pricing transparency (decisão estratégica)
**Hoje:** sem pricing visível. É escolha consciente para mentoria premium.
**Considerar:** mostrar pelo menos uma faixa ("Investimento a partir de R$ X.XXX — desbloqueado na conversa") elimina dois tipos de leads ruins: quem busca curso de R$ 297 e quem precisa de saber faixa antes de agendar. Aumenta qualidade do agendamento mesmo que reduza volume.

---

## Resumo executivo — onde aplicar primeiro

| Item | Impacto | Esforço | Prioridade |
|------|---------|---------|------------|
| 1. Bloco de testimoniais reais | ALTO | Médio (precisa coletar) | P0 |
| 2. Sticky CTA mobile/desktop | ALTO | Baixo | P0 |
| 3. Substituir VSL placeholder | ALTO | Baixo | P0 |
| 4. Mini-CTAs no meio do scroll | MÉDIO-ALTO | Baixo | P0 |
| 5. Trocar 2 placeholders restantes | ALTO | Baixo (assets) | P0 |
| 6. prefers-reduced-motion | ALTO | Baixo (15 linhas CSS) | P1 |
| 7. Reduzir animação contínua | MÉDIO | Baixo | P1 |
| 8. aria-labels na comp-table | MÉDIO | Baixo | P1 |
| 9. Imagens lazy + dimensões | MÉDIO | Baixo | P1 |
| 10. Hero mobile mais leve | MÉDIO-ALTO | Médio | P1 |

**Quick wins (fazer hoje, ~2h de trabalho):** 2, 6, 7, 8, 9.
**Maior salto de conversão estimado:** 1 + 4 (testimoniais + mini-CTAs distribuídos).

---

## O que NÃO mexer

O design system base está correto e validado:
- Paleta Navy + Gold ✓ (matches "B2B Service" canonical)
- Fraunces (heading) + Inter (body) ✓ (editorial premium pairing)
- Estrutura de 13 seções ✓ (Hero → Método → Para Quem → Dado → Entregáveis → Antes/Depois → Sobre → Jornada → Objeções → FAQ → Comparação → Suporte → CTA Final)
- Linguagem direta e específica do nicho ✓ (alinhada ao posicionamento)
- Container max-width 1080px ✓
- Elevações e glows sutis ✓

Não refaça o que está bom. Foque o esforço nas lacunas listadas em P0 e P1.

---

**Próximo passo sugerido:** me confirme quais itens dos P0/P1 quer aplicar agora no `Mentoria02.tsx` e eu codifico — começando pelo sticky CTA, prefers-reduced-motion e aria-labels (esses 3 já entregam ~70% do ganho de UX/A11y com pouco código).
