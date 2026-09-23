# 🔒 Segurança — MusicClipStudio

> Open source e gratuito **não** significa descuidado. Este documento descreve
> o modelo de segurança do aplicativo, o que é protegido e como.

## Modelo de ameaça

O Studio roda **100% na sua máquina** (`127.0.0.1`), sem servidores externos
recebendo seus dados. Os ativos sensíveis são:

1. **Suas chaves de API** (bancos de mídia + HuggingFace)
2. **Suas senhas de conta** (login local do app)
3. **Seus projetos** (letras, mídia baixada, clipes renderizados)

## Como cada ativo é protegido

| Ativo | Proteção | Onde vive |
|---|---|---|
| Chaves de API por usuário | Criptografia **Fernet** (AES128-CBC + HMAC), chave local `.mcs_secret_key` com permissão `0600` | `output/usuarios.db` |
| Senhas das contas | Hash **PBKDF2-HMAC-SHA256**, 200.000 iterações, salt aleatório de 16 bytes, comparação em tempo constante (`hmac.compare_digest`) | `output/usuarios.db` |
| Força bruta no login | **5 tentativas erradas → bloqueio de 10 minutos** por usuário | em memória |
| Sessão | Cookie **`httponly` + `samesite=lax`**, token aleatório de 256 bits, expira em 30 dias; imune a XSS (JS não lê o cookie) | cookie do navegador |
| Segredo Fernet | Arquivo `0600` (só o dono do processo lê); criado já com permissão correta | `output/.mcs_secret_key` |
| Rede | Backend e frontend **só em `127.0.0.1`** — nada escutado na rede | `RUN_WEB.sh` |
| Chaves no `.env` | Fora do repositório (`.gitignore`); `.env.example` distribuído vazio | seu disco |

## O que o app NÃO faz

- **Não envia** suas chaves, letras ou mídia para nenhum servidor dos autores.
  As únicas chamadas externas são para as APIs dos **próprios bancos de mídia**
  (Pexels, Pixabay, …) e para o HuggingFace (download do modelo Whisper).
- **Não telemetria, não analytics, não rastreamento.**

## Limitações honestas

- A criptografia das chaves protege contra **quem só copiar o arquivo** do banco.
  Quem tiver acesso à sua **conta do sistema operacional** consegue decriptar
  (o segredo fica no mesmo disco) — igual a qualquer app local (navegadores,
  gerenciadores de senha sem vault do SO, etc.).
- O bloqueio de força bruta vive **em memória**: reiniciar o backend zera o contador.
  Suficiente para o cenário local; não é um sistema multiusuário de rede.
- HTTPS: desnecessário em `127.0.0.1`. Se você expuser o app na rede (não
  recomendado sem saber o que faz), coloque um reverse proxy com TLS na frente.

## Boas práticas para quem instala

1. Use uma senha de **8+ caracteres** no login do Studio (não reutilize a do e-mail).
2. As chaves de API criadas nos bancos são **suas** — não as compartilhe nem as
   cole em chats/fóruns. Se expuser uma, regenere no site do banco.
3. Faça backup do `output/` se quiser preservar contas/projetos; apague-o para
   zerar tudo (contas, chaves, sessões).
4. Mantenha a máquina e o FFmpeg atualizados — o app é tão seguro quanto o resto
   do sistema.

## Denúncia de vulnerabilidade

Encontrou algo? Abra uma issue marcada como `security` ou escreva direto para
o mantenedor. Por ser um projeto local, divulgação coordenada simples é suficiente.
