# Páginas para o consentimento OAuth

Arquivos estáticos prontos para revisão: `index.html`, `privacy.html`, `terms.html`
e `style.css`. Descrevem a integração **atual** (atualizada pelo Claude em 23/10, Android
0.12): login da Conta Google no app com escopo do Drive (lê ROMs/saves; só **cria** saves
novos ou pendências, nunca apaga/sobrescreve), rclone somente leitura no notebook e
seletor Android. Não contêm credenciais, IDs OAuth, contas
ou endereços de rede do usuário. Nenhuma hospedagem foi publicada nesta rodada.

Para publicar:

1. Hospedar estes quatro arquivos por HTTPS em domínio controlado pelo responsável.
2. Conferir os links públicos sem login e ajustar o contato se necessário.
3. No Google Cloud, preencher Branding com nome, contato de suporte, homepage e
   privacidade; usar o mesmo domínio para ambas. Verificar domínio quando exigido.
4. Rever os escopos/clientes realmente usados. Um cliente Android criado não significa
   que a funcionalidade esteja pronta. Produção e verificação são etapas distintas;
   escopos sensíveis/restritos podem exigir verificações adicionais.
5. Após a mudança de publicação autorizada pelo titular, reconectar o rclone
   interativamente se preciso e testar leitura. Não compartilhar tokens com agentes.

Em modo externo **Testing**, refresh tokens com escopos de Drive expiram em sete
dias. Mudar para produção remove essa condição específica, mas não torna tokens
permanentes: revogação e outras condições ainda se aplicam.
[Referência Google](https://developers.google.com/identity/protocols/oauth2/).

Requisitos de homepage/domínio e privacidade:
[políticas OAuth](https://developers.google.com/identity/protocols/oauth2/policies) e
[verificação de marca](https://developers.google.com/identity/protocols/oauth2/production-readiness/brand-verification).
Consulta em 23/10/2026. Publicar páginas não publica automaticamente o app OAuth.

## Hospedar no GitHub Pages (orientação de 23/10)

O repositório `vbonesi/PyRetro` é **público**, então o GitHub Pages é gratuito e serve por HTTPS.

1. GitHub → repositório PyRetro → **Settings → Pages** → *Build and deployment*: Source
   **Deploy from a branch**, Branch **main**, pasta **/docs** → Save. (Ou pelo terminal:
   `gh api -X POST repos/vbonesi/PyRetro/pages -f "source[branch]=main" -f "source[path]=/docs"`.)
2. Em 1–2 minutos as páginas ficam em
   `https://vbonesi.github.io/PyRetro/oauth/` (início),
   `https://vbonesi.github.io/PyRetro/oauth/privacy.html` e `.../oauth/terms.html`.
   Abrir sem login para conferir. Observação: a pasta `docs/` inteira fica navegável (já é
   pública no repositório; nada novo é exposto).
3. Google Cloud, projeto **PyRetro** → *Google Auth Platform* → **Branding**: nome do app,
   e-mail de suporte, logo (opcional), *Application home page* = URL do item 2, *Privacy policy* =
   `.../privacy.html`, *Terms of service* = `.../terms.html`. Em *Authorized domains*, adicionar
   `vbonesi.github.io` (o `github.io` é sufixo público, então esse subdomínio conta como seu).
   Se o Google pedir prova de posse: Google Search Console → adicionar a propriedade
   `https://vbonesi.github.io/PyRetro/` → método **arquivo HTML** → salvar o arquivo baixado em
   `docs/` do repositório, commit e push → Verificar.
4. **Audience** → *Publish app* (sair de Testing para In production).

O que muda ao publicar: o vencimento de 7 dias deixa de valer, mas os escopos do app são
**restritos** (`drive` completo no Android; o rclone usa `drive.readonly`, também restrito).
Em produção, app com escopo restrito **não verificado** mostra a tela "o Google não verificou
este app" e tem limite de 100 usuários; para uso pessoal (só a sua conta) isso é aceitável: basta
seguir em *Avançado → Acessar PyRetro (não seguro)* no primeiro consentimento. A verificação
completa (com avaliação de segurança paga para escopos restritos) só faz sentido se o app for
distribuído a outras pessoas. Um domínio próprio barato (com as páginas apontadas para o Pages)
é a alternativa se o Google recusar o `github.io` no Branding.
