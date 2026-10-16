# Modo TV do PyRetro

Primeira etapa da integração com Steam Big Picture, criada em 15/10/2026.

## Acesso

- Na máquina: `http://127.0.0.1:8000/tv`.
- Pelo acesso HTTPS/Tailscale já configurado: acrescentar `/tv` ao endereço do PyRetro.
- A interface normal tem um link **Modo TV**. A versão TV oferece o retorno à interface completa.

O serviço `pyretro-gui` precisa estar ativo. Não há servidor adicional nem nova porta.
A rota usa os mesmos cabeçalhos de segurança e as mutações exigem o token CSRF existente.

## Navegação

Direcional ou analógico esquerdo navegam entre os botões e as capas. A confirma e
B volta. O mapeamento segue o padrão Gamepad do navegador; teclado também funciona
com setas, Enter, Tab e Esc. Pressione um botão para o navegador reconhecer o controle.
O controle precisa chegar ao navegador como gamepad; o perfil Steam Input deve ser
conferido na instalação final para evitar ações duplicadas de mouse/teclado.

Biblioteca e Jogando oferecem filtros por plataforma. ROMs leves e pesadas oferecem
seleção por sistema. Cada capa abre o progresso: iniciado, finalizado, platinado e
nota entre 0 e 11, com ajustes de 1 ou 0,1. **Salvar progresso** aplica todas as
mudanças juntas; Voltar descarta alterações não salvas. A cascata mantém platinado
como finalizado e iniciado; desmarcar iniciado desmarca os dois seguintes.

O catálogo pesado reaproveita o cache do Drive da GUI. Jogos só na nuvem aparecem
com **Baixar para o PC**, seguido de confirmação explícita. Durante o download é
possível voltar e navegar; o rodapé informa o resultado. O backend atual informa
início e resultado, sem percentual ou velocidade. Não recarregue a página durante
o download: o acompanhamento fica na sessão da página. Se a conexão cair, confira
a coleção antes de tentar novamente. O modo TV permite um download por vez na página;
outras abas e clientes continuam sujeitos às regras já existentes do backend.

## Integração com setup-linux-bonesi

Contrato da primeira etapa: abrir `http://127.0.0.1:8000/tv` num navegador com
Gamepad API, como aplicativo/tela cheia, por um atalho da Steam. HTTPS e localhost
são os contextos previstos para o controle. A instalação do atalho e a escolha do
navegador/perfil de Steam Input devem ser feitas no setup da máquina.

Esta etapa **ainda não executa emuladores**. O próximo bloco deve conectar um
lançador local ao `bonisarch-emulator` preparado no setup, validando sistema e ROM
local, arquivos associados e resultado do download antes de abrir o emulador.
Também precisa validar o retorno do foco ao navegador e à Steam ao sair do jogo,
inclusive no Steam Link. Sair do emulador encerra a sessão; finalizar o jogo é
uma decisão explícita do usuário.

## Validação

A suíte Python verifica rota/CSP, progresso em lote, preservação de outros campos
e recusa sem gravação parcial. A suíte `/tests/test_app.html` monta o modo TV
com APIs falsas, sem acessar dados reais, e verifica cascata, token CSRF,
restauração de foco, falha de gravação, confirmação de download, sucesso/falha SSE,
A/B simulados e largura de celular. Controle físico, Steam Input, download real
e Steam Link precisam de homologação na máquina.
