# Camada de nuvem independente (plano de 28/10/2026)

Objetivo: o PyRetro funciona sozinho no PC e no celular (local-first) e, se o usuário quiser,
conecta uma nuvem para guardar ROMs sob demanda, saves e backups. Hoje o Drive é usado pelo Insync;
o alvo é o PyRetro falar com a nuvem direto, qualquer que seja ela.

## Peças

| Peça | Estado |
|---|---|
| `core/cloud.py`: interface `Storage` (list, exists, get, put sem sobrescrever, trash) com `RcloneStorage` (qualquer remoto do rclone ou pasta local) e `MemoryStorage` | **pronta e testada** |
| `core/cloud_saves.py`: motor de saves por manifestos por dispositivo (push, pull, conflito, resolver, histórico) | **pronto e testado** (memória e rclone local) |
| Ligar o motor ao lançador (baixar antes de abrir, enviar ao fechar) e à tela de conflito | falta |
| Android 0.18.0: `CloudStorage`, `DriveCloudStorage` (Drive), `CloudSavesEngine` (mesmo protocolo e prefixos por grupo), `CloudPhone` (pastas SAF) e botão "☁ Saves na nuvem (novo)" em Situação | **compila e tem 9 testes JVM de paridade; não testado no aparelho** |
| Biblioteca e Backups sem Insync: `core/cloud_snapshots.py` (versões imutáveis, retenção, restauração, backups novos) com gancho no `save_library` | **pronto** (SQLite + diário fica para depois) |

## Protocolo de saves (sem escrita condicional)

```
<grupo>/blobs/<sha256>              conteúdo imutável
<grupo>/devices/<dispositivo>.json  manifesto que só aquele dispositivo escreve
```

- Cada dispositivo escreve só o próprio manifesto: não há disputa pelo mesmo arquivo.
- A versão atual de um save é o conjunto de **cabeças** (entradas que nenhuma outra declara como
  `base`). Uma cabeça = em dia; várias = conflito, e nada é sobrescrito até o usuário escolher.
- Antes de substituir um arquivo local, a versão antiga vai para `.pyretro-history/`. Na nuvem,
  todo blob fica (histórico); `trash` do provedor cobre a limpeza futura.
- O que vem da nuvem é desconfiado: caminhos hostis ignorados, hash conferido antes de gravar.
- Exclusão local nunca se propaga: arquivo que falta é restaurado (modo "só na nuvem": o cache local
  pode ser apagado e o próximo jogo baixa o save mais recente).

## Modo "saves só na nuvem"

O lançador do PyRetro baixa o save mais recente antes de abrir o jogo e envia ao fechar; offline,
joga com o cache e envia depois. Conflito pergunta (manter este, usar o da nuvem; o outro fica no
histórico).

## Para outras pessoas

- Escopos: o acesso total ao Drive (`drive`) é restrito pelo Google e pede verificação de segurança
  paga; para terceiros o caminho é `drive.file` (o app vê só o que criou) com a pasta escolhida pelo
  usuário. Outros provedores via rclone (OneDrive, Dropbox, S3, WebDAV, SFTP).
- Credenciais no chaveiro do sistema, nunca em arquivo de projeto.
- Modelo "traga a sua nuvem": o app não hospeda nem indexa conteúdo de terceiros (reduz o risco
  jurídico; não é parecer). Capas e metadados dependem dos termos de cada fonte.
- Empacotamento (Flatpak/AppImage), onboarding que detecta emuladores, atualizador e testes de
  instalação limpa ficam para depois da camada estar estável.

## Ordem sugerida

1. Ligar o motor de saves ao lançador do PC com um grupo de teste (pasta descartável no Drive).
2. Implementação Android de `Storage` (Drive) e do motor, com o mesmo protocolo.
3. Migrar os saves reais (etapa G) com backup, emuladores fechados e conferência por hash.
4. Biblioteca em SQLite + diário; backups remotos.

## Como testar no celular (Android 0.18.0)

1. Conferir no notebook que o envio terminou: `python3 -m core.cloud_sync status` deve mostrar `{}`.
2. Instalar: `adb install --user 0 -r cache/artifacts/PyRetro-0.18.0-debug.apk`.
3. Em Situação, escolher as pastas de saves (RetroArch, PPSSPP, 3DS) se ainda não estiverem, e abrir
   "☁ Saves na nuvem (novo)" → "Comparar e sincronizar". Esperado: baixar os saves do notebook e enviar os do celular.
4. Jogar algo, voltar ao notebook e rodar `python3 -m core.cloud_sync status`/`sync`.
5. Conflito (mudar o mesmo save nos dois lados): o app e o notebook mostram o conflito; nada é sobrescrito.
O protocolo antigo (pendências pelo Insync) continua no app até este teste passar.
