# Nuvem independente — estado em 29/10/2026

PC e Android 0.22.0 mantêm dados locais e acessam a nuvem diretamente. O notebook não é necessário
para consultar a Biblioteca, alterar progresso/favoritos, registrar sessões ou usar o catálogo do Drive
no celular após conectar a conta. Jogos locais e alterações funcionam offline; envio ocorre quando há rede.
O Insync deixa de transportar esses dados; a desmarcação seletiva continua sendo feita só pelo Victor.

## Componentes em uso

| Área | PC | Android |
|---|---|---|
| Transporte | `core/cloud.py`, rclone | `DriveCloudStorage`, Google Drive |
| Biblioteca | SQLite/`library_journal.py`, snapshots versionados | SQLite transacional/`LibraryJournal`, bootstrap pelo snapshot |
| Atualizações | início, pós-jogo, cinco minutos | WorkManager, rede/bateria, mínimo 15 minutos |
| Catálogo | resolvedor local/Drive | Biblioteca local + índice direto das pastas do Drive |
| Capas | `cloud_covers.py`, publicação quando exibidas | cache offline, blobs por hash e origem direta no Drive |
| Saves e estados | motor antes/depois do jogo e modo TV | SAF, ficha por título e central de saves |
| Backups | publicação verificável em `backups/` | cópia remota disponível; não exige Insync |

Cada campo da Biblioteca resolve concorrência pelo relógio persistente, dispositivo e sequência.
Sessões novas possuem identidade imutável e não são somadas duas vezes. Segmentos do diário são
imutáveis e conferidos; recibos só avançam após salvar. Ambiguidades e alterações antigas sem cadastro
não são descartadas. Desejados, edição, cadastro e estatísticas também usam a Biblioteca local.

Capas são enviadas sob demanda para os jogos exibidos, conforme decisão do Victor. Pré-busca não
envia toda a coleção. `catalog/arcade.json` contém nomes e pais do DAT já existente no PC;
não inclui ROM/BIOS e permite reconhecer nomes curtos e proteger a remoção de pais no Android.

## Protocolo de saves v2

```
saves/blobs/<sha256>                         conteúdo imutável compartilhado
saves/devices/<dispositivo>.json             manifesto de um dispositivo
states/<dispositivo>/blobs/<sha256>          estados exclusivos daquele aparelho
states/<dispositivo>/devices/<dispositivo>.json
```

Uma versão aponta suas bases. As cabeças não superadas por outra versão representam o estado atual:
uma cabeça pode ser aplicada; várias exigem escolha explícita. Hash e caminho são validados antes de
gravar. A versão local substituída vai para o histórico, e os blobs remotos antigos permanecem.
O Android usa `android-<UUID>` persistente; saves continuam compartilhados, estados são separados.
Dados antigos não são apagados ou restaurados em decorrência dessa separação.

Ausência local normalmente não é exclusão: um save ausente pode voltar da nuvem. **Esquecer** é uma
operação explícita por arquivo, com confirmação e prévia revalidada; publica marcador `deleted: true`,
sem apagar blobs. Outro aparelho com a mesma cópia arquiva a versão local; se ela mudou offline,
o motor apresenta conflito. Restaurar uma versão histórica cria uma cabeça de conteúdo normal.
Saves de jogos finalizados permanecem, mesmo sem ROM. Nenhuma rotina de limpeza em lote os esquece.

PSP/3DS exigem ID de título verificado/escolhido, com região/árvore quando necessário. Extdata não
é inferida automaticamente. A opção de sincronizar todos os jogos do emulador é apresentada por extenso.
Saves/extdata 3DS continuam compartilhados por escolha do Victor; os dados removidos por pedido dele
não devem ser recriados. O protocolo HTTP/Insync de saves foi removido; suas rotas respondem 410.

## Escritas e integridade no Drive

O Drive admite nomes duplicados. No PC, trava por destino protege escritas concorrentes e a criação
de diretórios é serializada antes do envio paralelo de arquivos. Android serializa escritas entre instâncias;
cópias de arquivo com mesmo tamanho/checksum podem ser tratadas juntas, mas divergências bloqueiam a operação.

A auditoria final encontrou diretórios duplicados nos Backups e estados, apesar da contagem lógica correta.
Foi criada uma árvore nova, conferida e promovida: **505 arquivos de Backups por hash e nove objetos de estados**.
As árvores anteriores permanecem em `backups-preservado-20261029-*` e `states-preservado-20261029-*`.
Não houve deduplicação destrutiva dos arquivos reais. Recibos privados ficaram fora do Git.

## Verificar antes de desmarcar o Insync

Com emuladores fechados, executar `python3 -m core.cloud_sync status` (sem ações pendentes = `{}`)
e conferir o snapshot mais recente da Biblioteca. Backups exigem conferência por hash, não só contagem.
Só o Victor desmarca Saves, Capas, Biblioteca e Backups na sincronização seletiva; não usar remoção local
em `~/Drive` para simular essa ação.

## Futuro, sem decisão

Produto para terceiros, revisão de escopos OAuth (`drive.file`), chaveiro, outros provedores,
empacotamento e onboarding continuam ideias. Não houve alteração de credenciais/escopos nesta entrega.
Também não foi implementada distribuição automática de BIOS.
