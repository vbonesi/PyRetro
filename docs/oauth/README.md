# Páginas para o consentimento OAuth

Arquivos estáticos prontos para revisão: `index.html`, `privacy.html`, `terms.html`
e `style.css`. Descrevem a integração **atual**: rclone no notebook, Drive somente
leitura e seletor Android. Não anunciar escrita de saves na nuvem ou login Google
nativo Android antes da implementação. Não contêm credenciais, IDs OAuth, contas
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
