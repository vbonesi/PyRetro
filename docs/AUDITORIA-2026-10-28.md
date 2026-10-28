# Auditoria — 28/10/2026

Base auditada: `721b9be7c3c3c9634acbc20b1adf940b434ea47c`, então igual ao
`main` publicado. O registro é uma linha de base para correção, sem certificar
alterações posteriores. O plano de melhorias e identidade publicado depois,
em `b2e6d5a`, é uma frente distinta.

## Validação

- 356 testes Python, 50 verificações JavaScript em Chromium e 69 testes JVM
  passaram em cópias isoladas, com dados sintéticos.
- Android 0.14.0/code22: `assembleDebug` e `lintDebug` concluídos. Lint com
  zero erros e 93 avisos; assinatura descartável somente no laboratório.
- Serviço ativo/habilitado e recurso estático HTTP 200. `HEAD /` responde 501
  por ausência do método; isso não demonstra indisponibilidade.
- Nenhuma instalação no aparelho, sincronização real ou alteração do acervo.
  Testes sintéticos não substituem homologação física.

## Fila de correção

### AUD28-01 — alta: identificador privado em documentação pública

Um hostname pessoal atual foi identificado em `docs/roadmap.md` e
`docs/changelog.md` na base auditada. O valor fica omitido deste registro.
Não é senha/token, e não foi demonstrado acesso à rede por essa exposição.

- [ ] Trocar os exemplos por valores neutros e verificar recorrência antes de publicar.
- [ ] Avaliar o histórico em etapa separada; esta auditoria não autoriza sua reescrita.

### AUD28-02 — média: save inicial pendente não pode ser aplicado

`core/drive_pending.py:79–85` repassa `None` quando não há versão anterior,
mas `core/mobile_sync.py:118–123` aceita ausência somente como `'-'`.
Fixture: `1700000000000-none.pending`, sem save no destino. A listagem diz
`apply`; aplicar retorna `ValueError: hash de comparação ausente ou inválido`.
A pendência permanece e o destino não é criado. O caminho forçado com destino
ausente também precisa da normalização.

- [ ] Normalizar o sentinela na fronteira e acrescentar regressões de criação
  inicial e aplicação forçada sem destino. A suíte atual começa com save existente.

### AUD28-03 — média: organização de CUE incompleto anuncia sucesso

`core/organize.py:242–254` filtra as referências por existência em vez de
recusar dependências ausentes. Fixture: CUE com `FILE "missing.bin" BINARY`,
sem a faixa. O descritor é movido e a operação retorna sucesso.

- [ ] Validar todas as referências antes da primeira movimentação, inclusive
  dentro de compactados. Preservar e sinalizar descritores incompletos;
  CUE sem BIN continua não sendo lixo.

### AUD28-04 — média: nomes normalizados colidem no mesmo conjunto

`core/organize.py:205–221` publica nomes um a um sem verificar colisões no lote.
Fixture: CUE com `A*B.bin` e `AB.bin`; ambos viram `AB.bin`. O retorno anuncia
três arquivos, mas há dois destinos únicos. A primeira faixa vai para a lixeira
e o CUE referencia a segunda duas vezes. Foi demonstrada substituição indevida,
não perda irrecuperável: a lixeira sintética preserva a primeira faixa.

- [ ] Calcular e validar o mapa completo de destinos antes de escrever;
  recusar colisões, conferir o conjunto e publicar o descritor por último.

### AUD28-07 — documentação e retomada

- [ ] Conciliar a abertura do roadmap com as entregas recentes de Android e
  OAuth, mantendo separados implementação, registro de uso anterior e nova homologação.
- [ ] Depois das regressões acima, seguir a matriz pequena de uso real do
  roadmap: controle físico, retorno de emulador, interrupções, permissões e saves.

As linhas citadas são da revisão auditada. As reproduções usaram apenas diretórios
temporários e fixtures; os logs e o script de reprodução permanecem no relatório
privado da auditoria. Este registro não contém hostname, credenciais ou inventário.

## Correções (28/10/2026)

AUD28-01 a 04 corrigidas com testes de regressão (`tests/test_public_docs.py`,
`test_drive_pending.py`, `test_organize_downloads.py`); 363 testes Python passam. O histórico
do Git ainda contém o hostname antigo (etapa separada, não reescrita). AUD28-07 conciliada no
roadmap; homologação real continua pendente.
