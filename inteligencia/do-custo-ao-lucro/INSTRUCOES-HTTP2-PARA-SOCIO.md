# Instruções para o sócio — Habilitar HTTP/2 no servidor (docustoaolucro.com)

**Para quem:** quem administra a VPS (62.72.11.136) e o openresty/nginx.
**Objetivo:** o site responde hoje em **HTTP/1.1**. Habilitar **HTTP/2** é a maior economia apontada pelo GTmetrix: **~1,2 segundo** no carregamento. Sem isso, a nota de performance não sobe de C para A.
**Risco:** baixíssimo. É uma alteração de 1 linha, testável antes de aplicar, com reload sem derrubar o site.
**Tempo:** 5 minutos.

---

## Como confirmar o problema (antes)

De qualquer máquina:

```bash
curl -sI --http2 https://www.docustoaolucro.com/ | head -1
```

Hoje retorna `HTTP/1.1 200 OK`. O alvo é `HTTP/2 200`.

---

## Onde mexer

O TLS (HTTPS) é terminado no **openresty** da VPS, que faz proxy para o container Docker. O HTTP/2 precisa ser ligado **no bloco `server` que escuta a 443 do openresty** — não no nginx de dentro do container.

Localizar o arquivo de configuração do site:

```bash
# Achar o server block do domínio
grep -rl "docustoaolucro" /usr/local/openresty/nginx/conf/ /etc/openresty/ /etc/nginx/ 2>/dev/null
```

Normalmente é algo como `/etc/nginx/sites-enabled/docustoaolucro.conf` ou dentro de `/usr/local/openresty/nginx/conf/conf.d/`.

---

## A alteração

Abra o arquivo e encontre a linha que escuta a porta 443. Vai estar parecida com:

```nginx
listen 443 ssl;
listen [::]:443 ssl;
```

### Se o openresty/nginx for versão **1.25.1 ou mais nova** (recomendado)

Mantenha o `listen` como está e adicione uma linha `http2 on;` dentro do mesmo bloco `server`:

```nginx
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;          # <-- adicionar esta linha
    server_name docustoaolucro.com www.docustoaolucro.com;
    ...
}
```

### Se for versão **anterior à 1.25.1**

Adicione `http2` direto no `listen`:

```nginx
listen 443 ssl http2;
listen [::]:443 ssl http2;
```

Para checar a versão: `openresty -v` ou `nginx -v`.

---

## Testar e aplicar (sem derrubar o site)

```bash
# 1. Validar a sintaxe — NÃO aplica nada ainda
openresty -t        # ou: nginx -t

# 2. Se aparecer "syntax is ok" e "test is successful", recarregar
openresty -s reload # ou: nginx -s reload   (ou: systemctl reload openresty)
```

O `reload` é graceful: não derruba conexões ativas.

---

## Confirmar que funcionou (depois)

```bash
curl -sI --http2 https://www.docustoaolucro.com/ | head -1
```

Tem que retornar `HTTP/2 200`. Pronto.

---

## Bônus opcional — Brotli (mais compressão que gzip)

O site já usa gzip. O Brotli comprime o JavaScript ~15-20% melhor, o que ajuda ainda mais no tempo de download (o bundle de JS é o maior peso da página). É opcional e só vale se o módulo já estiver disponível.

Verificar se o openresty foi compilado com brotli:

```bash
openresty -V 2>&1 | grep -o brotli
```

Se aparecer `brotli`, dá para habilitar adicionando no bloco `http` (ou no server):

```nginx
brotli on;
brotli_comp_level 5;
brotli_types text/plain text/css application/javascript application/json image/svg+xml;
```

Depois `openresty -t && openresty -s reload`. Se o módulo brotli **não** estiver compilado, ignore esta parte — não vale recompilar o openresty só por isso agora. O HTTP/2 é o que importa.

---

## Resumo do que pedir

1. Adicionar HTTP/2 no bloco 443 do openresty (1 linha).
2. `openresty -t` para validar.
3. `openresty -s reload` para aplicar.
4. Confirmar com `curl -sI --http2 https://www.docustoaolucro.com/`.

Qualquer dúvida na localização do arquivo, é só rodar o `grep` do passo "Onde mexer" e me mandar o caminho que aparecer.
