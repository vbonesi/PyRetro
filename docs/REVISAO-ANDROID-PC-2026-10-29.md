# Revisão da interface Android em comparação com o PC — 29/10/2026

## Conclusão da implementação — Android 0.22.0

As sete correções prioritárias desta revisão foram aplicadas. O APK **0.22.0 / code 32** foi
instalado no aparelho com a mesma chave, preservando os dados. A revisão original abaixo é histórica.

| Achado | Entrega atual |
|---|---|
| Sucesso falso em falha de saves | Erro visível, tela preservada e nova tentativa; consulta e envio com falha induzida passaram na Activity real. |
| Filtro de Desejados | Opções da própria coleção, verificadas em retrato e paisagem. |
| Ranking/empates | 1–2–3 em retrato, 2–1–3 em paisagem; desempate por nome normalizado, plataforma e ID. |
| Escopo PSP/3DS | ID verificado/escolhido, região/árvore, alcance apresentado; fallback explícito para todo o emulador. |
| Glifos/foco/espaço | Auto/manual Xbox, PlayStation e genérico; foco branco e seleção verde; aba ativa trazida à vista, busca compacta e ajuda. |
| Remoção | Celular/Drive/ambos, prévia e revalidação; lixo local recuperável, proteção de compartilhados, fixados, iniciados e fila. |
| Acabamento | Marca PR, nota especial 11, sorteio repetido, selos e fila. |
| Dependência do notebook | Biblioteca SQLite/diário, catálogo direto, Desejados/edição/cadastro/estatísticas locais e capas sob demanda. |

Verificação final: **48 telas/estados com fonte 80% + 48 com fonte 130%**, em ambas as orientações.
As asserções passaram e as capturas de Ranking, início e ficha foram inspecionadas. Textos longos
quebram linha ou usam rolagem; com fonte ampliada e paisagem há menos cartões visíveis. Um vídeo
flutuante do usuário encobria parte de algumas capturas; essa região não foi tratada como evidência visual.
Fonte e rotação originais foram restauradas.

Passaram também as suítes no aparelho de SQLite/transações/replay/sessões, saves com falha/retry,
SAF/histórico/checksum/conflitos, fila e remoção/restauração de ROM sintética. Nenhuma dessas suítes
alterou saves/jogos reais: o inventário final manteve **231 arquivos** com nomes, tamanhos e datas iguais.
KOF '97 foi iniciado separadamente com config e saves temporários: FBNeo não encontrou arquivos faltantes
e exibiu o boot Neo Geo. A BIOS instalada tem MD5 igual ao PC; configuração real do RetroArch preservada.

Recursos do ícone instalado e nove máscaras/temas foram renderizados e inspecionados. O tema do
launcher real e Steam Big Picture continuam com conferência física pendente. Atalhos 3DS, uso prolongado,
G8 no notebook e clone Arcade real também não são comprovados por esta revisão. O roteiro não faz
login, compra, edição real de Biblioteca nem sincronização destrutiva.

Validação de código: **103 JVM, 58 JavaScript, build, lint e APK auxiliar aprovados**; Python passou
448 testes antes de integrar mais um teste de criação de diretório do Claude, aprovado na suíte focada.
Evidências privadas em `auditoria/android-final-2026-10-29/`, fora do Git.

## Revisão original — Android 0.19.0

**Na revisão original, a paridade ainda estava incompleta.** As cores de nota, os selos de plataforma e o motor de
saves chegaram ao Android. Outras mudanças do modo TV não chegaram, e há defeitos próprios
do app. Esta entrega registra a revisão e recupera a instrumentação; não instala uma nova
versão do produto nem marca as diferenças abaixo como corrigidas.

Base consultada: `b405e66`, Android instalado **0.19.0 / code 28**. A comparação usa o modo TV
como interface do PC; a web permanece como ferramenta de administração/diagnóstico.

## Matriz de paridade

| Área | Android observado | Resultado em relação ao PC |
|---|---|---|
| Início, catálogo, favoritos, busca | Fileiras e grade; pesquisa local, cache e cartões com disponibilidade | Implementados; catálogo e capas ainda dependem da primeira carga pelo notebook. |
| Nota 0–11 | Cores comuns nos cartões e no editor; editor pula de 10 para 11 | Aplicado. O resumo inicial da ficha ainda escreve `★ 11,0` neutro, embora cartão/editor usem o símbolo especial e dourado. |
| Ranking | Só jogos com nota, Top 3 e restantes sem repetição | Aplicado em parte: retrato continua com três cartões na ordem 2–1–3. |
| Empates | Nome em minúsculas como único desempate | Diverge do PC: faltam normalização do nome, plataforma e ID estável. |
| Filtro recolhido | Diálogo de plataforma/gênero, botão resume a escolha | Aplicado em parte; Desejados usa opções da coleção errada. |
| Sortear | Botão próprio; filtros e ficha do resultado sem lançar jogo | O defeito de herdar estilo de capa não existe no Android. Falta o fluxo explícito de resultado/“Sortear novamente” do PC. |
| Selos de plataforma | Mesmo manifesto, alias e fallback; cartões/fileiras/ficha | Aplicado nessas superfícies. Stream e outras listas não têm o mesmo selo em todas as ocorrências previstas no plano. |
| Marca | Placeholder e ícone adaptativo PR; recurso monocromático presente | Aplicado aos recursos. Cabeçalho ainda usa estrela; máscaras do launcher e ícone temático dependem de conferência visual própria. |
| Cabeçalho e rodapé | Barras horizontais; dica some em paisagem | Parcial: cabeçalho e paginação deixam pouca área para cartões em paisagem; sem ajuda expansível equivalente ao PC. |
| Glifos | Textos fixos `A/B/X/Y`, `LB/RB`, “Galileo G8” | Não aplicado: sem detecção/escolha Xbox/PlayStation/genérico na interface. |
| Foco e aba ativa | Ambos usam `shape(true)` | Não aplicado: foco e seleção recebem o mesmo sinal visual. |
| Ficha | Ação principal, favorito/fixação, Saves, progresso e opções recolhidos | Estrutura aplicada. Conferir divergências de saves e de remoção abaixo. |
| Remover | Apenas ROM deste celular; CUE/M3U com prévia local | Falta a escolha local / Drive à lixeira / ambos de `core/removal.py`, já presente no PC. |
| Downloads e espaço | Fila, estados, pausa/retomada, fixados e espaço | Telas presentes. A revisão não inicia transferências nem remove arquivos. |
| Saves na nuvem | Motor novo nas fichas e em Opções; conflito explícito | Aplicado, mas há confirmação falsa em falhas e PSP/3DS usam o grupo inteiro. |
| Progresso/tempo e Biblioteca | Pendências HTTP; catálogo vem do notebook | Diário local/SQLite e publicação incremental do PC ainda não portados; pendência já registrada. |
| Desejados, edição, capas e estatísticas | Cache de leitura e ações pelo notebook; busca de capa descarta resposta antiga | Presentes. Mutação real e serviços externos não foram homologados nesta revisão. |
| Organizar, playlists, texturas, apps/permissões | Ferramentas presentes; Organizar identifica o notebook no botão | Administração do PC não equivale a importar arquivo local no celular. Não acionar operação real para conferir layout. |

## Correções prioritárias

1. **P1 — saves podem anunciar sucesso após falha.** Em `MainActivity.cloudSaves`, os dois
   botões de resolução descartam o resultado de `runCatching(resolve(...))` e exibem “Mantido”/
   “Usado” mesmo se a resolução falhar. No envio em lote, resultados de grupo com `isFailure`
   desaparecem de `getOrNull().orEmpty()` e não entram na contagem de erros. Uma exceção fora
   desses resultados também não recebe tratamento na ação de aplicar. Preservar a tela,
   exibir o erro e permitir nova tentativa; só confirmar depois do sucesso. Achado de leitura
   de código; não foi provocada falha em save real.
2. **P2 — filtro de Desejados consulta Catálogo.** `render()` usa `wishGames`, mas
   `filterDialog()` sempre usa `games`. Reproduzido com catálogo NES/SNES e desejo Xbox/Corrida:
   o filtro não oferece Xbox nem Corrida, nas duas orientações.
3. **P2 — Ranking em retrato não recebeu a adaptação do PC.** `GridRules.podiumOrder()`
   aplica 2–1–3 sempre, e `render()` sempre monta uma fileira horizontal. No aparelho, os nomes
   e plataformas ficam truncados. Com fonte 130%, até a nota 11 pode sair do trecho visível
   do selo do primeiro colocado. Usar 1–2–3 em retrato e ordenar empates como no PC.
4. **P2 — ficha PSP/3DS tem escopo maior que o nome sugere.** `gameSaves()` filtra o jogo no
   RetroArch, mas todos os arquivos `psp-*`/`3ds-*` nos demais casos. O diálogo recebe o nome do
   jogo sem explicar esse alcance. Expor o escopo e retomar identificação segura por título
   antes de prometer sincronização por jogo.
5. **P2 — glifos, foco e espaço útil.** Portar a escolha automática/manual de glifos, distinguir
   foco da aba ativa e reduzir o cabeçalho/paginação em paisagem. A aba selecionada também
   pode ficar fora do trecho visível da barra horizontal; `render()` não a traz à vista.
   Os recortes pioram com fonte ampliada: o teste de navegação passa, mas isso não aprova a
   legibilidade dos cartões.
6. **P2 — remoção no Drive ainda não existe na ficha Android.** Entrega separada, com prévia,
   proteção, revalidação, escopo por extenso e teste descartável; não ampliar a ação local
   existente silenciosamente.
7. **P3 — acabamento comum.** Marca no cabeçalho, nota especial no resumo da ficha, fluxo de
   repetir sorteio e cobertura restante dos selos. Não trocar identidade de jogos/arquivos.

## Verificação e limites

`InterfaceSmoke` percorre as oito coleções, filtros de Desejados, sorteio, ficha e progresso,
Situação, Opções, pastas/permissões, apps, pendências, downloads/fila, saves, índice do Drive,
playlists, estatísticas e espaço, em retrato e paisagem: **48 telas/estados** por execução.
Jogos e preferências de teste são isolados; as preferências visuais reais são restauradas.
As asserções de navegação são separadas das observações de paridade: navegar sem fechar não
significa que todas as diferenças da matriz passaram a estar corrigidas. Foram executadas
duas rodadas completas (96 verificações): fonte original do aparelho (80%) e ampliada (130%).
O valor original foi restaurado e conferido. Build/lint e **82 testes JVM**, **435 Python** e
**54 JavaScript** passaram; a suíte web usou o acervo sintético dos testes HTTP.

Os nomes, tamanhos e datas dos **272 arquivos** de jogos/saves/playlists inventariados
permaneceram iguais. Nenhum jogo, sincronização, download, remoção ou gravação de progresso
real foi acionado. Uma sonda de conexão de leitura pode ocorrer ao iniciar a Activity;
`automaticUpdates=false` impede as atualizações automáticas durante a instrumentação.

O APK principal instalado permanece 0.19.0. Só o APK auxiliar de testes foi instalado no
usuário 0. Capturas/relatórios completos ficam em `auditoria/android-ui-2026-10-29/`, ignorado
pelo Git. Não publicar dados do aparelho, contas, preferências ou inventários.

Foi encontrado e retirado de `StatusSmoke` o teste de `FileSync.observation`, API do protocolo
HTTP/Insync removido na 0.19.0: ele impedia compilar **qualquer** APK de instrumentação.
O build normal/JVM/lint não detectava esse erro de compilação dos testes de aparelho.

Não se repetiram homologação física do G8, atalhos 3DS em jogo, uso prolongado, operações
destrutivas, login, busca/aplicação real de capa ou edições na Biblioteca. Esses resultados
não podem ser inferidos da navegação sintética. Máscaras do launcher, ícone temático e
Steam Big Picture continuam com conferência visual própria pendente.

Para repetir, compile `:app:assembleDebugAndroidTest` com a chave local preservada, instale
o APK auxiliar com `adb install --user 0 -r` e execute:

```bash
adb shell am instrument -w -e suite interface com.pyretro.app.test/com.pyretro.app.StorageSmoke
```

Execute sem download ativo: a instrumentação reinicia o processo do app. A suíte também
recusa começar se a fila persistida registrar um download em execução. O relatório informa a pasta privada
das evidências; retire as evidências antes de remover apenas a pasta de teste e o APK auxiliar.
