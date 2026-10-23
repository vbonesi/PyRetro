# RomM como referência para o PyRetro

Pesquisa documental em 23/10/2026; nenhum serviço instalado e nenhum acervo importado.
As páginas `latest` são móveis; a página de saves consultada é da **5.3.0-beta**.
Não tratar recursos dessa documentação como homologados em toda versão estável.

## O que aproveitar

| Referência observada | Aplicação proposta ao PyRetro |
|---|---|
| Dispositivo tem identidade e registra a última versão sincronizada | Manter baseline por origem/dispositivo ao acrescentar Drive direto; não usar somente data como árbitro |
| Save e state são conceitos distintos; state depende do emulador/core | Mostrar core e versão conhecidos antes de restaurar; não prometer compatibilidade só pela extensão |
| Escolha de versão antes de abrir o jogo | Oferecer recuperação explícita na ficha, preservando a versão atual |
| Pedido de instalação espera o dispositivo e informa conclusão/falha | Fila persistente deve distinguir recebido, baixando, validado e pronto; término do transporte não prova jogo completo |

Fontes primárias:
[dispositivos](https://docs.romm.app/latest/using/devices/) e
[saves/states na 5.3.0-beta](https://docs.romm.app/5.3.0-beta/using/saves-and-states/).

## Decisão técnica desta rodada

Recomendação: aproveitar os conceitos de identidade de dispositivo, baseline,
compatibilidade e estado explícito da fila na arquitetura atual. PyRetro já possui
sincronização explícita, baseline e histórico; substituir isso por outro servidor
agora ampliaria instalação, migração e superfícies de conflito sem resolver a
homologação pendente. Esta é uma avaliação de arquitetura, não uma medição comparativa.

Não copiar a política de retenção automaticamente: no PyRetro a remoção de versões
deve continuar explícita. Não importar tempo acumulado nem sobrepor states entre
cores. Uma prova futura deve usar fixtures: duas pontas alteradas offline, origem
indisponível, retry sem duplicação, recuperação e identidade após renomear ROM.
