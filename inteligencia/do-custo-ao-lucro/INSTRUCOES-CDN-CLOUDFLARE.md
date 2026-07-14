# CDN via Cloudflare — docustoaolucro.com

**Objetivo:** colocar o Cloudflare (plano grátis) na frente do site pra servir os arquivos de pontos próximos do visitante. Ataca o gargalo real que sobrou no GTmetrix: ~1s de latência de conexão (TTFB 632ms + Connect 443ms) porque o servidor está no Brasil e o teste vem dos EUA. É o que falta pra nota ir de B pra A.

**Quem faz o quê:**
- **Rodrigo:** conta Cloudflare + revisar os registros + trocar os nameservers na Hostinger (Parte A).
- **Sócio:** validação técnica de e-mail, SSL e renovação de certificado (Parte B).
- Ideal fazer juntos, ~30 min. Não mexe no código.

**Risco real e único:** errar os registros de e-mail. Por isso a Parte A tem um passo dedicado a isso, e a Parte B confirma.

---

## Mapa atual do DNS (levantado hoje — use como conferência)

DNS hoje está na Hostinger (nameservers `hyperion.dns-parking.com` / `atlas.dns-parking.com`).

| Tipo | Nome | Valor | No Cloudflare deve ficar |
|---|---|---|---|
| A | docustoaolucro.com (raiz) | 62.72.11.136 | **Proxied** (nuvem laranja) |
| A | www | 62.72.11.136 | **Proxied** (laranja) |
| A | app | 62.72.11.136 | **Proxied** (laranja) |
| A | api | 62.72.11.136 | **Proxied** (laranja) |
| A | dev (homolog) | 62.72.11.136 | DNS only (cinza) — ver nota |
| MX | docustoaolucro.com | mx1.hostinger.com (prio 5), mx2.hostinger.com (prio 10) | **DNS only (cinza)** — E-MAIL |
| A | mail | 62.72.11.136 | **DNS only (cinza)** — E-MAIL |
| A | autoconfig | 34.120.251.119 | **DNS only (cinza)** — E-MAIL |
| TXT | docustoaolucro.com | `v=spf1 include:_spf.mail.hostinger.com include:amazonses.com ~all` | DNS only (TXT não tem proxy) |

**Regra de ouro:** tudo que é **e-mail (MX, mail, autoconfig, SPF/TXT, DKIM, DMARC)** fica **cinza (DNS only)**. O Cloudflare não faz proxy de e-mail; se ligar a nuvem laranja neles, o e-mail quebra. Só o que é **site/web (raiz, www, app, api)** fica **laranja (Proxied)** — é o que ganha CDN.

> **Nota sobre o `dev` (homolog):** deixar cinza (DNS only) pra não confundir testes de homologação com cache do CDN. O homolog não precisa de CDN.

---

## PARTE A — Rodrigo

### A1. Criar conta no Cloudflare
1. Acesse https://dash.cloudflare.com/sign-up e crie a conta (grátis).
2. Confirme o e-mail.

### A2. Adicionar o domínio
1. No painel: **Add a site** → digite `docustoaolucro.com`.
2. Escolha o plano **Free**.
3. O Cloudflare vai **escanear e importar** os registros DNS atuais automaticamente.

### A3. Conferir os registros importados (passo mais importante)
Compare a lista que o Cloudflare importou com a tabela "Mapa atual do DNS" acima. Confirme item por item:
- Os 4 registros de **e-mail** (MX mx1/mx2, A `mail`, A `autoconfig`, TXT do SPF) **existem** e estão como **DNS only (nuvem cinza)**.
- Os registros de **site** (raiz, www, app, api) existem apontando pra `62.72.11.136`.
- Se faltar qualquer registro de e-mail, **adicione manualmente** antes de seguir (peça o valor exato pro sócio se tiver dúvida). Não avance com e-mail faltando.

### A4. Marcar o que é site como Proxied
- Clique no ícone de nuvem de cada registro de **site** (raiz, www, app, api) e deixe **laranja (Proxied)**.
- Deixe os de **e-mail** e o **dev** em **cinza (DNS only)**.

### A5. Trocar os nameservers na Hostinger
O Cloudflare vai mostrar **2 nameservers** dele (algo como `xxx.ns.cloudflare.com`). Anote os dois.
1. Entre na **Hostinger** → painel do domínio `docustoaolucro.com` → **DNS / Nameservers**.
2. Troque de "nameservers da Hostinger" para **"usar nameservers personalizados"** e cole os 2 do Cloudflare.
3. Salve.
4. Volte no Cloudflare e clique em **Done, check nameservers**. A ativação leva de alguns minutos a algumas horas (propagação). O Cloudflare manda e-mail quando estiver ativo.

### A6. Avisar o sócio
Quando o Cloudflare confirmar que está ativo, avise o sócio pra ele fazer a Parte B. Não pule isso — sem a Parte B o HTTPS pode dar erro.

---

## PARTE B — Sócio (validação técnica)

### B1. Modo de SSL/TLS
No painel Cloudflare → **SSL/TLS** → **Overview** → defina o modo como **Full (strict)**.
Motivo: o openresty já tem certificado Let's Encrypt válido na origem. "Full (strict)" mantém a criptografia ponta a ponta. **Não** usar "Flexible" (causa loop de redirect e HTTP inseguro origem↔Cloudflare).

### B2. Renovação do Let's Encrypt (atenção)
Com o proxy do Cloudflare ligado, a renovação automática do certbot por desafio HTTP-01 (porta 80, `/.well-known/acme-challenge/`) pode falhar se o Cloudflare forçar HTTPS antes do desafio chegar na origem.
Duas saídas (escolher uma):
- **Recomendado:** migrar a renovação do certbot pra desafio **DNS-01** (via API token do Cloudflare), que não depende da porta 80.
- **Alternativa:** criar uma **Page Rule / Configuration Rule** no Cloudflare que faça *bypass* (sem cache, sem "Always HTTPS") só no caminho `*/.well-known/acme-challenge/*`.
Testar uma renovação manual (`certbot renew --dry-run`) depois de ligar o proxy.

### B3. IP real do visitante (analytics/Pixel/Clarity)
Com o proxy, a origem passa a ver o IP do Cloudflare, não do visitante. Se algum log/analytics da origem usa IP, ler o header **`CF-Connecting-IP`** (ou `X-Forwarded-For`) no openresty. O Meta Pixel/CAPI e o Clarity rodam no navegador, então não são afetados — mas se o CAPI server-side usa IP, ajustar pra ler `CF-Connecting-IP`.

### B4. Cache de assets
O Cloudflare já cacheia estáticos por extensão. Como os arquivos do site têm hash no nome (`index-xxxx.js`) e o nginx manda `immutable`, o cache do Cloudflare respeita. Opcional: ligar **Auto Minify** desligado (o Vite já minifica) e **Brotli** ligado (Cloudflare faz Brotli automático no edge — resolve aquele item que tínhamos deixado opcional).

### B5. Confirmar HTTP/2 e HTTP/3
O Cloudflare serve **HTTP/2 e HTTP/3 por padrão** no edge pra todos os hostnames proxados — inclusive o www. Ou seja, ligando o proxy, o problema do www em HTTP/1.1 (Parte 1) fica resolvido automaticamente pro visitante, mesmo que a origem siga HTTP/1.1. Confirmar em **SSL/TLS → Edge Certificates** que HTTP/2 e HTTP/3 estão "On".

---

## Como confirmar que deu certo (depois)

```bash
# protocolo servido pelo Cloudflare (deve ser HTTP/2)
curl -sI https://www.docustoaolucro.com/dono14 | head -1

# header do Cloudflare presente?
curl -sI https://www.docustoaolucro.com/dono14 | grep -i 'server\|cf-ray'
```
Deve aparecer `server: cloudflare` e uma linha `cf-ray:`. Aí rodar o GTmetrix de novo — a expectativa é o TTFB/Connect caírem bastante e a Performance subir pra faixa de A.

---

## Resumo de 1 linha
Rodrigo cria a conta Cloudflare e troca os nameservers na Hostinger (cuidando pra deixar e-mail em cinza); o sócio ajusta SSL pra "Full (strict)" e a renovação do certificado. Resultado: CDN global + HTTP/2 e HTTP/3 no edge pra todo mundo, incluindo o www.
