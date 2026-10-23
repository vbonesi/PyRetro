# Adicionar ROM do celular à Biblioteca

`POST /api/library/add-rom`, JSON, com `X-PyRetro-CSRF` obtido em `GET /api/csrf`.
O celular precisa alcançar o servidor para cadastrar; offline conserva o pedido
localmente e pode reenviar depois. Não exige ROM/capa no PC ou no Drive.

```json
{"nome":"Nome do jogo (USA)","code":"PSP"}
```

Somente esses dois campos. `nome` é título/basename sem extensão e sem caminho,
não vazio, até 240 caracteres, sem controles ou barras. `code` deve ser um sistema
configurado cuja plataforma tenha mapeamento conhecido na Biblioteca. Plataforma
e fonte `rom:<code>` vêm do servidor, não do cliente.

201 quando cria; 200 quando já existe:

```json
{"ok":true,"id":"id-estavel","created":true,"code":"PSP","romName":"Nome do jogo (USA)","nome":"Nome do jogo (USA)","plataforma":"Sony - PSP","fontes":["rom:PSP"]}
```

Procura por nome normalizado + plataforma, depois aliases da mesma plataforma,
como o tracking. Reenvio não duplica. Preserva progresso, tempo, capa, aliases e
demais fontes existentes; apenas acrescenta a fonte ROM se necessário. Não marca
iniciado/local no PC e não importa arquivo. A transação usa o mesmo lock e gravação
atômica de `/api/library/track`. Editar progresso continua pelas rotas existentes.

`GET /api/tv/catalog` passa a incluir `id,code,romName` também no cadastro de ROM
sem arquivo/capa/cache remoto, com `local:false`. O app conserva sua presença local
SAF separada desse campo (que descreve o PC), associa o `id` retornado à ROM e
atualiza o catálogo. `romName` da resposta é o pedido; `nome` pode ser o nome
canônico do cadastro reaproveitado. Não apagar o vínculo local por essa diferença.

Erros JSON `{error:"mensagem"}`: 400 para corpo/campos/nome/code inválidos ou
plataforma não mapeada; 403 para CSRF ausente/inválido; 409 para mais de um cadastro
compatível (resolver duplicidade explicitamente); 413 para corpo acima do limite
global. Falha de armazenamento não é sucesso: manter pedido pendente e reconsultar.
Não enviar `campos`, `plataforma`, `fonte` ou caminho absoluto nessa rota.
