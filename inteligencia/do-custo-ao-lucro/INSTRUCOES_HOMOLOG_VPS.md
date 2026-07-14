# Configurar `dev.docustoaolucro.com` no VPS — Instruções para o sócio

**Para:** sócio com acesso ao VPS Hostinger (62.72.11.136)
**De:** Rodrigo
**Tempo estimado:** 10–15 minutos
**Objetivo:** fazer `https://dev.docustoaolucro.com` funcionar como ambiente de homologação, roteando para o container Docker que já existe na porta 3054.

---

## Contexto rápido

O repositório `Do-Custo-ao-Lucro/docustoaolucro` já tem um workflow CI/CD que faz deploy automático da branch `homolog` para o container `docustoaolucro-front-homolog` (porta 3054 do VPS). O container já existe e roda no VPS — falta apenas configurar o nginx (openresty) para responder ao subdomínio `dev.docustoaolucro.com` e emitir o certificado SSL.

**O DNS já está configurado.** Já existe um CNAME para `dev.docustoaolucro.com` apontando para `docustoaolucro.com`. Só falta o nginx do VPS rotear corretamente.

---

## Passo 1 — Acessar o VPS

Conectar via SSH ou pelo Browser Terminal do hPanel da Hostinger:

```bash
ssh root@62.72.11.136
```

Ou no painel: **VPS → docustoaolucro (ou nome do servidor) → Browser Terminal**.

---

## Passo 2 — Diagnóstico (descobrir a estrutura atual)

Antes de criar qualquer arquivo, rodar estes comandos para entender como o servidor está organizado. **Cole a saída completa para o Rodrigo** se algo parecer estranho.

```bash
# 2.1 — Confirmar que os containers estão rodando
docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}"

# 2.2 — Confirmar versão do nginx (provavelmente openresty)
nginx -v 2>&1
which nginx

# 2.3 — Descobrir onde estão os arquivos de configuração
ls -la /etc/nginx/conf.d/ 2>/dev/null
ls -la /etc/nginx/sites-enabled/ 2>/dev/null
ls -la /usr/local/openresty/nginx/conf/ 2>/dev/null

# 2.4 — Localizar a config de docustoaolucro.com já existente
grep -rln "docustoaolucro.com" /etc/nginx/ /usr/local/openresty/ 2>/dev/null | head -5

# 2.5 — Confirmar que o certbot está instalado
which certbot && certbot --version
```

**Resultado esperado:**
- Dois containers rodando: `docustoaolucro-front-prod` (porta 3055) e `docustoaolucro-front-homolog` (porta 3054)
- nginx ou openresty instalado
- Pelo menos um arquivo com a config de `docustoaolucro.com` já existente
- certbot instalado

Se algum item falhar, parar e me reportar antes de seguir.

---

## Passo 3 — Criar a config do subdomínio `dev`

**Versão A — se o servidor usa estrutura `sites-available` / `sites-enabled` (Debian/Ubuntu padrão):**

```bash
cat > /etc/nginx/sites-available/dev.docustoaolucro.com.conf <<'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name dev.docustoaolucro.com;

    # Healthcheck rápido sem proxy
    location = /health {
        access_log off;
        return 200 'ok';
        add_header Content-Type text/plain;
    }

    location / {
        proxy_pass http://127.0.0.1:3054;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_read_timeout 90s;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
    }
}
EOF

ln -sf /etc/nginx/sites-available/dev.docustoaolucro.com.conf /etc/nginx/sites-enabled/dev.docustoaolucro.com.conf
```

**Versão B — se o servidor usa apenas `/etc/nginx/conf.d/`:**

```bash
cat > /etc/nginx/conf.d/dev.docustoaolucro.com.conf <<'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name dev.docustoaolucro.com;

    location = /health {
        access_log off;
        return 200 'ok';
        add_header Content-Type text/plain;
    }

    location / {
        proxy_pass http://127.0.0.1:3054;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_read_timeout 90s;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
    }
}
EOF
```

**Use a versão A se viu pasta `/etc/nginx/sites-enabled/` no diagnóstico, senão use a B.**

---

## Passo 4 — Validar e recarregar o nginx

```bash
# Testar a sintaxe da configuração
nginx -t

# Se aparecer "syntax is ok" e "test is successful", aplicar:
systemctl reload nginx

# Validar que o subdomínio está respondendo via HTTP
curl -I http://dev.docustoaolucro.com
```

**Resultado esperado:** HTTP 200 ou 301/302 (vai redirecionar pra HTTPS depois do passo 5).

Se der erro `nginx -t`, parar e reportar a saída exata.

---

## Passo 5 — Emitir certificado SSL via Let's Encrypt

```bash
certbot --nginx -d dev.docustoaolucro.com \
  --non-interactive \
  --agree-tos \
  -m rodrigo.haertel@gmail.com \
  --redirect
```

**O que esse comando faz:**
- Conecta no Let's Encrypt
- Valida que o domínio aponta pro servidor (via desafio HTTP-01)
- Emite certificado SSL gratuito
- Atualiza automaticamente a config do nginx para usar HTTPS
- Adiciona redirect HTTP → HTTPS

**Resultado esperado:**
```
Successfully deployed certificate for dev.docustoaolucro.com to /etc/nginx/...
```

---

## Passo 6 — Validar tudo funcionando

```bash
# Testar HTTPS
curl -I https://dev.docustoaolucro.com

# Testar healthcheck do container
curl https://dev.docustoaolucro.com/health
# Deve retornar: ok

# Testar o site em si
curl -s https://dev.docustoaolucro.com | head -20
```

**Resultado esperado:**
- HTTP 200 OK
- Headers com `Strict-Transport-Security` (vem do certbot)
- HTML do site começando com `<!doctype html>`

Se aparecer **502 Bad Gateway**, significa que o nginx não consegue se conectar ao container — verificar se `docker ps` ainda mostra o container `docustoaolucro-front-homolog` rodando.

---

## Passo 7 — Confirmar para o Rodrigo

Mandar pra o Rodrigo:

> "Pronto. dev.docustoaolucro.com está funcionando com SSL."

E o resultado do `curl -I https://dev.docustoaolucro.com` (cabeçalho HTTP).

---

## Troubleshooting

### Erro: `nginx -t` falha com "duplicate listen options"
Já existe um `default_server` em outra config. Adicionar a flag `listen 80;` sem `default_server`. O template já está sem.

### Erro: certbot diz "DNS problem"
Significa que o CNAME ainda não propagou. Esperar 5 minutos e tentar de novo. Pode também testar:
```bash
dig dev.docustoaolucro.com +short
```
Deve retornar o IP `62.72.11.136`. Se não retornar nada, o DNS não está configurado direito (nesse caso parar e reportar).

### Erro: 502 Bad Gateway depois de tudo configurado
O container `docustoaolucro-front-homolog` pode não estar rodando.
```bash
cd /opt/docustoaolucro/homolog
docker compose ps
docker compose up -d
```

### Reverter tudo se algo der errado
```bash
# Remover config
rm /etc/nginx/sites-enabled/dev.docustoaolucro.com.conf 2>/dev/null
rm /etc/nginx/sites-available/dev.docustoaolucro.com.conf 2>/dev/null
rm /etc/nginx/conf.d/dev.docustoaolucro.com.conf 2>/dev/null
# Recarregar
nginx -t && systemctl reload nginx
```

---

## Resumo do que vai existir depois

| URL | Container | Porta interna | Branch |
|---|---|---|---|
| https://docustoaolucro.com | docustoaolucro-front-prod | 3055 | main (produção) |
| https://dev.docustoaolucro.com | docustoaolucro-front-homolog | 3054 | homolog (homologação) |

A renovação do certificado SSL é automática (cron do certbot já configurado quando o domínio principal foi emitido).

Após esses passos, qualquer push na branch `homolog` vai disparar o GitHub Actions, que builda e atualiza o container, e a versão fica acessível em `https://dev.docustoaolucro.com` em ~2 minutos.
