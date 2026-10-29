# Saves PSP/3DS por jogo — consulta v1

`GET /api/mobile/saves/game?id=<ID da Biblioteca>` usa o `id` de
`/api/tv/catalog` ou `/api/library/add-rom`. Consulta sem escrita, sem rede/adb,
sem ler bytes de saves. Não precisa CSRF. 400 sem ID, 404 desconhecido;
resultado desconhecido ou plataforma não suportada retorna 200 com status.

Exemplo PSP identificado:

```json
{
  "schema":1,"id":"id-do-jogo","code":"PSP","status":"identified",
  "titleIds":["ULUS12345"],
  "candidates":[{"titleId":"ULUS12345","name":"Game (USA)","source":"redump-psp"}],
  "filters":[
    {"group":"psp-saves","kind":"psp-serial","titleId":"ULUS12345"},
    {"group":"psp-states","kind":"psp-serial","titleId":"ULUS12345"}
  ],
  "extdataStatus":"not-applicable","source":"URL do DAT PSP"
}
```

`status`: `identified`, `needs-choice`, `unknown`, `unsupported`. Só identified
preenche titleIds/filters automaticamente. Candidatos nunca autorizam copiar
todos: mostrar nome/região e pedir escolha, guardada pelo app por jogo/conta/raiz.
App pode armazenar a resposta para uso direto no Drive offline do notebook;
revalidar após renomear/corrigir cadastro ou trocar a ROM. A rota não comprova
presença de saves, compatibilidade entre versões nem que o emulador esteja fechado.

## PSP

Usa `core/serials.py`, índice Redump existente em `cache/serials_index.json`.
GET lê apenas o cache; ausente/inválido retorna unknown. Preparação explícita do
índice usa a função existente `serials.build_index()` (rede/escrita de cache;
nunca chamar por abertura automática da ficha). Nenhum download foi executado
para esta entrega. Fonte: [DAT PSP do libretro/Redump](https://github.com/libretro/libretro-database/blob/master/metadat/redump/Sony%20-%20PlayStation%20Portable.dat).

Serial `ULUS-12345` vira `ULUS12345`. Correspondência automática exige nome ou
alias exato, normalizando só Unicode, caixa e espaços, mantendo região/edição.
A normalização mais ampla do catálogo fornece apenas candidatos. Mais de um
serial, inclusive em aliases, exige escolha. Não fazer fuzzy match de títulos.

O filtro compara os nove caracteres iniciais do componente de pasta/arquivo,
depois de validar pelo `save_paths.accepted`: `ULUS12345DATA00/**` para saves,
`ULUS12345*.ppst/jpg/png` para states. Não confundir região ou usar simples busca
por substring. `core/game_save_ids.matches` é referência para espelhar no Kotlin.

## 3DS: cabeçalho local NCCH/NCSD

Fonte escolhida: Program ID de 64 bits do cabeçalho da própria ROM, conforme
[estruturas do Azahar](https://github.com/azahar-emu/azahar/blob/master/src/core/file_sys/ncch_container.h)
e [leitura NCSD/NCCH](https://github.com/azahar-emu/azahar/blob/master/src/core/file_sys/ncch_container.cpp).
É evidência da versão local; não depende de uma lista de nomes inferidos.
Lê no máximo dois cabeçalhos de 512 bytes, sem descriptografar ROM ou alterar
conteúdo. Magic em 0x100, Program ID little-endian em NCCH+0x118; NCSD usa
partição principal da tabela 0x120, offset/tamanho em unidades de 512 bytes.
Confere limites e aceita apenas aplicação base `00040000xxxxxxxx` não nula.

Consulta arquivos `.3ds/.cci/.cxi` correspondentes ao nome/aliases na raiz 3DS
ou na pasta do título, sem seguir symlinks. Diferentes IDs retornam candidatos;
candidato ilegível impede seleção automática (`incomplete:true`). CIA, arquivos
comprimidos, jogo só no celular/nuvem sem cabeçalho no PC e ausência de evidência
retornam unknown. O app pode espelhar `read_3ds_id` sobre a ROM SAF local para
esse caso, vinculando o resultado ao ID da Biblioteca; não derivar pelo filename,
product code, região ou ID do cadastro.

Para identificado: `source:"ncch-program-id"`, `titleIds:["0004000000123400"]`,
`filters:[{group:"3ds-saves",kind:"3ds-title",titleId:"0004000000123400",
high:"00040000",low:"00123400"}]`, `extdataStatus:"unknown"`.
Filtro inclui somente `Nintendo 3DS/<ID0>/<ID1>/title/<high>/<low>/data/**`,
validando ID0/ID1 e o caminho completo. Havendo várias árvores ID0/ID1, o app
deve pedir a árvore usada pelo emulador, não misturá-las. O layout de save vem
do [ArchiveSource_SDSaveData do Azahar](https://github.com/azahar-emu/azahar/blob/master/src/core/file_sys/archive_source_sd_savedata.cpp).

**Extdata é outro identificador** e não pode ser derivado cortando o title ID.
Não entra no filtro por jogo nesta versão: exige metadado verificável ou escolha
explícita da pasta no fluxo de grupo. A sincronização de grupo existente continua
disponível. Updates/DLC, NAND, content e histórico nunca entram nesse filtro.
Testes sintéticos comprovam mapeamento/limites, não homologam saves reais.
