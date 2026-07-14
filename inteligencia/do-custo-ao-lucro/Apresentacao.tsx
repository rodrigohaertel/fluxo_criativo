import { useState, useEffect, useCallback, useRef } from "react";
import { AnimatePresence, motion, useMotionValue, useSpring } from "framer-motion";
import "./apresentacao.css";

interface SlideData {
  id: number;
  steps: number;
  theme: string;
  notes: string;
  glow: string;
  inlineStyle: string;
  html: string;
}

const SLIDES: SlideData[] = [
  {
    "id": 1,
    "steps": 0,
    "theme": "cover",
    "notes": "Abertura. Silêncio. Deixe o visual carregar. Apresente-se: 'Obrigado por reservar esse tempo, Delane. Nos próximos minutos vou te mostrar como funciona a Mentoria Dono 14%. Ao final a gente decide juntos se faz sentido avançar.'",
    "glow": "",
    "inlineStyle": "justify-content:center; align-items:center;",
    "html": "<div class=\"img-bg overlay-heavy\"\n         style=\"background-image: url('https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Fundo%20Hero%20Dono%2014.webp');\"></div>\n    <div style=\"position:absolute; inset:0; z-index:1; pointer-events:none;\n                background: radial-gradient(ellipse 70% 55% at 50% 50%, hsla(36,55%,62%,0.10) 0%, transparent 65%);\"></div>\n\n    <div style=\"position:relative; z-index:2; text-align:center; display:flex; flex-direction:column; align-items:center; gap:36px;\">\n\n      <!-- Logo Dono 14% -->\n      <img src=\"https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Logo%20-%20Dono%2014.webp\"\n           alt=\"Dono 14%\" class=\"reveal\"\n           style=\"height: clamp(140px, 22vh, 240px); display:block; margin:0 auto;\n                  filter: drop-shadow(0 0 60px hsla(36,55%,62%,0.35));\">\n\n      <!-- Divisor -->\n      <div class=\"reveal d1\" style=\"width:1px; height:50px; background:linear-gradient(to bottom, transparent, var(--border-gold), transparent); margin:0 auto;\"></div>\n\n      <!-- Cliente -->\n      <div class=\"reveal d2\" style=\"padding:20px 40px;\n           background:hsla(165,45%,11%,0.75); backdrop-filter:blur(20px);\n           border:1px solid var(--border-gold); border-radius:16px; text-align:center;\">\n        <div style=\"font-family:var(--serif); font-size:clamp(1.1rem,2vw,1.4rem); font-weight:700; color:var(--cream); letter-spacing:-0.015em;\">\n          Delane Castelo Branco\n        </div>\n        <div style=\"font-size:0.72rem; color:var(--gold); letter-spacing:0.14em; text-transform:uppercase; font-weight:700; margin-top:6px;\">\n          @chefaosushibar\n        </div>\n      </div>\n\n    </div>"
  },
  {
    "id": 2,
    "steps": 0,
    "theme": "",
    "notes": "Crie suspense. Diga: 'Antes de falar do que eu faço, quero te mostrar um número. Porque ele explica tudo que você vai ver aqui.' Pausa. Depois clique.",
    "glow": "glow-emerald",
    "inlineStyle": "",
    "html": "<div class=\"slide-photo\">\n      <img src=\"https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Dono%20e%20Engenheiro%20-%2003.webp\" alt=\"\">\n    </div>\n    <div class=\"slide-inner\" style=\"max-width:680px;\">\n      <span class=\"eyebrow reveal\"><span class=\"eyebrow-dot\"></span> Antes de tudo</span>\n      <h2 class=\"h2 reveal d1\">Quero te mostrar <em>um número.</em></h2>\n      <div class=\"divider reveal d2\" style=\"max-width:120px; margin:24px 0;\"></div>\n      <p class=\"sub reveal d3\">\n        Não é sobre faturamento. Não é sobre clientela.<br>\n        É sobre o que está acontecendo <strong style=\"color:var(--cream);\">dentro</strong> do seu restaurante agora.\n      </p>\n    </div>"
  },
  {
    "id": 3,
    "steps": 1,
    "theme": "soft",
    "notes": "Deixe o número aparecer. SILÊNCIO de 3 segundos. Depois leia: 'Nove em cada dez donos não sabem o custo real do próprio prato.' Pergunte: 'Você sabe?' — e ouça antes de clicar.",
    "glow": "glow-gold",
    "inlineStyle": "justify-content:center; align-items:center;",
    "html": "<!-- Eyebrow fixo no topo, não afeta o layout do número -->\n    <div style=\"position:absolute; top:52px; left:0; right:0; text-align:center; z-index:2; pointer-events:none;\">\n      <span class=\"eyebrow reveal\"><span class=\"eyebrow-dot\"></span> Dado que você não pode ignorar</span>\n    </div>\n    <!-- Número + texto centralizados -->\n    <div style=\"display:flex; flex-direction:column; align-items:center; text-align:center; width:100%; max-width:760px; position:relative; z-index:1;\">\n      <div class=\"reveal\">\n        <span class=\"big-num\" id=\"big-num-91\" style=\"font-size:clamp(8rem,19vw,15rem); display:block; white-space:nowrap; padding-right:0.55em; line-height:1.05;\">91%</span>\n      </div>\n      <div class=\"step\" id=\"s3-1\" style=\"margin-top:24px;\">\n        <p style=\"font-size:clamp(1.1rem,1.9vw,1.38rem); color:var(--cream-80); line-height:1.65; max-width:580px; margin:0 auto;\">\n          dos donos de restaurante <strong style=\"color:var(--cream);\">não sabem o custo real</strong>\n          do próprio prato — independente do formato, do faturamento ou do tempo de mercado.\n        </p>\n        <p style=\"margin-top:12px; font-size:0.78rem; color:var(--cream-40); font-style:italic; font-family:var(--serif);\">\n          Pesquisa própria · 482 donos de restaurante · Do Custo ao Lucro Restaurantes\n        </p>\n      </div>\n    </div>"
  },
  {
    "id": 4,
    "steps": 0,
    "theme": "",
    "notes": "Depoimento de Alexandre Prataviera. Deixe o vídeo falar por você. Não comente enquanto toca.",
    "glow": "glow-emerald",
    "inlineStyle": "",
    "html": "<div class=\"slide-inner\" style=\"max-width:1120px; padding-top:0;\">\n      <span class=\"eyebrow reveal\"><span class=\"eyebrow-dot\"></span> Quem já fez a virada</span>\n      <div class=\"test-layout reveal d1\">\n        <div class=\"test-left\">\n          <div class=\"test-name\">Alexandre<br>Prataviera</div>\n          <div class=\"test-location\">📍 Vila Velha · ES</div>\n          <div class=\"test-quote\">Precificar está longe de só colocar o preço em produto.</div>\n        </div>\n        <div class=\"test-right\">\n          <div class=\"test-video\">\n            <iframe src=\"https://www.youtube-nocookie.com/embed/5Sh1jOUbclY?rel=0&modestbranding=1&playsinline=1\"\n              title=\"Depoimento Alexandre Prataviera\" allow=\"accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen\"\n              allowfullscreen loading=\"lazy\"></iframe>\n          </div>\n        </div>\n      </div>\n    </div>"
  },
  {
    "id": 5,
    "steps": 0,
    "theme": "",
    "notes": "Depoimento de Vinicius Leite. Silêncio enquanto o vídeo toca.",
    "glow": "glow-emerald",
    "inlineStyle": "",
    "html": "<div class=\"slide-inner\" style=\"max-width:1120px; padding-top:0;\">\n      <span class=\"eyebrow reveal\"><span class=\"eyebrow-dot\"></span> Quem já fez a virada</span>\n      <div class=\"test-layout reveal d1\">\n        <div class=\"test-left\">\n          <div class=\"test-name\">Vinicius<br>Leite</div>\n          <div class=\"test-location\">📍 Belo Horizonte · MG</div>\n          <div class=\"test-quote\">Eu achava que era certo copiar o preço do concorrente.</div>\n        </div>\n        <div class=\"test-right\">\n          <div class=\"test-video\">\n            <iframe src=\"https://www.youtube-nocookie.com/embed/v8VfeuYv9W4?rel=0&modestbranding=1&playsinline=1\"\n              title=\"Depoimento Vinicius Leite\" allow=\"accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen\"\n              allowfullscreen loading=\"lazy\"></iframe>\n          </div>\n        </div>\n      </div>\n    </div>"
  },
  {
    "id": 6,
    "steps": 3,
    "theme": "",
    "notes": "Direto ao ponto. Não explique — apresente. Diga o título de cada item e deixe a imagem se formar na cabeça do dono. Sem leitura, sem detalhamento aqui.",
    "glow": "glow-gold",
    "inlineStyle": "",
    "html": "<div class=\"slide-photo\">\n      <img src=\"https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Projeto%2014/04-paraquem-sim.webp\" alt=\"\">\n    </div>\n    <div class=\"slide-inner\" style=\"max-width:680px;\">\n      <span class=\"eyebrow reveal\"><span class=\"eyebrow-dot\"></span> A solução</span>\n      <h2 class=\"h2 reveal d1\">A <em>Mentoria Dono 14%</em></h2>\n      <div style=\"display:flex; flex-direction:column; gap:16px; margin-top:32px;\">\n\n        <div class=\"step\" id=\"s6-1\"\n             style=\"display:flex; gap:20px; align-items:center; padding:22px 28px;\n                    background:hsla(165,45%,11%,0.75); border:1px solid var(--border-gold); border-radius:14px;\">\n          <div class=\"ent-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M2 18a1 1 0 0 0 1 1h18a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1H3a1 1 0 0 0-1 1v2z\"/><path d=\"M10 10V5a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v5\"/><path d=\"M4 15v-3a8 8 0 0 1 16 0v3\"/></svg></div>\n          <div>\n            <div class=\"ent-tag\">Não é um curso</div>\n            <div style=\"font-family:var(--serif); font-size:clamp(1.3rem,2.2vw,1.7rem); font-weight:700; color:var(--cream); line-height:1.1; margin-top:4px;\">\n              É uma mentoria de <em>construção</em>\n            </div>\n          </div>\n        </div>\n\n        <div class=\"step\" id=\"s6-2\"\n             style=\"display:flex; gap:20px; align-items:center; padding:22px 28px;\n                    background:hsla(165,45%,11%,0.75); border:1px solid var(--border-gold); border-radius:14px;\">\n          <div class=\"ent-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><polygon points=\"12 2 2 7 12 12 22 7 12 2\"/><polyline points=\"2 17 12 22 22 17\"/><polyline points=\"2 12 12 17 22 12\"/></svg></div>\n          <div>\n            <div class=\"ent-tag\">O método</div>\n            <div style=\"font-family:var(--serif); font-size:clamp(1.3rem,2.2vw,1.7rem); font-weight:700; color:var(--cream); line-height:1.1; margin-top:4px;\">\n              Engenharia de <em>Cardápio</em>\n            </div>\n          </div>\n        </div>\n\n        <div class=\"step\" id=\"s6-3\"\n             style=\"display:flex; gap:20px; align-items:center; padding:22px 28px;\n                    background:linear-gradient(135deg, hsla(36,55%,62%,0.12), transparent);\n                    border:1px solid hsla(36,55%,62%,0.4); border-radius:14px;\">\n          <div class=\"ent-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><circle cx=\"12\" cy=\"12\" r=\"10\"/><circle cx=\"12\" cy=\"12\" r=\"6\"/><circle cx=\"12\" cy=\"12\" r=\"2\"/></svg></div>\n          <div>\n            <div class=\"ent-tag\">O resultado</div>\n            <div style=\"font-family:var(--serif); font-size:clamp(1.3rem,2.2vw,1.7rem); font-weight:700; color:var(--cream); line-height:1.1; margin-top:4px;\">\n              <em>14%</em> de lucro operacional todo mês\n            </div>\n          </div>\n        </div>\n\n      </div>\n    </div>"
  },
  {
    "id": 7,
    "steps": 0,
    "theme": "soft",
    "notes": "Fase 1 de 5. Diga: 'Antes de qualquer número, a gente fecha um pacto. Você decide virar Dono 14%. A obra começa aqui.' Deixe pousar.",
    "glow": "glow-emerald",
    "inlineStyle": "",
    "html": "<div class=\"slide-photo soft\">\n      <img src=\"https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Dono%20e%20Engenheiro%20-%2001.webp\" alt=\"\" loading=\"lazy\">\n    </div>\n    <div class=\"slide-inner\" style=\"max-width:900px;\">\n\n      <!-- Timeline -->\n      <div class=\"dcal-timeline reveal\">\n        <div class=\"dcal-phase\">\n          <div class=\"dcal-circle active\">1</div>\n          <div class=\"dcal-label active\">O Pacto</div>\n        </div>\n        <div class=\"dcal-connector\"></div>\n        <div class=\"dcal-phase\">\n          <div class=\"dcal-circle\">2</div>\n          <div class=\"dcal-label\">A Verdade</div>\n        </div>\n        <div class=\"dcal-connector\"></div>\n        <div class=\"dcal-phase\">\n          <div class=\"dcal-circle\">3</div>\n          <div class=\"dcal-label\">O Projeto</div>\n        </div>\n        <div class=\"dcal-connector\"></div>\n        <div class=\"dcal-phase\">\n          <div class=\"dcal-circle\">4</div>\n          <div class=\"dcal-label\">A Obra</div>\n        </div>\n        <div class=\"dcal-connector\"></div>\n        <div class=\"dcal-phase\">\n          <div class=\"dcal-circle\">5</div>\n          <div class=\"dcal-label\">A Chave</div>\n        </div>\n      </div>\n\n      <!-- Conteúdo da fase -->\n      <div class=\"dcal-content\">\n        <span class=\"dcal-fase-num reveal d1\">01</span>\n        <div class=\"dcal-fase-name reveal d2\">O <em>Pacto</em></div>\n        <p class=\"dcal-fase-desc reveal d3\">\n          Compromisso público de virar Dono 14%. A jornada já começa aqui, antes de qualquer número.\n        </p>\n      </div>\n\n    </div>"
  },
  {
    "id": 8,
    "steps": 0,
    "theme": "soft",
    "notes": "Fase 2. Diga: 'Primeiro encontro: diagnóstico individual. A gente olha os seus números, sem filtro. Você enxerga a realidade pela primeira vez.'",
    "glow": "glow-emerald",
    "inlineStyle": "",
    "html": "<div class=\"slide-photo soft\">\n      <img src=\"https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Projeto%2014/06-fase2-receita.webp\" alt=\"\" loading=\"lazy\">\n    </div>\n    <div class=\"slide-inner\" style=\"max-width:900px;\">\n\n      <!-- Timeline -->\n      <div class=\"dcal-timeline reveal\">\n        <div class=\"dcal-phase\">\n          <div class=\"dcal-circle done\">✓</div>\n          <div class=\"dcal-label done\">O Pacto</div>\n        </div>\n        <div class=\"dcal-connector filled\"></div>\n        <div class=\"dcal-phase\">\n          <div class=\"dcal-circle active\">2</div>\n          <div class=\"dcal-label active\">A Verdade</div>\n        </div>\n        <div class=\"dcal-connector\"></div>\n        <div class=\"dcal-phase\">\n          <div class=\"dcal-circle\">3</div>\n          <div class=\"dcal-label\">O Projeto</div>\n        </div>\n        <div class=\"dcal-connector\"></div>\n        <div class=\"dcal-phase\">\n          <div class=\"dcal-circle\">4</div>\n          <div class=\"dcal-label\">A Obra</div>\n        </div>\n        <div class=\"dcal-connector\"></div>\n        <div class=\"dcal-phase\">\n          <div class=\"dcal-circle\">5</div>\n          <div class=\"dcal-label\">A Chave</div>\n        </div>\n      </div>\n\n      <!-- Conteúdo da fase -->\n      <div class=\"dcal-content\">\n        <span class=\"dcal-fase-num reveal d1\">02</span>\n        <div class=\"dcal-fase-name reveal d2\">A <em>Verdade</em></div>\n        <p class=\"dcal-fase-desc reveal d3\">\n          Diagnóstico individual. Você enxerga a realidade dos números pela primeira vez — sem achismo, sem estimativa.\n        </p>\n      </div>\n\n    </div>"
  },
  {
    "id": 9,
    "steps": 0,
    "theme": "soft",
    "notes": "Fase 3. Diga: 'Com a verdade na mão, a gente projeta o cardápio novo. Duas reuniões de projeto — eu desenho, você valida.'",
    "glow": "glow-emerald",
    "inlineStyle": "",
    "html": "<div class=\"slide-photo soft\">\n      <img src=\"https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Dono%20e%20Engenheiro%20-%2004.webp\" alt=\"\" loading=\"lazy\">\n    </div>\n    <div class=\"slide-inner\" style=\"max-width:900px;\">\n\n      <!-- Timeline -->\n      <div class=\"dcal-timeline reveal\">\n        <div class=\"dcal-phase\">\n          <div class=\"dcal-circle done\">✓</div>\n          <div class=\"dcal-label done\">O Pacto</div>\n        </div>\n        <div class=\"dcal-connector filled\"></div>\n        <div class=\"dcal-phase\">\n          <div class=\"dcal-circle done\">✓</div>\n          <div class=\"dcal-label done\">A Verdade</div>\n        </div>\n        <div class=\"dcal-connector filled\"></div>\n        <div class=\"dcal-phase\">\n          <div class=\"dcal-circle active\">3</div>\n          <div class=\"dcal-label active\">O Projeto</div>\n        </div>\n        <div class=\"dcal-connector\"></div>\n        <div class=\"dcal-phase\">\n          <div class=\"dcal-circle\">4</div>\n          <div class=\"dcal-label\">A Obra</div>\n        </div>\n        <div class=\"dcal-connector\"></div>\n        <div class=\"dcal-phase\">\n          <div class=\"dcal-circle\">5</div>\n          <div class=\"dcal-label\">A Chave</div>\n        </div>\n      </div>\n\n      <!-- Conteúdo da fase -->\n      <div class=\"dcal-content\">\n        <span class=\"dcal-fase-num reveal d1\">03</span>\n        <div class=\"dcal-fase-name reveal d2\">O <em>Projeto</em></div>\n        <p class=\"dcal-fase-desc reveal d3\">\n          Duas reuniões de projeto. O engenheiro desenha, você valida o cardápio que defende 14% mês a mês.\n        </p>\n      </div>\n\n    </div>"
  },
  {
    "id": 10,
    "steps": 0,
    "theme": "soft",
    "notes": "Fase 4. Diga: 'Cardápio projetado, a gente executa. O Painel do Dono entra em operação. Os resultados aparecem no caixa. Esta é a fase mais longa — e onde o lucro começa a mudar.'",
    "glow": "glow-emerald",
    "inlineStyle": "",
    "html": "<div class=\"slide-photo soft\">\n      <img src=\"https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Projeto%2014/08-fase4-preco.webp\" alt=\"\" loading=\"lazy\">\n    </div>\n    <div class=\"slide-inner\" style=\"max-width:900px;\">\n\n      <!-- Timeline -->\n      <div class=\"dcal-timeline reveal\">\n        <div class=\"dcal-phase\">\n          <div class=\"dcal-circle done\">✓</div>\n          <div class=\"dcal-label done\">O Pacto</div>\n        </div>\n        <div class=\"dcal-connector filled\"></div>\n        <div class=\"dcal-phase\">\n          <div class=\"dcal-circle done\">✓</div>\n          <div class=\"dcal-label done\">A Verdade</div>\n        </div>\n        <div class=\"dcal-connector filled\"></div>\n        <div class=\"dcal-phase\">\n          <div class=\"dcal-circle done\">✓</div>\n          <div class=\"dcal-label done\">O Projeto</div>\n        </div>\n        <div class=\"dcal-connector filled\"></div>\n        <div class=\"dcal-phase\">\n          <div class=\"dcal-circle active\">4</div>\n          <div class=\"dcal-label active\">A Obra</div>\n        </div>\n        <div class=\"dcal-connector\"></div>\n        <div class=\"dcal-phase\">\n          <div class=\"dcal-circle\">5</div>\n          <div class=\"dcal-label\">A Chave</div>\n        </div>\n      </div>\n\n      <!-- Conteúdo da fase -->\n      <div class=\"dcal-content\">\n        <span class=\"dcal-fase-num reveal d1\">04</span>\n        <div class=\"dcal-fase-name reveal d2\">A <em>Obra</em></div>\n        <p class=\"dcal-fase-desc reveal d3\">\n          Projeto em operação. Resultados aparecem no caixa. Ajustes finos ao longo da execução.\n        </p>\n      </div>\n\n    </div>"
  },
  {
    "id": 11,
    "steps": 0,
    "theme": "soft",
    "notes": "Fase 5 — a entrega final. Diga: 'Mês 6: a gente entrega a chave. O método está implantado, o Painel está ativo. Você é Dono 14%.' Pausa longa. Deixe o Delane responder.",
    "glow": "glow-emerald",
    "inlineStyle": "",
    "html": "<div class=\"slide-photo soft\">\n      <img src=\"https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Dono%20e%20Engenheiro%20-%2005.webp\" alt=\"\" loading=\"lazy\">\n    </div>\n    <div class=\"slide-inner\" style=\"max-width:900px;\">\n\n      <!-- Timeline -->\n      <div class=\"dcal-timeline reveal\">\n        <div class=\"dcal-phase\">\n          <div class=\"dcal-circle done\">✓</div>\n          <div class=\"dcal-label done\">O Pacto</div>\n        </div>\n        <div class=\"dcal-connector filled\"></div>\n        <div class=\"dcal-phase\">\n          <div class=\"dcal-circle done\">✓</div>\n          <div class=\"dcal-label done\">A Verdade</div>\n        </div>\n        <div class=\"dcal-connector filled\"></div>\n        <div class=\"dcal-phase\">\n          <div class=\"dcal-circle done\">✓</div>\n          <div class=\"dcal-label done\">O Projeto</div>\n        </div>\n        <div class=\"dcal-connector filled\"></div>\n        <div class=\"dcal-phase\">\n          <div class=\"dcal-circle done\">✓</div>\n          <div class=\"dcal-label done\">A Obra</div>\n        </div>\n        <div class=\"dcal-connector filled\"></div>\n        <div class=\"dcal-phase\">\n          <div class=\"dcal-circle active\">5</div>\n          <div class=\"dcal-label active\">A Chave</div>\n        </div>\n      </div>\n\n      <!-- Conteúdo da fase -->\n      <div class=\"dcal-content\">\n        <span class=\"dcal-fase-num reveal d1\">05</span>\n        <div class=\"dcal-fase-name reveal d2\">A <em>Chave</em></div>\n        <p class=\"dcal-fase-desc reveal d3\">\n          Entregamos a chave do método. Você toma posse: Restaurante 14% rodando.\n        </p>\n      </div>\n\n    </div>"
  },
  {
    "id": 12,
    "steps": 3,
    "theme": "",
    "notes": "Apresente o Projeto 14% item por item. Diga: o mapa da obra - cada passo do metodo em video, com ferramentas prontas. Revele um card por clique.",
    "glow": "glow-gold",
    "inlineStyle": "",
    "html": "<div class=\"slide-inner\" style=\"max-width:900px;\">\n      <span class=\"eyebrow reveal\"><span class=\"eyebrow-dot\"></span> O que entregamos</span>\n      <div class=\"produto-header reveal\">\n        <div class=\"produto-logo\"><img src=\"https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Logo%20Projeto%2014.webp\" alt=\"\"></div>\n        <div>\n          <div class=\"produto-nome\">Projeto <em>14%</em></div>\n          <div class=\"produto-tag\">Curso &middot; Metodo DCAL Completo &middot; 12 meses de acesso</div>\n        </div>\n      </div>\n      <div class=\"vc-grid\">\n        <div id=\"s12-1\" class=\"vc-card step\">\n          <div class=\"vc-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z\"/><path d=\"M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 0 3-3h7z\"/></svg></div>\n          <div>\n            <div class=\"vc-card-title\">5 Fases do Metodo DCAL</div>\n            <div class=\"vc-card-text\">Do custo real do ingrediente ao cardapio reprecificado &mdash; em video, passo a passo, do comeco ao fim.</div>\n          </div>\n        </div>\n        <div id=\"s12-2\" class=\"vc-card step\">\n          <div class=\"vc-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z\"/><polyline points=\"14 2 14 8 20 8\"/><line x1=\"16\" y1=\"13\" x2=\"8\" y2=\"13\"/><line x1=\"16\" y1=\"17\" x2=\"8\" y2=\"17\"/></svg></div>\n          <div>\n            <div class=\"vc-card-title\">Fichas Tecnicas Prontas</div>\n            <div class=\"vc-card-text\">Modelos para calcular o custo real de cada prato, adaptados ao seu restaurante. Sem criar do zero.</div>\n          </div>\n        </div>\n        <div id=\"s12-3\" class=\"vc-card step\">\n          <div class=\"vc-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><rect x=\"9\" y=\"9\" width=\"6\" height=\"6\"/><line x1=\"15\" y1=\"9\" x2=\"15\" y2=\"3.5\"/><line x1=\"15\" y1=\"20.5\" x2=\"15\" y2=\"15\"/><line x1=\"9\" y1=\"9\" x2=\"9\" y2=\"3.5\"/><line x1=\"9\" y1=\"20.5\" x2=\"9\" y2=\"15\"/><line x1=\"3.5\" y1=\"15\" x2=\"9\" y2=\"15\"/><line x1=\"20.5\" y1=\"15\" x2=\"15\" y2=\"15\"/><line x1=\"3.5\" y1=\"9\" x2=\"9\" y2=\"9\"/><line x1=\"20.5\" y1=\"9\" x2=\"15\" y2=\"9\"/></svg></div>\n          <div>\n            <div class=\"vc-card-title\">Software de Precificacao</div>\n            <div class=\"vc-card-text\">A ferramenta usada no metodo &mdash; sem planilha, sem formula para montar, sem contador para consultar.</div>\n          </div>\n        </div>\n      </div>\n    </div>"
  },
  {
    "id": 13,
    "steps": 3,
    "theme": "",
    "notes": "Como o aluno acessa o material. Reforce o ritmo proprio - sem pressao.",
    "glow": "glow-gold",
    "inlineStyle": "",
    "html": "<div class=\"slide-inner\" style=\"max-width:900px;\">\n      <span class=\"eyebrow reveal\"><span class=\"eyebrow-dot\"></span> Como entregamos</span>\n      <div class=\"produto-header reveal\">\n        <div class=\"produto-logo\"><img src=\"https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Logo%20Projeto%2014.webp\" alt=\"\"></div>\n        <div>\n          <div class=\"produto-nome\">Projeto <em>14%</em></div>\n          <div class=\"produto-tag\">Curso &middot; Metodo DCAL Completo &middot; 12 meses de acesso</div>\n        </div>\n      </div>\n      <div class=\"vc-grid\">\n        <div id=\"s13-1\" class=\"vc-card step\">\n          <div class=\"vc-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><circle cx=\"12\" cy=\"12\" r=\"10\"/><polyline points=\"12 6 12 12 16 14\"/></svg></div>\n          <div>\n            <div class=\"vc-card-title\">12 Meses de Acesso</div>\n            <div class=\"vc-card-text\">Aulas sempre disponíveis. Assiste hoje, aplica amanhã, revisa em seis meses &mdash; no seu ritmo.</div>\n          </div>\n        </div>\n        <div id=\"s13-2\" class=\"vc-card step\">\n          <div class=\"vc-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><circle cx=\"12\" cy=\"12\" r=\"10\"/><polygon points=\"10 8 16 12 10 16 10 8\"/></svg></div>\n          <div>\n            <div class=\"vc-card-title\">Assiste e Aplica no Dia Seguinte</div>\n            <div class=\"vc-card-text\">Cada módulo tem uma ação concreta para fazer no restaurante logo depois de assistir.</div>\n          </div>\n        </div>\n        <div id=\"s13-3\" class=\"vc-card step\">\n          <div class=\"vc-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2\"/><circle cx=\"9\" cy=\"7\" r=\"4\"/><path d=\"M23 21v-2a4 4 0 0 0-3-3.87\"/><path d=\"M16 3.13a4 4 0 0 1 0 7.75\"/></svg></div>\n          <div>\n            <div class=\"vc-card-title\">Comunidade Ativa</div>\n            <div class=\"vc-card-text\">Acesso ao grupo de alunos que estão no mesmo caminho &mdash; dúvidas respondidas, exemplos reais.</div>\n          </div>\n        </div>\n      </div>\n    </div>"
  },
  {
    "id": 14,
    "steps": 3,
    "theme": "",
    "notes": "O que muda na vida do dono depois do Projeto 14%. Fale em consequencias, nao em conteudo.",
    "glow": "glow-emerald",
    "inlineStyle": "",
    "html": "<div class=\"slide-inner\" style=\"max-width:900px;\">\n      <span class=\"eyebrow reveal\"><span class=\"eyebrow-dot\"></span> O que você ganha</span>\n      <div class=\"produto-header reveal\">\n        <div class=\"produto-logo\"><img src=\"https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Logo%20Projeto%2014.webp\" alt=\"\"></div>\n        <div>\n          <div class=\"produto-nome\">Projeto <em>14%</em></div>\n          <div class=\"produto-tag\">Curso &middot; Metodo DCAL Completo &middot; 12 meses de acesso</div>\n        </div>\n      </div>\n      <div class=\"vc-grid\">\n        <div id=\"s14-1\" class=\"vc-card gain step\">\n          <div class=\"vc-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3z\"/></svg></div>\n          <div>\n            <div class=\"vc-card-title\">Sabe o Custo Real de Cada Prato</div>\n            <div class=\"vc-card-text\">Sem chute, sem achismo &mdash; o número calculado, real, do seu restaurante. Nada de olhar para o concorrente.</div>\n          </div>\n        </div>\n        <div id=\"s14-2\" class=\"vc-card gain step\">\n          <div class=\"vc-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3z\"/></svg></div>\n          <div>\n            <div class=\"vc-card-title\">Precifica com Margem Real</div>\n            <div class=\"vc-card-text\">Preço que sustenta o negócio &mdash; calculado com a margem certa, não tirado da cabeça.</div>\n          </div>\n        </div>\n        <div id=\"s14-3\" class=\"vc-card gain step\">\n          <div class=\"vc-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3z\"/></svg></div>\n          <div>\n            <div class=\"vc-card-title\">Cardápio que Defende 14%</div>\n            <div class=\"vc-card-text\">Menu projetado para gerar lucro operacional &mdash; não só para encher mesa.</div>\n          </div>\n        </div>\n      </div>\n    </div>"
  },
  {
    "id": 15,
    "steps": 3,
    "theme": "",
    "notes": "Apresente o Painel como central de decisao do dia a dia. Diga: imagina ter um numero que te mostra todo dia se voce esta no lucro ou no prejuizo.",
    "glow": "glow-emerald",
    "inlineStyle": "",
    "html": "<div class=\"slide-inner\" style=\"max-width:900px;\">\n      <span class=\"eyebrow reveal\"><span class=\"eyebrow-dot\"></span> O que entregamos</span>\n      <div class=\"produto-header reveal\">\n        <div class=\"produto-logo\"><img src=\"https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Logo%20Painel%20do%20Dono%201920x1920.webp\" alt=\"\"></div>\n        <div>\n          <div class=\"produto-nome\">Painel <em>do Dono</em></div>\n          <div class=\"produto-tag\">SaaS &middot; Software de Gestao &middot; Sem contrato</div>\n        </div>\n      </div>\n      <div class=\"vc-grid\">\n        <div id=\"s15-1\" class=\"vc-card step\">\n          <div class=\"vc-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><line x1=\"18\" y1=\"20\" x2=\"18\" y2=\"10\"/><line x1=\"12\" y1=\"20\" x2=\"12\" y2=\"4\"/><line x1=\"6\" y1=\"20\" x2=\"6\" y2=\"14\"/></svg></div>\n          <div>\n            <div class=\"vc-card-title\">CMV Diário em Tempo Real</div>\n            <div class=\"vc-card-text\">Calcula o custo das mercadorias vendidas com os dados do seu restaurante &mdash; todo dia, não só no fim do mês.</div>\n          </div>\n        </div>\n        <div id=\"s15-2\" class=\"vc-card step\">\n          <div class=\"vc-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><circle cx=\"12\" cy=\"12\" r=\"10\"/><circle cx=\"12\" cy=\"12\" r=\"6\"/><circle cx=\"12\" cy=\"12\" r=\"2\"/></svg></div>\n          <div>\n            <div class=\"vc-card-title\">Ponto de Equilíbrio</div>\n            <div class=\"vc-card-text\">Quanto você precisa faturar por dia para cobrir todos os custos &mdash; visível antes de abrir o restaurante.</div>\n          </div>\n        </div>\n        <div id=\"s15-3\" class=\"vc-card step\">\n          <div class=\"vc-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><polyline points=\"23 6 13.5 15.5 8.5 10.5 1 18\"/><polyline points=\"17 6 23 6 23 12\"/></svg></div>\n          <div>\n            <div class=\"vc-card-title\">Resultado do Mês</div>\n            <div class=\"vc-card-text\">Lucro ou prejuízo visível antes do fim do mês. Sem surpresa no fechamento, sem esperar o contador.</div>\n          </div>\n        </div>\n      </div>\n    </div>"
  },
  {
    "id": 16,
    "steps": 3,
    "theme": "",
    "notes": "Como o dono usa o Painel na rotina. Reforce a simplicidade e a ausencia de contrato.",
    "glow": "glow-emerald",
    "inlineStyle": "",
    "html": "<div class=\"slide-inner\" style=\"max-width:900px;\">\n      <span class=\"eyebrow reveal\"><span class=\"eyebrow-dot\"></span> Como entregamos</span>\n      <div class=\"produto-header reveal\">\n        <div class=\"produto-logo\"><img src=\"https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Logo%20Painel%20do%20Dono%201920x1920.webp\" alt=\"\"></div>\n        <div>\n          <div class=\"produto-nome\">Painel <em>do Dono</em></div>\n          <div class=\"produto-tag\">SaaS &middot; Software de Gestao &middot; Sem contrato</div>\n        </div>\n      </div>\n      <div class=\"vc-grid\">\n        <div id=\"s16-1\" class=\"vc-card step\">\n          <div class=\"vc-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><rect x=\"2\" y=\"3\" width=\"20\" height=\"14\" rx=\"2\" ry=\"2\"/><line x1=\"8\" y1=\"21\" x2=\"16\" y2=\"21\"/><line x1=\"12\" y1=\"17\" x2=\"12\" y2=\"21\"/></svg></div>\n          <div>\n            <div class=\"vc-card-title\">Acesso Online Imediato</div>\n            <div class=\"vc-card-text\">Entra no painel, lança as compras e vendas do dia e o número aparece. Sem instalação, sem configuração.</div>\n          </div>\n        </div>\n        <div id=\"s16-2\" class=\"vc-card step\">\n          <div class=\"vc-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><polyline points=\"23 4 23 10 17 10\"/><polyline points=\"1 20 1 14 7 14\"/><path d=\"M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15\"/></svg></div>\n          <div>\n            <div class=\"vc-card-title\">Sem Contrato, Sem Fidelidade</div>\n            <div class=\"vc-card-text\">Cancela quando quiser. Você está no controle &mdash; o Painel precisa provar valor todo mês.</div>\n          </div>\n        </div>\n        <div id=\"s16-3\" class=\"vc-card step\">\n          <div class=\"vc-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><circle cx=\"12\" cy=\"12\" r=\"10\"/><polyline points=\"12 6 12 12 8 14\"/></svg></div>\n          <div>\n            <div class=\"vc-card-title\">5 Minutos por Dia</div>\n            <div class=\"vc-card-text\">Projetado para ser parte da rotina diária &mdash; rápido o suficiente para fazer entre o café e a abertura.</div>\n          </div>\n        </div>\n      </div>\n    </div>"
  },
  {
    "id": 17,
    "steps": 3,
    "theme": "",
    "notes": "O que muda na vida do dono com o Painel ativo. Fale em decisao e clareza.",
    "glow": "glow-emerald",
    "inlineStyle": "",
    "html": "<div class=\"slide-inner\" style=\"max-width:900px;\">\n      <span class=\"eyebrow reveal\"><span class=\"eyebrow-dot\"></span> O que você ganha</span>\n      <div class=\"produto-header reveal\">\n        <div class=\"produto-logo\"><img src=\"https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Logo%20Painel%20do%20Dono%201920x1920.webp\" alt=\"\"></div>\n        <div>\n          <div class=\"produto-nome\">Painel <em>do Dono</em></div>\n          <div class=\"produto-tag\">SaaS &middot; Software de Gestao &middot; Sem contrato</div>\n        </div>\n      </div>\n      <div class=\"vc-grid\">\n        <div id=\"s17-1\" class=\"vc-card gain step\">\n          <div class=\"vc-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3z\"/></svg></div>\n          <div>\n            <div class=\"vc-card-title\">Clareza Onde o Lucro Some</div>\n            <div class=\"vc-card-text\">Vê exatamente em qual linha de custo o dinheiro está vazando &mdash; sem precisar de relatório mensal.</div>\n          </div>\n        </div>\n        <div id=\"s17-2\" class=\"vc-card gain step\">\n          <div class=\"vc-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3z\"/></svg></div>\n          <div>\n            <div class=\"vc-card-title\">Decisão pelo Número, não pelo Instinto</div>\n            <div class=\"vc-card-text\">Para de decidir por feeling. Começa a decidir pelo dado do dia &mdash; compra, vende, corta com base no real.</div>\n          </div>\n        </div>\n        <div id=\"s17-3\" class=\"vc-card gain step\">\n          <div class=\"vc-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3z\"/></svg></div>\n          <div>\n            <div class=\"vc-card-title\">Fim das Surpresas no Fim do Mês</div>\n            <div class=\"vc-card-text\">Sabe o resultado antes de chegar lá. Não tem mais aquele susto de fechar o mês no prejuízo sem entender por quê.</div>\n          </div>\n        </div>\n      </div>\n    </div>"
  },
  {
    "id": 18,
    "steps": 4,
    "theme": "",
    "notes": "Agora a Mentoria. Aqui o diferencial e o acompanhamento humano, individual, ombro a ombro. Diga: isso e diferente de tudo que voce ja viu. Revele um card por vez.",
    "glow": "glow-gold",
    "inlineStyle": "",
    "html": "<div class=\"slide-inner\" style=\"max-width:900px;\">\n      <span class=\"eyebrow reveal\"><span class=\"eyebrow-dot\"></span> O que entregamos</span>\n      <div class=\"produto-header reveal\">\n        <div class=\"produto-logo\"><img src=\"https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Logo%20-%20Dono%2014.webp\" alt=\"\"></div>\n        <div>\n          <div class=\"produto-nome\">Mentoria <em>Dono 14%</em></div>\n          <div class=\"produto-tag\">Individual &middot; 6 meses &middot; Alto contato &middot; Baixa escala</div>\n        </div>\n      </div>\n      <div class=\"vc-grid\">\n        <div id=\"s18-1\" class=\"vc-card step\">\n          <div class=\"vc-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M2 18a1 1 0 0 0 1 1h18a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1H3a1 1 0 0 0-1 1v2z\"/><path d=\"M10 10V5a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v5\"/><path d=\"M4 15v-3a8 8 0 0 1 16 0v3\"/></svg></div>\n          <div>\n            <div class=\"vc-card-title\">De Engenheiro pra Dono</div>\n            <div class=\"vc-card-text\">Encontros individuais com Rodrigo &mdash; 1:1, todo mês, para construir o resultado juntos. Não é aula: é obra.</div>\n          </div>\n        </div>\n        <div id=\"s18-2\" class=\"vc-card step\">\n          <div class=\"vc-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"m3 21 1.9-5.7a8.5 8.5 0 1 1 3.8 3.8z\"/></svg></div>\n          <div>\n            <div class=\"vc-card-title\">Conversa de Obra</div>\n            <div class=\"vc-card-text\">Diagnóstico inicial do seu restaurante. Mapeamos onde está o buraco antes de começar a construir.</div>\n          </div>\n        </div>\n        <div id=\"s18-3\" class=\"vc-card step\">\n          <div class=\"vc-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z\"/><line x1=\"12\" y1=\"9\" x2=\"12\" y2=\"13\"/><line x1=\"12\" y1=\"17\" x2=\"12.01\" y2=\"17\"/></svg></div>\n          <div>\n            <div class=\"vc-card-title\">Parada Técnica</div>\n            <div class=\"vc-card-text\">Revisão profunda da operação em momentos críticos &mdash; acesso em 48 horas quando o restaurante precisar.</div>\n          </div>\n        </div>\n        <div id=\"s18-4\" class=\"vc-card step\">\n          <div class=\"vc-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2\"/><circle cx=\"9\" cy=\"7\" r=\"4\"/><path d=\"M23 21v-2a4 4 0 0 0-3-3.87\"/><path d=\"M16 3.13a4 4 0 0 1 0 7.75\"/></svg></div>\n          <div>\n            <div class=\"vc-card-title\">2 Cadeiras</div>\n            <div class=\"vc-card-text\">Você e seu sócio ou gerente &mdash; na mesma mesa, com o mesmo nível de acesso. Sem deixar ninguém de fora.</div>\n          </div>\n        </div>\n      </div>\n    </div>"
  },
  {
    "id": 19,
    "steps": 3,
    "theme": "",
    "notes": "Como funciona o dia a dia da Mentoria. Mostre que Rodrigo esta presente - nao e suporte por ticket.",
    "glow": "glow-gold",
    "inlineStyle": "",
    "html": "<div class=\"slide-inner\" style=\"max-width:900px;\">\n      <span class=\"eyebrow reveal\"><span class=\"eyebrow-dot\"></span> Como entregamos</span>\n      <div class=\"produto-header reveal\">\n        <div class=\"produto-logo\"><img src=\"https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Logo%20-%20Dono%2014.webp\" alt=\"\"></div>\n        <div>\n          <div class=\"produto-nome\">Mentoria <em>Dono 14%</em></div>\n          <div class=\"produto-tag\">Individual &middot; 6 meses &middot; Alto contato &middot; Baixa escala</div>\n        </div>\n      </div>\n      <div class=\"vc-grid\">\n        <div id=\"s19-1\" class=\"vc-card step\">\n          <div class=\"vc-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><rect x=\"3\" y=\"4\" width=\"18\" height=\"18\" rx=\"2\" ry=\"2\"/><line x1=\"16\" y1=\"2\" x2=\"16\" y2=\"6\"/><line x1=\"8\" y1=\"2\" x2=\"8\" y2=\"6\"/><line x1=\"3\" y1=\"10\" x2=\"21\" y2=\"10\"/></svg></div>\n          <div>\n            <div class=\"vc-card-title\">Reunião Mensal de Construção</div>\n            <div class=\"vc-card-text\">Videochamada individual com Rodrigo todo mês &mdash; para revisar o que foi feito e definir o próximo passo.</div>\n          </div>\n        </div>\n        <div id=\"s19-2\" class=\"vc-card step\">\n          <div class=\"vc-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><rect x=\"5\" y=\"2\" width=\"14\" height=\"20\" rx=\"2\" ry=\"2\"/><line x1=\"12\" y1=\"18\" x2=\"12.01\" y2=\"18\"/></svg></div>\n          <div>\n            <div class=\"vc-card-title\">WhatsApp Todo Dia</div>\n            <div class=\"vc-card-text\">Resposta de Rodrigo no mesmo dia, durante toda a mentoria. Não é uma fila de suporte &mdash; é um engenheiro de plantão.</div>\n          </div>\n        </div>\n        <div id=\"s19-3\" class=\"vc-card step\">\n          <div class=\"vc-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><circle cx=\"12\" cy=\"12\" r=\"10\"/><line x1=\"12\" y1=\"8\" x2=\"12\" y2=\"12\"/><line x1=\"12\" y1=\"16\" x2=\"12.01\" y2=\"16\"/></svg></div>\n          <div>\n            <div class=\"vc-card-title\">Parada Técnica em 48h</div>\n            <div class=\"vc-card-text\">Quando surgir urgência &mdash; fornecedor, crise de caixa, prato fora do custo &mdash; revisão profunda agendada em dois dias.</div>\n          </div>\n        </div>\n      </div>\n    </div>"
  },
  {
    "id": 20,
    "steps": 3,
    "theme": "",
    "notes": "A transformacao real da Mentoria. Fale em responsabilidade compartilhada.",
    "glow": "glow-gold",
    "inlineStyle": "",
    "html": "<div class=\"slide-inner\" style=\"max-width:900px;\">\n      <span class=\"eyebrow reveal\"><span class=\"eyebrow-dot\"></span> O que você ganha</span>\n      <div class=\"produto-header reveal\">\n        <div class=\"produto-logo\"><img src=\"https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Logo%20-%20Dono%2014.webp\" alt=\"\"></div>\n        <div>\n          <div class=\"produto-nome\">Mentoria <em>Dono 14%</em></div>\n          <div class=\"produto-tag\">Individual &middot; 6 meses &middot; Alto contato &middot; Baixa escala</div>\n        </div>\n      </div>\n      <div class=\"vc-grid\">\n        <div id=\"s20-1\" class=\"vc-card gain step\">\n          <div class=\"vc-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3z\"/></svg></div>\n          <div>\n            <div class=\"vc-card-title\">Nunca Decide Sozinho</div>\n            <div class=\"vc-card-text\">Alguém que conhece seu restaurante de dentro para fora &mdash; junto em cada decisão difícil, sem cobrar por hora.</div>\n          </div>\n        </div>\n        <div id=\"s20-2\" class=\"vc-card gain step\">\n          <div class=\"vc-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3z\"/></svg></div>\n          <div>\n            <div class=\"vc-card-title\">Resultado Compartilhado</div>\n            <div class=\"vc-card-text\">Se não chegar em 14%, a gente descobre junto por que. A responsabilidade não é só sua &mdash; é do Engenheiro também.</div>\n          </div>\n        </div>\n        <div id=\"s20-3\" class=\"vc-card gain step\">\n          <div class=\"vc-icon\"><svg width=\"22\" height=\"22\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.5\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3z\"/></svg></div>\n          <div>\n            <div class=\"vc-card-title\">6 Meses com Direção Clara</div>\n            <div class=\"vc-card-text\">Você sabe o próximo passo, sempre. Sem perder meses tentando descobrir sozinho o que está errado.</div>\n          </div>\n        </div>\n      </div>\n    </div>"
  },
  {
    "id": 21,
    "steps": 0,
    "theme": "cover",
    "notes": "MOMENTO DE OUVIR. Faca a pergunta e CALE A BOCA. Espere a resposta do Delane. Nunca responda antes dele terminar.",
    "glow": "",
    "inlineStyle": "justify-content:center; align-items:center; text-align:center;",
    "html": "<div class=\"img-bg overlay-heavy\"\n         style=\"background-image: url('https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Fundo%20Hero%20Dono%2014.webp');\"></div>\n    <div style=\"position:absolute; inset:0; z-index:1; pointer-events:none;\n                background: radial-gradient(ellipse 65% 55% at 50% 50%, hsla(36,55%,62%,0.10) 0%, transparent 65%);\"></div>\n    <div class=\"slide-inner\" style=\"position:relative; z-index:2; max-width:820px; margin:0 auto;\">\n      <span class=\"eyebrow reveal\" style=\"margin-bottom:32px;\"><span class=\"eyebrow-dot\"></span> Perspectiva</span>\n      <h2 class=\"h2 reveal d1\" style=\"font-size:clamp(2.4rem,5.5vw,4.4rem); line-height:1.1;\">\n        De tudo o que falamos até aqui,<br>o que mais fez sentido <em>para você?</em>\n      </h2>\n      <div class=\"divider reveal d2\" style=\"max-width:140px; margin:36px auto;\"></div>\n    </div>"
  },
  {
    "id": 22,
    "steps": 0,
    "theme": "cover",
    "notes": "Faca a pergunta e deixe o silencio trabalhar. Cada objecao que ele trouxer e material para voce trabalhar.",
    "glow": "",
    "inlineStyle": "justify-content:center; align-items:center; text-align:center;",
    "html": "<div class=\"img-bg overlay-heavy\"\n         style=\"background-image: url('https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Fundo%20Hero%20Dono%2014.webp');\"></div>\n    <div style=\"position:absolute; inset:0; z-index:1; pointer-events:none;\n                background: radial-gradient(ellipse 65% 55% at 50% 50%, hsla(36,55%,62%,0.10) 0%, transparent 65%);\"></div>\n    <div class=\"slide-inner\" style=\"position:relative; z-index:2; max-width:820px; margin:0 auto;\">\n      <span class=\"eyebrow reveal\" style=\"margin-bottom:32px;\"><span class=\"eyebrow-dot\"></span> Comprometimento</span>\n      <h2 class=\"h2 reveal d1\" style=\"font-size:clamp(2.4rem,5.5vw,4.2rem); line-height:1.15;\">\n        Então, o que falta para você <em>se tornar nosso mentorado?</em>\n      </h2>\n      <div class=\"divider reveal d2\" style=\"max-width:140px; margin:36px auto;\"></div>\n    </div>"
  },
  {
    "id": 23,
    "steps": 0,
    "theme": "",
    "notes": "Mostre o custo invisivel de manter o CMV descontrolado. Nao fale - deixe os numeros falarem. Pause em cima do R$ 48.000/ano.",
    "glow": "",
    "inlineStyle": "justify-content:center; align-items:center; text-align:center;",
    "html": "<div style=\"position:absolute; inset:0; z-index:0; pointer-events:none;\n                background: radial-gradient(ellipse 70% 55% at 50% 50%, hsla(4,70%,40%,0.07) 0%, transparent 65%);\"></div>\n    <div class=\"slide-inner\" style=\"position:relative; z-index:1; max-width:840px; width:100%;\">\n      <span class=\"eyebrow reveal\"><span class=\"eyebrow-dot\"></span> O que acontece sem o método</span>\n      <h2 class=\"h2 reveal d1\" style=\"font-size:clamp(1.5rem,2.8vw,2.2rem); margin-bottom:36px;\">\n        Cada <strong style=\"color:hsl(4,70%,72%);\">2% a mais de CMV</strong><br>\n        é <em style=\"color:hsl(4,70%,72%);\">R$ 48.000 por ano</em> saindo do seu lucro\n      </h2>\n      <div class=\"cmv-grid reveal d2\">\n        <div class=\"cmv-col bad\">\n          <div class=\"cmv-col-icon\">&#128201;</div>\n          <div class=\"cmv-col-label\">Hoje &mdash; sem controle</div>\n          <div class=\"cmv-col-value\">CMV descontrolado</div>\n          <div class=\"cmv-col-sub\">R$ 4.000 por mês<br>saindo do lucro</div>\n          <div class=\"cmv-col-total\">R$ 48.000/ano</div>\n        </div>\n        <div class=\"cmv-arrow\">&rarr;</div>\n        <div class=\"cmv-col good\">\n          <div class=\"cmv-col-icon\">&#128200;</div>\n          <div class=\"cmv-col-label\">Com o método</div>\n          <div class=\"cmv-col-value\">CMV monitorado</div>\n          <div class=\"cmv-col-sub\">Margem controlada<br>todos os dias</div>\n          <div class=\"cmv-col-total\">14% de lucro</div>\n        </div>\n      </div>\n    </div>"
  },
  {
    "id": 24,
    "steps": 7,
    "theme": "",
    "notes": "Revele CADA ITEM com uma pausa entre eles. Deixe o valor de cada componente pousar antes de avancar. Ao mostrar o total, aguarde a reacao.",
    "glow": "",
    "inlineStyle": "justify-content:center; align-items:center;",
    "html": "<div class=\"slide-inner\" style=\"max-width:860px; width:100%;\">\n      <span class=\"eyebrow reveal\"><span class=\"eyebrow-dot\"></span> Tudo que está incluído</span>\n      <h2 class=\"h2 reveal d1\" style=\"font-size:clamp(1.4rem,2.4vw,2rem); margin-bottom:28px; white-space:nowrap;\">\n        O que você recebe na <em>Mentoria Dono 14%</em>\n      </h2>\n      <div style=\"display:flex; flex-direction:column; gap:10px; width:100%;\">\n\n        <div id=\"s24-1\" class=\"step\" style=\"display:flex; justify-content:space-between; align-items:center;\n             padding:14px 24px; background:var(--bg-card); border:1px solid var(--border); border-radius:12px;\">\n          <span style=\"font-family:var(--sans); font-size:1rem; color:var(--cream-80);\">Projeto 14% <span style=\"color:var(--cream-40); font-size:0.85rem;\">&mdash; curso completo DCAL</span></span>\n          <span style=\"font-family:var(--serif); font-weight:700; font-size:1.05rem; color:var(--gold-100); text-decoration:line-through; opacity:0.7;\">R$ 1.497</span>\n        </div>\n\n        <div id=\"s24-2\" class=\"step\" style=\"display:flex; justify-content:space-between; align-items:center;\n             padding:14px 24px; background:var(--bg-card); border:1px solid var(--border); border-radius:12px;\">\n          <span style=\"font-family:var(--sans); font-size:1rem; color:var(--cream-80);\">Painel do Dono <span style=\"color:var(--cream-40); font-size:0.85rem;\">&mdash; 6 meses de acesso</span></span>\n          <span style=\"font-family:var(--serif); font-weight:700; font-size:1.05rem; color:var(--gold-100); text-decoration:line-through; opacity:0.7;\">R$ 582</span>\n        </div>\n\n        <div id=\"s24-3\" class=\"step\" style=\"display:flex; justify-content:space-between; align-items:center;\n             padding:14px 24px; background:var(--bg-card); border:1px solid var(--border); border-radius:12px;\">\n          <span style=\"font-family:var(--sans); font-size:1rem; color:var(--cream-80);\">Conversa de Obra <span style=\"color:var(--cream-40); font-size:0.85rem;\">&mdash; diagnóstico inicial do restaurante</span></span>\n          <span style=\"font-family:var(--serif); font-weight:700; font-size:1.05rem; color:var(--gold-100); text-decoration:line-through; opacity:0.7;\">R$ 3.000</span>\n        </div>\n\n        <div id=\"s24-4\" class=\"step\" style=\"display:flex; justify-content:space-between; align-items:center;\n             padding:14px 24px; background:var(--bg-card); border:1px solid var(--border); border-radius:12px;\">\n          <span style=\"font-family:var(--sans); font-size:1rem; color:var(--cream-80);\">7 encontros Engenheiro pra Dono <span style=\"color:var(--cream-40); font-size:0.85rem;\">&mdash; 1:1 com Rodrigo</span></span>\n          <span style=\"font-family:var(--serif); font-weight:700; font-size:1.05rem; color:var(--gold-100); text-decoration:line-through; opacity:0.7;\">R$ 7.000</span>\n        </div>\n\n        <div id=\"s24-5\" class=\"step\" style=\"display:flex; justify-content:space-between; align-items:center;\n             padding:14px 24px; background:var(--bg-card); border:1px solid var(--border); border-radius:12px;\">\n          <span style=\"font-family:var(--sans); font-size:1rem; color:var(--cream-80);\">2 Paradas Técnicas <span style=\"color:var(--cream-40); font-size:0.85rem;\">&mdash; revisão profunda da operação</span></span>\n          <span style=\"font-family:var(--serif); font-weight:700; font-size:1.05rem; color:var(--gold-100); text-decoration:line-through; opacity:0.7;\">R$ 2.000</span>\n        </div>\n\n        <div id=\"s24-6\" class=\"step\" style=\"display:flex; justify-content:space-between; align-items:center;\n             padding:14px 24px; background:var(--bg-card); border:1px solid var(--border); border-radius:12px;\">\n          <span style=\"font-family:var(--sans); font-size:1rem; color:var(--cream-80);\">Segunda Cadeira <span style=\"color:var(--cream-40); font-size:0.85rem;\">&mdash; sócio ou gerente incluso</span></span>\n          <span style=\"font-family:var(--serif); font-weight:700; font-size:1.05rem; color:var(--gold-100); text-decoration:line-through; opacity:0.7;\">R$ 5.000</span>\n        </div>\n\n        <div id=\"s24-7\" class=\"step\" style=\"display:flex; justify-content:space-between; align-items:center;\n             padding:18px 24px; background:hsla(36,55%,62%,0.10); border:1.5px solid var(--gold);\n             border-radius:12px; margin-top:4px;\">\n          <span style=\"font-family:var(--serif); font-weight:700; font-size:1.1rem; color:var(--cream);\">Valor total separado</span>\n          <span style=\"font-family:var(--serif); font-weight:900; font-size:1.3rem; color:var(--gold); text-decoration:line-through;\">R$ 19.079</span>\n        </div>\n\n      </div>\n    </div>"
  },
  {
    "id": 25,
    "steps": 0,
    "theme": "cover",
    "notes": "Faca a pergunta e PARE. O silencio e intencional - deixe o Delane falar o numero que esta na cabeca dele. O que ele disser vai calibrar sua resposta antes de mostrar o preco real.",
    "glow": "",
    "inlineStyle": "justify-content:center; align-items:center; text-align:center;",
    "html": "<div class=\"img-bg overlay-heavy\"\n         style=\"background-image: url('https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Fundo%20Hero%20Dono%2014.webp');\"></div>\n    <div style=\"position:absolute; inset:0; z-index:1; pointer-events:none;\n                background: radial-gradient(ellipse 65% 55% at 50% 50%, hsla(36,55%,62%,0.10) 0%, transparent 65%);\"></div>\n    <div class=\"slide-inner\" style=\"position:relative; z-index:2; max-width:820px; margin:0 auto;\">\n      <span class=\"eyebrow reveal\" style=\"margin-bottom:32px;\"><span class=\"eyebrow-dot\"></span> Decisão</span>\n      <h2 class=\"h2 reveal d1\" style=\"font-size:clamp(1.9rem,4.5vw,3.6rem); line-height:1.18;\">\n        Agora que você já conhece<br>todo o programa,<br><em>quanto você está disposto<br>a investir?</em>\n      </h2>\n      <div class=\"divider reveal d2\" style=\"max-width:140px; margin:36px auto;\"></div>\n    </div>"
  },
  {
    "id": 26,
    "steps": 1,
    "theme": "",
    "notes": "Apresente o valor com confianca e uma pausa logo depois. Deixe o numero R$ 12.000 pousar. Sem pressa para avancar.",
    "glow": "",
    "inlineStyle": "justify-content:center; align-items:center; text-align:center;",
    "html": "<div style=\"position:absolute; inset:0; z-index:0; pointer-events:none;\n                background: radial-gradient(ellipse 70% 50% at 50% 50%, hsla(36,55%,62%,0.08) 0%, transparent 65%);\"></div>\n    <div class=\"slide-inner\" style=\"position:relative; z-index:1; max-width:680px; width:100%;\">\n      <span class=\"eyebrow reveal\"><span class=\"eyebrow-dot\"></span> Investimento</span>\n      <h2 class=\"h2 reveal d1\" style=\"font-size:clamp(1.6rem,3vw,2.2rem); margin-bottom:32px;\">\n        Sua entrada na <em>Mentoria Dono 14%</em>\n      </h2>\n      <div id=\"s26-1\" class=\"step\" style=\"margin:0 auto; max-width:520px;\">\n        <div style=\"padding:40px 48px; background:var(--bg-card); border:1.5px solid var(--border-gold); border-radius:20px;\">\n          <p style=\"font-family:var(--sans); font-size:0.8rem; color:var(--cream-40); text-transform:uppercase; letter-spacing:0.14em; margin-bottom:6px;\">À vista</p>\n          <p style=\"font-family:var(--serif); font-weight:900; font-size:clamp(2.8rem,6vw,4rem); line-height:1;\n                    background:var(--grad-text); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; padding-right:4px;\">R$ 12.000</p>\n          <div class=\"divider\" style=\"margin:20px auto; max-width:80px;\"></div>\n          <p style=\"font-family:var(--sans); font-size:0.8rem; color:var(--cream-40); text-transform:uppercase; letter-spacing:0.14em; margin-bottom:6px;\">Ou parcelado</p>\n          <p style=\"font-family:var(--serif); font-weight:700; font-size:clamp(1.4rem,3vw,1.9rem); color:var(--cream);\">10&times; de <span style=\"color:var(--gold);\">R$ 1.500</span></p>\n        </div>\n      </div>\n    </div>"
  },
  {
    "id": 27,
    "steps": 0,
    "theme": "",
    "notes": "A garantia remove o risco. Apresente com calma: se em 30 dias voce nao ver clareza, devolvemos tudo - sem burocracia. Isso fecha o medo de errar.",
    "glow": "",
    "inlineStyle": "justify-content:center; align-items:center; text-align:center;",
    "html": "<div style=\"position:absolute; inset:0; z-index:0; pointer-events:none;\n                background: radial-gradient(ellipse 65% 55% at 50% 50%, hsla(145,50%,30%,0.08) 0%, transparent 65%);\"></div>\n    <div class=\"slide-inner\" style=\"position:relative; z-index:1; max-width:640px; width:100%;\">\n      <div class=\"reveal\" style=\"margin-bottom:20px; display:flex; justify-content:center;\"><svg width=\"64\" height=\"64\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" style=\"color:hsl(145,50%,65%); filter:drop-shadow(0 0 20px hsla(145,50%,50%,0.5));\"><path d=\"M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z\"/><path d=\"m9 12 2 2 4-4\"/></svg></div>\n      <h2 class=\"h2 reveal d1\" style=\"font-size:clamp(2rem,4vw,3rem); line-height:1.15; margin-bottom:12px;\">\n        Garantia de <em style=\"color:hsl(145,50%,75%);\">30 dias</em>\n      </h2>\n      <p class=\"sub reveal d2\" style=\"font-size:clamp(0.95rem,1.4vw,1.15rem); color:var(--cream-60); max-width:460px; margin:0 auto 36px; line-height:1.65;\">\n        Se em 30 dias você não ver clareza no caminho,<br>\n        devolvemos o investimento integral.<br>\n        Sem burocracia. Sem pergunta difícil.\n      </p>\n      <div class=\"reveal d3\" style=\"display:flex; justify-content:center; gap:16px; flex-wrap:wrap;\">\n        <div style=\"display:flex; align-items:center; gap:10px; padding:14px 22px; background:hsla(145,50%,50%,0.08); border:1px solid hsla(145,50%,50%,0.25); border-radius:12px;\">\n          <span style=\"font-size:1.1rem; color:hsl(145,50%,65%);\">&#10003;</span>\n          <span style=\"font-family:var(--sans); font-size:0.88rem; color:hsl(145,50%,70%);\">Devolução integral</span>\n        </div>\n        <div style=\"display:flex; align-items:center; gap:10px; padding:14px 22px; background:hsla(145,50%,50%,0.08); border:1px solid hsla(145,50%,50%,0.25); border-radius:12px;\">\n          <span style=\"font-size:1.1rem; color:hsl(145,50%,65%);\">&#10003;</span>\n          <span style=\"font-family:var(--sans); font-size:0.88rem; color:hsl(145,50%,70%);\">Sem burocracia</span>\n        </div>\n        <div style=\"display:flex; align-items:center; gap:10px; padding:14px 22px; background:hsla(145,50%,50%,0.08); border:1px solid hsla(145,50%,50%,0.25); border-radius:12px;\">\n          <span style=\"font-size:1.1rem; color:hsl(145,50%,65%);\">&#10003;</span>\n          <span style=\"font-family:var(--sans); font-size:0.88rem; color:hsl(145,50%,70%);\">30 dias completos</span>\n        </div>\n      </div>\n    </div>"
  },
  {
    "id": 28,
    "steps": 0,
    "theme": "cover",
    "notes": "Tom firme, olho no olho. Sem rodeios. Diga exatamente: chegou a hora de fazer nosso pacto. Nao preencha o silencio depois.",
    "glow": "",
    "inlineStyle": "justify-content:center; align-items:center; text-align:center;",
    "html": "<div class=\"img-bg overlay-heavy\"\n         style=\"background-image: url('https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Fundo%20Hero%20Dono%2014.webp');\"></div>\n    <div style=\"position:absolute; inset:0; z-index:1; pointer-events:none;\n                background: radial-gradient(ellipse 65% 55% at 50% 50%, hsla(36,55%,62%,0.14) 0%, transparent 65%);\"></div>\n    <div class=\"slide-inner\" style=\"position:relative; z-index:2; max-width:800px; margin:0 auto;\">\n      <div class=\"cta-pacto reveal\">\n        <div style=\"margin-bottom:20px; display:flex; justify-content:center;\"><svg width=\"48\" height=\"48\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.3\" stroke-linecap=\"round\" stroke-linejoin=\"round\" style=\"color:var(--gold); filter:drop-shadow(0 0 16px hsla(36,55%,62%,0.6));\"><polygon points=\"13 2 3 14 12 14 11 22 21 10 12 10 13 2\"/></svg></div>\n        <h2 class=\"h2\" style=\"font-size:clamp(2.2rem,5vw,3.6rem); line-height:1.1; margin-bottom:18px;\">\n          Chegou a hora de fazer<br><em>nosso Pacto</em>\n        </h2>\n        <div class=\"divider\" style=\"max-width:140px; margin:0 auto 24px;\"></div>\n        <p class=\"sub\" style=\"font-size:clamp(0.95rem,1.5vw,1.15rem); color:var(--cream-60); max-width:440px; margin:0 auto; line-height:1.75;\">\n          Você de um lado.<br>\n          Eu do outro.<br>\n          O restaurante no centro.<br>\n          <strong style=\"color:var(--cream);\">A responsabilidade, dividida.</strong>\n        </p>\n      </div>\n    </div>"
  },
  {
    "id": 29,
    "steps": 0,
    "theme": "cover",
    "notes": "Slide de encerramento. Momento de silencio e contato visual. Nao preencha o silencio.",
    "glow": "",
    "inlineStyle": "justify-content:center; align-items:center; text-align:center;",
    "html": "<div class=\"img-bg overlay-heavy\"\n         style=\"background-image: url('https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Fundo%20Hero%20Dono%2014.webp');\"></div>\n    <div style=\"position:absolute; inset:0; z-index:1; pointer-events:none;\n                background: radial-gradient(ellipse 70% 60% at 50% 50%, hsla(36,55%,62%,0.12) 0%, transparent 65%);\"></div>\n    <div class=\"slide-inner\" style=\"position:relative; z-index:2; max-width:720px; margin:0 auto;\">\n      <div class=\"reveal\" style=\"margin-bottom:32px;\">\n        <img src=\"https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Logo%20-%20Dono%2014.webp\"\n             alt=\"Dono 14%\"\n             style=\"height:72px; width:auto; filter:drop-shadow(0 4px 24px hsla(36,55%,62%,0.4));\">\n      </div>\n      <div class=\"reveal d1\" style=\"margin-bottom:28px;\">\n        <img src=\"https://sizhdcrnfylimhsdfdnf.supabase.co/storage/v1/object/public/Imagens/Rodrigo%20Haertel.webp\"\n             alt=\"Rodrigo Haertel\"\n             style=\"width:96px; height:96px; border-radius:50%; object-fit:cover; object-position:top;\n                    border:2px solid var(--border-gold);\n                    filter:drop-shadow(0 4px 20px hsla(36,55%,62%,0.35));\">\n      </div>\n      <h2 class=\"h2 reveal d2\" style=\"font-size:clamp(2rem,5vw,3.6rem); line-height:1.15;\">\n        Lucro não é sorte.<br><em>É cardápio projetado.</em>\n      </h2>\n      <div class=\"divider reveal d3\" style=\"max-width:140px; margin:32px auto;\"></div>\n      <p class=\"sub reveal d4\" style=\"font-size:1rem; color:var(--cream-60); max-width:440px; margin:0 auto;\">\n        Rodrigo Haertel &middot; Dono 14%\n      </p>\n    </div>"
  }
];

const TOTAL = SLIDES.length;

// ── Converte string de style CSS em objeto React.CSSProperties ────────────────
function parseCSSStyle(style: string): React.CSSProperties {
  if (!style) return {};
  const result: Record<string, string> = {};
  style.split(";").forEach((decl) => {
    const [prop, ...rest] = decl.split(":");
    if (!prop || rest.length === 0) return;
    const key = prop.trim().replace(/-([a-z])/g, (_, c) => c.toUpperCase());
    result[key] = rest.join(":").trim();
  });
  return result as React.CSSProperties;
}

// ── Variantes clip-path ────────────────────────────────────────────────────────
const variants = {
  enter: (dir: number) => ({
    clipPath: dir > 0 ? "inset(0 0 0 100%)" : "inset(0 100% 0 0)",
    filter: "blur(14px)",
    scale: 0.97,
    opacity: 0,
  }),
  center: {
    clipPath: "inset(0 0 0 0%)",
    filter: "blur(0px)",
    scale: 1,
    opacity: 1,
  },
  exit: (dir: number) => ({
    clipPath: dir > 0 ? "inset(0 100% 0 0)" : "inset(0 0 0 100%)",
    filter: "blur(8px)",
    scale: 1.02,
    opacity: 0,
  }),
};

const slideTransition = {
  clipPath: { duration: 0.6, ease: [0.22, 1, 0.36, 1] as [number, number, number, number] },
  filter:   { duration: 0.5, ease: "easeOut" as const },
  scale:    { duration: 0.6, ease: [0.22, 1, 0.36, 1] as [number, number, number, number] },
  opacity:  { duration: 0.3, ease: "easeOut" as const },
};

// ── Counter animado 91% ───────────────────────────────────────────────────────
function countUp(el: HTMLElement, end: number, duration: number) {
  const startTime = performance.now();
  function frame(now: number) {
    const progress = Math.min((now - startTime) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(eased * end).toString();
    if (progress < 1) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}

// ── Cursor Glow ───────────────────────────────────────────────────────────────
function CursorGlow({ glow }: { glow: string }) {
  const rawX = useMotionValue(-9999);
  const rawY = useMotionValue(-9999);
  const x = useSpring(rawX, { stiffness: 110, damping: 20 });
  const y = useSpring(rawY, { stiffness: 110, damping: 20 });

  useEffect(() => {
    const h = (e: MouseEvent) => { rawX.set(e.clientX); rawY.set(e.clientY); };
    window.addEventListener("mousemove", h);
    return () => window.removeEventListener("mousemove", h);
  }, [rawX, rawY]);

  const glowRgb = glow === "glow-gold" ? "201,168,76" : "52,211,153";
  return (
    <motion.div
      id="cursor-glow"
      style={{ x, y, "--glow-rgb": glowRgb } as React.CSSProperties}
    />
  );
}

// ── Componente principal ──────────────────────────────────────────────────────
export default function Apresentacao() {
  const [cur, setCur]           = useState(1);
  const [direction, setDir]     = useState(1);
  const [shownSteps, setShown]  = useState(0);
  const [busy, setBusy]         = useState(false);
  const [notesOn, setNotesOn]   = useState(false);
  const slideRef = useRef<HTMLDivElement | null>(null);

  const slide    = SLIDES[cur - 1];
  const progress = ((cur - 1) / (TOTAL - 1)) * 100;

  const goTo = useCallback((next: number, dir: number) => {
    if (busy || next < 1 || next > TOTAL) return;
    setBusy(true);
    setDir(dir);
    setCur(next);
    setShown(0);
  }, [busy]);

  const advance = useCallback(() => {
    if (busy) return;
    const s = SLIDES[cur - 1];
    if (shownSteps < s.steps) {
      setShown(p => p + 1);
    } else {
      goTo(cur + 1, 1);
    }
  }, [busy, cur, shownSteps, goTo]);

  const retreat = useCallback(() => {
    if (busy) return;
    if (shownSteps > 0) {
      setShown(p => p - 1);
    } else {
      goTo(cur - 1, -1);
    }
  }, [busy, cur, shownSteps, goTo]);

  // Keyboard
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === " " || e.key === "PageDown") { e.preventDefault(); advance(); }
      if (e.key === "ArrowLeft"  || e.key === "PageUp")                    { e.preventDefault(); retreat(); }
      if (e.key === "n" || e.key === "N") setNotesOn(p => !p);
      if (e.key === "Escape") setNotesOn(false);
      if (e.key === "Home") goTo(1, -1);
      if (e.key === "End")  goTo(TOTAL, 1);
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [advance, retreat, goTo]);

  // Reveal .reveal elements — dispara cedo (250ms) para coincidir com a transição
  useEffect(() => {
    if (!busy) return;
    // Resetar reveals do slide anterior (já saindo) não é necessário —
    // AnimatePresence cria um novo DOM node para o slide entrante.
    const t = setTimeout(() => {
      // Buscar o slide pelo ref (mais confiável que querySelector)
      const el = slideRef.current;
      if (el) {
        const revs = el.querySelectorAll(".reveal");
        revs.forEach((r, i) => setTimeout(() => r.classList.add("visible"), i * 80));
      }
      setBusy(false);
    }, 250);
    return () => clearTimeout(t);
  }, [busy, cur]);

  // Step reveal via DOM (imediato — sem delay)
  useEffect(() => {
    const el = slideRef.current;
    if (!el) return;
    const s = SLIDES[cur - 1];
    for (let i = 1; i <= s.steps; i++) {
      const stepEl = el.querySelector(`#s${cur}-${i}`) as HTMLElement | null;
      if (stepEl) stepEl.classList.toggle("shown", i <= shownSteps);
    }
  }, [cur, shownSteps]);

  // 91% counter — slide 3
  useEffect(() => {
    if (cur === 3 && !busy) {
      const el = document.getElementById("big-num-91");
      if (el) { el.textContent = "0"; countUp(el, 91, 1400); }
    }
  }, [cur, busy]);

  // Dots — usar .active conforme o CSS original
  const stepDots = Array.from({ length: slide.steps }).map((_, i) => (
    <div
      key={i}
      className={`step-dot${i < shownSteps ? " active" : ""}`}
      onClick={(e) => { e.stopPropagation(); setShown(i + 1); }}
    />
  ));

  // Estilo inline original do slide (preserva justify-content:center etc.)
  const inlineStyleObj = parseCSSStyle(slide.inlineStyle);

  return (
    <div
      style={{ position: "fixed", inset: 0, overflow: "hidden",
               background: "hsl(165,50%,8%)", cursor: "pointer" }}
      onClick={advance}
    >
      <CursorGlow glow={slide.glow} />

      <motion.div
        id="progress-bar"
        animate={{ width: `${progress}%` }}
        transition={{ duration: 0.4, ease: "easeOut" }}
      />

      <div id="deck">
        <AnimatePresence custom={direction} mode="sync">
          <motion.div
            key={cur}
            custom={direction}
            variants={variants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={slideTransition}
            ref={slideRef}
            data-slide={cur}
            data-steps={slide.steps}
            data-theme={slide.theme || undefined}
            className={`slide${slide.glow ? ` ${slide.glow}` : ""}`}
            style={{
              position: "absolute",
              inset: 0,
              pointerEvents: "auto",
              // Inline styles originais do slide (justify-content:center etc.)
              ...inlineStyleObj,
            }}
            dangerouslySetInnerHTML={{ __html: slide.html }}
          />
        </AnimatePresence>
      </div>

      <div id="controls" onClick={(e) => e.stopPropagation()}>
        <button onClick={retreat} title="Anterior (←)">‹</button>
        <span id="slide-counter">{cur} / {TOTAL}</span>
        <div id="step-dots">{stepDots}</div>
        <button onClick={advance} title="Próximo (→)">›</button>
      </div>

      <AnimatePresence>
        {notesOn && slide.notes && (
          <motion.div
            id="speaker-notes"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
            transition={{ duration: 0.25 }}
            onClick={(e) => e.stopPropagation()}
          >
            <strong style={{ color: "var(--gold, #C9A84C)", fontSize: "11px",
                             textTransform: "uppercase", letterSpacing: "0.08em" }}>
              Notas — tecle N para fechar
            </strong>
            <p style={{ margin: "8px 0 0" }}>{slide.notes}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
