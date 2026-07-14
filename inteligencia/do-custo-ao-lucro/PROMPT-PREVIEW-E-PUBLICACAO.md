# Prompt — Preview local e publicação em HTML (pré-renderização)

> Cole este prompt no início de uma nova conversa. Ele define **como ver o preview das páginas sem publicar no dev** e **como entregar as LPs pagas como HTML estático** sem abandonar o `.tsx`.

---

## Contexto do projeto (não mude isto)

- Stack: **Vite + React 18 + react-router-dom v6 (BrowserRouter)**, `@vitejs/plugin-react-swc`, Tailwind + shadcn/Radix, Supabase.
- Páginas em `src/pages/*.tsx`. Rotas em `src/App.tsx` (`Index` é eager; o resto é `lazy`). Entrada em `src/main.tsx` com `createRoot`.
- Deploy automático: `git push` → GitHub Actions. Branch **`homolog`** → `dev.docustoaolucro.com`; branch **`main`** → `docustoaolucro.com`.
- As páginas são **arquivos únicos quase autossuficientes**: CSS num bloco `<style dangerouslySetInnerHTML>` + classes Tailwind. Imports externos = só `lucide-react` (ícones) e 1–2 hooks de `@/lib` (`useViewContent`, `trackMetaEvent`).
- Tracking (GTM/Pixel/Clarity) já está no `index.html`, com GTM adiado 1,5s / no primeiro gesto. **Não mexer nisso.**

**Decisão já tomada:** NÃO reescrever páginas em HTML na mão. A fonte continua `.tsx`. HTML é **saída de build** (pré-renderização), nunca arquivo editado à mão. Motivo: 17 páginas compartilham design system; HTML na mão vira copia-e-cola.

---

## Parte 1 — Preview SEM publicar no dev

Objetivo: parar de publicar no `homolog` só pra conferir visual. Dois modos:

### Modo A — Servidor local (para quando o Rodrigo edita)
1. Rodar `npm run dev` na raiz do repo (porta 8080).
2. Abrir `http://localhost:8080/<rota>` (ex.: `/desafio`, `/dono14`).
3. Atualização automática ao salvar (HMR). É o `.tsx` rodando de verdade.
- O assistente pode subir o dev server e tirar print via Claude in Chrome para validar, OU deixar a URL pro Rodrigo abrir.

### Modo B — Preview aqui no chat, sob demanda (para quando o assistente edita)
Quando o Rodrigo pedir "me mostra a `<página>`", o assistente deve gerar um **HTML autossuficiente** da página e exibir via `present_files`:
1. Transpilar o JSX da página (esbuild) OU buildar só aquela rota com Vite.
2. Resolver dependências: React/ReactDOM/lucide-react via CDN (esm.sh) **ou** bundle do Vite; mockar `useViewContent`/`trackMetaEvent` como no-op; injetar o bloco de CSS inline da própria página + Tailwind (config do projeto).
3. Salvar `preview-<pagina>.html` em outputs e mostrar com `present_files`.
- Validar que o visual bate com o real (cores emerald/ouro, Fraunces, seções na ordem).

---

## Parte 2 — Publicação em HTML (pré-renderização das LPs pagas)

Objetivo: as LPs de tráfego pago chegam ao visitante como **HTML estático** (pinta na hora), e o React só hidrata depois — sem travar a tela. Rodrigo continua editando `.tsx`.

**Rotas alvo (LPs pagas):** `/desafio`, `/dono14`, `/projeto14`, `/guia`, `/mentoria-cadastro`. (Confirmar a lista com o Rodrigo antes.)

### Como fazer
1. Escolher e **validar** uma ferramenta de SSG/prerender compatível com Vite + react-router + BrowserRouter. Candidatos, do menos invasivo ao mais:
   - `react-snap` (passo pós-build, puppeteer; exige trocar `createRoot`→`hydrateRoot` quando há HTML pré-renderizado).
   - script próprio com Puppeteer que renderiza cada rota e salva `index.html` por pasta.
   - `vite-react-ssg` (mais moderno, mas exige reestruturar o roteamento — só se os outros falharem).
2. Garantir **hidratação correta**: usar `hydrateRoot` nas rotas pré-renderizadas; manter `createRoot` onde não houver HTML.
3. O build final precisa emitir, por rota, um HTML completo (com o conteúdo visível dentro do `<div id="root">`, não vazio).
4. Servir no nginx/openserver com fallback de SPA preservado (rotas não pré-renderizadas continuam funcionando).

### O que NÃO pode quebrar (verificação obrigatória)
- `npm run build` passa **sem erro** antes de qualquer push (build já travou antes — sempre rodar local).
- **Nada de `manualChunks`** quebrando o React (já causou tela branca).
- Tracking: PageView do Pixel + CAPI continuam disparando uma vez, com dedupe por `event_id`.
- Formulários (ex.: `/mentoria-cadastro`) continuam enviando pro Supabase com `keepalive:true` + redirect imediato.
- Sem regressão visual: comparar print antes/depois em cada LP.
- A11y: `focus-visible` + `prefers-reduced-motion` preservados.

### Gotchas do repo (ler antes de editar)
- `Write`/`Edit` truncam arquivos > ~1000 linhas silenciosamente → arquivos grandes via Python/heredoc no bash; sempre conferir com `wc -l`.
- Edit que remove bytes em arquivo OneDrive deixa `\x00` no fim → `tail -c 50 | xxd` + `file`; build falha se houver null bytes.
- Sessões paralelas do Cowork commitam no mesmo repo → `git fetch` + `git pull --rebase` antes de push.
- Fluxo de publicação: editar/testar em `homolog` → validar em `dev.docustoaolucro.com` → merge `homolog`→`main`.
- Mantra: **sem planilhas** em nenhuma copy (`grep -i planilha` antes de publicar).

---

## Critério de pronto
- [ ] `npm run dev` documentado e funcionando para preview local.
- [ ] Fluxo de preview no chat funcionando para pelo menos 1 página.
- [ ] Pré-renderização ligada e validada em 1 LP paga (HTML estático no `view-source`, hidratação ok, tracking ok, sem regressão visual).
- [ ] Rollout para as demais LPs pagas.
- [ ] `npm run build` verde + push só depois de validar.
