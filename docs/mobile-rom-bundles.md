# Contrato de conjuntos de discos (versão 1)

Implementação do servidor em 23/10/2026. O cliente Android precisa consumir este
contrato antes de liberar CUE/M3U. O download antigo de arquivo único permanece.
Não há rota de exclusão de arquivos nesta entrega.

## Obter e baixar

1. Consultar `/api/mobile/rom/options?code=PS&name=...` como antes.
2. Para a opção escolhida, consultar
   `/api/mobile/rom/bundle?code=PS&entry=...` (todos os valores URL-encoded).
3. A resposta contém `version: 1`, `entry`, `id`, `total_size` e `files`.
   Cada arquivo tem `file`, `size`, `etag`, `source` (`pc`/`drive`), `descriptor`.
   `file` é relativo à raiz do sistema; preservar subpastas e nomes exatos.
4. Baixar cada arquivo, na ordem do manifesto, por
   `/api/mobile/rom/file?code=PS&entry=...&bundle=ID&file=...&etag=...`.
   `Range: bytes=N-` conserva a retomada por membro. A rota revalida o conjunto
   e recusa arquivos externos. HTTP 409 exige uma nova análise, nunca concatenar
   o parcial antigo à versão nova. HTTP 400 indica conjunto inválido/incompleto.
5. Antes de publicar qualquer arquivo, verificar colisões em **todos** os destinos.
   Não substituir faixas existentes sem comprovar identidade e decisão explícita.
   Copiar para staging privado; verificar tamanho e identidade esperados; publicar
   dependências antes dos descritores e o `entry` por último. Em encerramento do
   processo, conservar os checkpoints. Só marcar pronto depois de validar o
   conjunto no destino. Não iniciar emulador automaticamente.

O manifesto percorre M3U, CUE e GDI; deduplica faixas compartilhadas e rejeita ciclos,
ascendência `..`, links para fora do acervo, URL, arquivo ausente/vazio, CCD e extensão
de dependência desconhecida. Limites: 256 arquivos, profundidade 16 e descritores
UTF-8 de até 1 MiB. Nenhuma referência é deduzida por semelhança de nome.

A origem é única: PC quando o descritor existe localmente, senão Drive para um item
do catálogo. Um CUE local incompleto não mistura faixas remotas silenciosamente.
O `id` é SHA-256 dos **metadados** ordenados, não dos bytes das ROMs. ETag usa
tamanho/data; não é prova criptográfica de conteúdo. O cliente deve manter esse
limite explícito. A revalidação no Drive faz consultas por membro e pode ser lenta.

## Remoção

`GET /api/mobile/rom/removal-plan?code=PS&entry=...` retorna uma **prévia do PC**:
`scope: pc`, `id`, `complete`, `remove`, `preserve`, `requires_confirmation: true`.
Descritores externos que usam um membro o protegem; qualquer descritor externo
inválido impede provar exclusividade e bloqueia toda a proposta de remoção.

Essa lista não autoriza exclusão no Android: o cliente deve inventariar os
descritores locais via SAF, proteger aliases/fixados, repetir a análise imediatamente
antes de aplicar e pedir confirmação. Nunca excluir saves, estados, BIOS, texturas
ou cópias remotas. Se outro M3U usa o entry, todo o subgrafo permanece protegido.

## Evidência

`tests/test_rom_bundles.py`: ordem, deduplicação, retomada com identidade,
manifesto obsoleto, travessia, ciclos, faixa ausente, symlink externo, tamanho
excessivo, Drive simulado e prévia de remoção compartilhada. Fixtures somente;
não homologam SAF, provedor Drive real ou emuladores.
