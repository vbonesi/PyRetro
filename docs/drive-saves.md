# Saves diretamente no Google Drive — contrato v1

O Android usa a conta Google e Drive v3, sem notebook ligado. Este documento e
`core/drive_saves.py` definem a política para espelhar no Kotlin. O Python é puro:
não autentica, consulta Drive ou transfere arquivos. Integração e homologação
com o provedor real continuam com o Android.

## Layout

Partindo da pasta escolhida `Jogos/Saves`, os grupos são os de `mobile_sync`:

| Grupo | Caminho relativo | Conteúdo |
| --- | --- | --- |
| `retro-saves` | `saves` | `.srm .sav .rtc .sra .eep .fla .mcr .mcd .dat .dsv .nv .nvm .mem .fs` |
| `retro-states` | `states` | `.state`, `.stateN`, `.state.auto` e respectivos `.png` |
| `retro-runtime` | `runtime-logs` | `.lrtl`; só transferência, sem somar/importar tempo |
| `psp-saves` | `PPSSPP/SAVEDATA` | `ULUS12345DATA00/DATA.BIN`, por exemplo |
| `psp-states` | `PPSSPP/PPSSPP_STATE` | arquivos por serial `.ppst .jpg .png` |
| `3ds-saves` | `Lime3DS/sdmc` | `Nintendo 3DS/<ID0>/<ID1>/title/<high>/<low>/data/**` e `extdata/<high>/<low>/**` |

`mobile_sync.accepted` é a lista permitida normativa, incluindo capitalização e
IDs. Nunca copiar NAND, BIOS, configurações, conteúdo instalado ou `.pyretro-*`.
Caminhos relativos usam `/`, sem segmentos vazios, `.`/`..`, barra invertida,
`:` ou NUL. Limites: 20 mil arquivos por análise, 512 MiB por arquivo. `.fs` foi
alinhado no servidor com a regra FBNeo já existente no Android.

Pastas personalizadas do PC exigem associação explícita, sem adivinhar caminhos.
Analisar não cria pastas. Persistir IDs da conta/pasta, paginar todas as listagens,
ignorar lixeira, recusar atalhos e nomes duplicados em qualquer nível até escolha
explícita da origem. Nome no Drive não é chave única; nunca escolher o primeiro.

## Conflitos e histórico

Fechar emuladores antes de aplicar. Calcular SHA-256 e tamanho dos bytes estáveis
nas duas pontas. Data, MD5 ou `appProperties` isolados não substituem esse cálculo.
Baseline é o hash da última transferência confirmada por arquivo; ausência é null.

| Situação | Resultado |
| --- | --- |
| hashes iguais, inclusive ambos ausentes | `same` |
| só celular, sem baseline | `upload` |
| só Drive, sem baseline | `download` |
| uma ponta ausente com baseline anterior | `conflict`, sem propagar exclusão |
| duas versões diferentes sem baseline | `conflict` |
| celular igual à baseline | `download` |
| Drive igual à baseline | `upload` |
| ambas mudaram | `conflict` |

Conflito pergunta **Usar celular**, **Usar Drive** ou **Não sincronizar agora**.
Data/tamanho são informativos, nunca critério automático. Antes de substituir,
copiar e conferir a versão anterior em
`.pyretro-history/<caminho>/<timestamp>-<uuid>.previous` na raiz do grupo no
destino. Sem limpeza automática; histórico não entra no manifesto. Revisões
automáticas do Drive não substituem esse histórico explícito.

## Funções e formato

`identity(account_id, saves_folder_id, group, local_tree)` calcula SHA-256 do
UTF-8 do array JSON `[1,account_id,saves_folder_id,group,local_tree]`, compacto,
com escapes ASCII (`ensure_ascii=True`). Kotlin deve reproduzir essa serialização
exata, inclusive caracteres não ASCII. Conta usa identificador estável, não token
OAuth/nome exibido. Mudança de qualquer componente invalida análise e baseline.

`analyze(group, local_rows, remote_rows, baseline, identity)` recebe listas assim:

```json
{
  "local_rows": [{"path":"SFC/Game.srm","sha256":"<64 hex minúsculos>","size":8192}],
  "remote_rows": [{"path":"SFC/Game.srm","sha256":"<64 hex minúsculos>","size":8192,"id":"fileId","version":"42"}],
  "baseline": {"SFC/Game.srm":"<64 hex minúsculos>"}
}
```

Retorna `{schema:1,identity,group,rows:[{path,local,remote,baseline,direction}]}`.
Ponta ausente é null. Ponta existente tem `sha256,size` e, no Drive, `id,version`
(strings). `prepare(row, choice, local_now, remote_now)` revalida e retorna
`{action,path,source,expected,preserve}`; escolha `skip` retorna `{action:"skip"}`.
Mudança de hash/tamanho ou ID/version remoto levanta `mobile_sync.Conflict`;
entrada inválida levanta `ValueError`.

Após aplicar, `confirm(transfer, local_after, remote_after, preserved_hash,
published=True)` confere os dois conteúdos e a cópia anterior, retornando o hash
para baseline. `published` é recibo do adaptador transacional, **não** consequência
de HTTP 200. Skip, erro, cancelamento, parcial e conflito não avançam baseline.
Persistir recibo/baseline de modo recuperável; falha exige reanálise.

## Concorrência e recuperação

1. Revalidar identidade, permissões e inventário completo antes de aplicar.
2. Transferir para staging privado/objeto temporário com ID conhecido, conferir
   bytes/tamanho e preservar versão anterior antes de publicar.
3. Revalidar origem e destino contra a análise imediatamente antes de publicar.
4. Garantir publicação condicional contra alteração do destino e criação
   concorrente de nomes. `files.version` é metadado de saída, não parâmetro CAS.
   Uma sequência GET + PATCH não é atômica.
5. Se o adaptador não garantir essa condição com Insync/outros dispositivos,
   guardar versão imutável pendente com ID próprio, sem substituir o ativo nem
   avançar baseline. Exibir pendência/conflito. Esse comportamento conservador
   é obrigatório até validar um protocolo de publicação concorrente.
6. Após publicação comprovada, reler ambas as pontas, confirmar bytes, histórico
   e ausência de duplicatas. Só então `confirm`. Após queda, localizar staging
   pelo ID e validar tudo novamente; mudança exige nova escolha.

As funções puras não implementam atomicidade Drive/SAF. Homologar rede perdida,
token expirado, processo encerrado, duas contas, duplicatas, gravação simultânea,
emulador ativo e recuperação antes de liberar substituições reais. Diagnóstico
público não deve incluir tokens, contas, IDs ou nomes privados.

Fontes oficiais: [recurso Files (nomes, IDs e version)](https://developers.google.com/workspace/drive/api/reference/rest/v3/files)
e [atualizações parciais](https://developers.google.com/workspace/drive/api/guides/performance).

## Implementação 23/10 (Claude): envio do celular como pendência aplicada pelo PC

Seguindo o item 5 acima, o app (0.12.0, `DriveSaves.kt`) **nunca sobrescreve** um arquivo
ativo no Drive:

- **Drive → celular:** confere o `sha256Checksum` do Drive logo antes, baixa, confere bytes e
  hash e grava pelo `FileSync.install` (versão anterior preservada no celular). Avança a base.
- **Celular → Drive, arquivo novo** (sem versão no Drive e sem base): cria o arquivo e relista a
  pasta; se surgiu um homônimo (criação concorrente), move o próprio envio para pendência.
- **Celular → Drive, arquivo existente** (ou conflito resolvido como "usar o do celular"): cria
  `<grupo>/.pyretro-pending/<caminho>/<ms>-<base>.pending`, onde base é o SHA-256 da versão do
  Drive que o celular viu (`none` se não havia). Não avança a base. A análise seguinte mostra a
  linha como "Enviado, aguardando o notebook aplicar" enquanto a pendência existir.
- **No PC** (`core/drive_pending.py`, Ferramentas → ☁ Saves enviados pelo celular; rotas
  `GET /api/drive_pending`, `POST /api/drive_pending/apply|reject`): o Insync traz a pendência
  para a pasta local; aplicar usa `mobile_sync.receive` com `expected=base` (gravação
  condicional, versão anterior em `.pyretro-history`). PC mudou depois → conflito, nada é
  substituído; o usuário escolhe "Usar o do celular" (força, PC vai para o histórico) ou
  "Manter o do PC" (a pendência vai para o histórico como `.rejected`). Aplicada vira `.applied`.
- Identidade da análise: `DriveSaveRules.identity` reproduz `identity()` (teste com os mesmos
  valores de referência), com o `permissionId` da conta como identificador estável.

A homologar com Drive/Insync reais: se o Insync sincroniza pastas `.pyretro-*` (ocultas) nos dois
sentidos, latência até a pendência chegar ao PC e o fluxo com o emulador fechado nas duas pontas.
