# ADR 0003: Transporte de Tempo Real via SSE com Fallback por Reconciliação (UC016)

## Status
Proposta (ainda não implementada — depende da Fase 6 do planejamento, que por sua vez depende da
Fase 5/UC014-015-017 estarem gerando os eventos que serão transmitidos)

## Contexto

O [UC016 - Visualizar Partida em Tempo Real](../spec/UC016_InterfaceUsuário_VisualizarPartida.md)
define que alunos devem receber, ao vivo, atualizações de placar, timeline de eventos e cronômetro
de partidas `IN_PROGRESS`, através de uma conexão que o próprio documento descreve como
"WebSocket" (RN1-7, Bloco de Dados 4). O documento também define, na RN17-20 e no Fluxo Alternativo
5, um comportamento de reconexão: ao perder conexão, o sistema deve tentar reconectar
automaticamente e, ao reconectar, **sincronizar o estado atual do servidor** (não assumir que os
eventos perdidos durante a queda serão retransmitidos pelo canal em tempo real).

Como registrado no [planejamento](../ai/planejamento.md) (Fase 6), hoje não existe nenhuma
infraestrutura de tempo real no projeto. Este ADR decide **como** implementar esse transporte,
antes da Fase 6 começar — no mesmo espírito do [ADR 0001](ADR001_Cronometro.md) (que decidiu como
calcular o cronômetro antes do UC014) e do [ADR 0002](ADR002_NormalizacaoModalidade.md) (que
decidiu como persistir dados do vôlei antes do UC014/017).

O ponto central deste ADR: a espec de negócio usa a palavra "WebSocket" mas **não exige**
bidirecionalidade. Todo o fluxo de escrita (marcar gol, cartão, pausar cronômetro, etc.) já
acontece por endpoints REST comuns do UC014/015/017, chamados pelo monitor. O aluno, consumidor do
UC016, **nunca envia dados pelo canal de tempo real** — ele só recebe. Isso muda a decisão de
transporte: WebSocket resolveria o problema, mas é uma ferramenta bidirecional para um problema
unidirecional.

## Decisão

O canal de tempo real do UC016 será implementado com **SSE (Server-Sent Events)**, não WebSocket,
com uma estratégia de reconciliação por `GET` de estado completo em toda reconexão — que é
justamente o comportamento que a RN17-20 do UC016 já pede independentemente do transporte
escolhido.

### 1. Por que SSE em vez de WebSocket

SSE é um protocolo unidirecional (servidor → cliente) construído sobre HTTP puro: o cliente abre
uma requisição `GET` comum, o servidor responde com `Content-Type: text/event-stream` e mantém a
conexão aberta, enviando linhas no formato `data: <payload>\n\n` conforme eventos ocorrem. O
navegador consome isso via `EventSource`, uma API nativa que **já reconecta automaticamente** em
caso de queda, sem código extra no cliente.

Isso é suficiente para o UC016 porque:
- Todos os eventos que o aluno recebe (`score_update`, `goal_scored`, `card_issued`,
  `clock_update`, `match_finished`, `event_deleted`, etc. — Bloco de Dados 4 do UC016) são
  gerados por ações do monitor via endpoints REST já existentes (UC014/UC015/UC017); o aluno nunca
  precisa escrever nesse canal.
- FastAPI suporta SSE nativamente via `StreamingResponse`/`EventSourceResponse` (biblioteca
  `sse-starlette`), sem exigir uma stack de protocolo adicional como o `websockets` exige.
- Reconexão automática do `EventSource` já cobre metade da RN17 ("sistema tenta reconectar
  automaticamente") de graça, sem lógica de reconexão manual no front.
- Infraestrutura de rede (proxies, load balancers, CDNs) tende a lidar melhor com SSE do que com
  WebSocket, por ser HTTP comum — relevante para deploy em ambientes que talvez não tenham upgrade
  de protocolo configurado.

A escolha não é "SSE é tecnicamente superior a WebSocket" de forma absoluta — é que WebSocket
resolveria um problema que o UC016 não tem (o aluno não precisa mandar nada de volta pelo canal
ao vivo), então adotar SSE remove a complexidade de um protocolo bidirecional sem perder nenhuma
regra de negócio do documento.

### 2. Dois canais, como a espec já define

Mantém-se exatamente a topologia de canais da RN2-3 do UC016, só troca-se o protocolo de
transporte:
- **Feed de jogos:** `GET /api/seasons/{season_id}/live` (SSE) — substitui
  `/seasons/{season_id}/live` (WebSocket) da espec.
- **Detalhes de partida:** `GET /api/matches/{match_id}/live` (SSE) — substitui
  `/matches/{match_id}/live` (WebSocket) da espec.

Cada endpoint mantém uma lista de conexões (`asyncio.Queue` por conexão) associadas ao
`season_id`/`match_id`; quando um adapter do UC014/015/017 persiste um evento, ele publica a
mensagem correspondente nas queues do canal relevante (broadcaster leve em memória, sem
dependência de infraestrutura externa como Redis Pub/Sub nesta primeira versão — ver seção de
trade-offs).

### 3. Reconexão: por que reconciliar por GET, não "reenviar o que perdeu"

A RN17-20 do UC016 já deixa isso explícito ("sistema sincroniza estado atual do servidor" ao
reconectar) — este ADR só formaliza a implementação. A decisão é: **o servidor não tenta guardar
um buffer de eventos perdidos para retransmitir na reconexão.** Em vez disso:

1. Ao detectar queda (evento `onerror` do `EventSource` no front, ou timeout no backend), o
   cliente entra em estado "Reconectando..." (RN17-18 já preveem isso na UI).
2. O `EventSource` do navegador já tenta reabrir a conexão SSE sozinho (comportamento nativo).
3. **Em paralelo**, e não apenas na abertura da tela: toda vez que o front detecta que a conexão
   SSE caiu e voltou, ele dispara um `GET /api/matches/{match_id}` (estado completo: placar,
   cronômetro calculado — via ADR 0001 —, timeline completa de eventos não deletados) para
   reconciliar o estado local, substituindo qualquer estado antigo que possa ter ficado
   inconsistente durante a queda.
4. Esse mesmo endpoint de leitura completa (`GET /api/matches/{match_id}`) é o mesmo que resolve o
   débito técnico já registrado na Fase 4/5 do planejamento (endpoints `GET` de consulta que
   ficaram pendentes) — este ADR não cria um endpoint novo só para reconciliação, reaproveita o
   que já está planejado como pendência.

Essa decisão evita um problema real de buffer de eventos perdidos: quanto tempo guardar, quantos
eventos guardar por partida, o que fazer se o cliente ficou offline por muito tempo. Reconciliar
por `GET` de estado completo é mais simples e sempre correto, porque o estado completo (placar,
timeline, cronômetro) já é a fonte da verdade persistida — não há necessidade de reconstruir um
histórico de mensagens de transporte.

### 4. Formato das mensagens SSE

Cada mensagem publicada usa o campo `event:` do protocolo SSE para o tipo (mapeando diretamente os
tipos já definidos no Bloco de Dados 4 do UC016 — `score_update`, `goal_scored`, `clock_update`,
etc.) e `data:` com o payload em JSON:

```
event: goal_scored
data: {"match_id": 42, "team_id": 7, "player_id": 15, "clock_seconds": 932, "new_score": {"team1": 2, "team2": 1}}

```

Isso permite que o `EventSource` no front use `addEventListener("goal_scored", handler)` por tipo,
em vez de um único `onmessage` que precisa inspecionar o payload para descobrir o tipo.

### 5. Push Notifications (RN13-16 do UC016) ficam fora deste ADR

Push Notification é um mecanismo independente (entrega mesmo com app fechado, via FCM/APNs) e não
compete com SSE/WebSocket como "transporte de tempo real com app aberto". Este ADR resolve apenas
o canal ao vivo com app aberto; a integração com provedor de push é uma decisão separada, já
registrada como pendência na Fase 6 do planejamento.

## Consequências

**Positivas**
- Reaproveita HTTP comum: sem biblioteca de protocolo adicional além de `sse-starlette` (ou
  implementação manual com `StreamingResponse`, que também é viável em poucas linhas).
- Reconexão automática de graça via `EventSource` nativo do navegador.
- Reconciliação por `GET` de estado completo é simples de raciocinar e testar: não existe conceito
  de "mensagem perdida" para gerenciar, porque a reconciliação sempre parte do estado persistido
  completo.
- Fluxo unidirecional do SSE casa exatamente com o padrão real de uso do UC016 (aluno só
  observa) — não há complexidade de protocolo não utilizada.

**Negativas / trade-offs**
- **Broadcaster em memória, por processo.** Se a aplicação subir em mais de um processo/instância
  (múltiplos workers Uvicorn, ou múltiplas réplicas em produção), um evento publicado no processo
  A não chega a um cliente SSE conectado ao processo B. Nesta primeira versão isso é aceito como
  limitação conhecida — é o análogo do que WebSocket também teria sem uma camada de Pub/Sub
  compartilhada (ex.: Redis). Se o projeto crescer para múltiplas instâncias, será necessário
  introduzir um broker compartilhado (Redis Pub/Sub é a opção mais direta) antes deste ADR ser
  considerado suficiente — fica registrado como extensão futura, não como decisão tomada agora.
- SSE tem limite de conexões simultâneas por domínio em HTTP/1.1 no navegador (6 por domínio,
  tipicamente); em HTTP/2 esse limite não existe (multiplexação). Como o feed de jogos já é um
  único canal por temporada compartilhado entre todas as partidas (RN2), o número de conexões SSE
  simultâneas por aluno tende a ser pequeno (1 no feed + no máximo 1 na tela de detalhes, nunca
  os dois função simultaneamente segundo RN4-5), então esse limite não deve ser um problema
  prático — mas fica registrado caso o front venha a abrir conexões SSE de forma diferente do
  previsto pela espec.
- SSE só transporta texto (UTF-8); não há problema aqui porque todo payload já é JSON, mas
  descarta de saída a possibilidade de mandar binário pelo mesmo canal (não é uma necessidade do
  UC016).

## Alternativas consideradas

1. **WebSocket, como o texto do UC016 sugere literalmente.** Rejeitada como implementação
   (não como conceito — WebSocket resolveria o problema): exige protocolo bidirecional para um
   caso de uso unidirecional, exige biblioteca adicional (`websockets`) e lógica própria de
   reconexão no cliente (o `EventSource` já resolve isso de graça para SSE). Ficaria correto
   funcionalmente, mas mais complexo do que o problema exige.
2. **Polling simples (cliente faz `GET` a cada N segundos, sem canal de push nenhum).** Rejeitada:
   atenderia a RN17-20 (reconciliação) mas desconsidera as limitações da aplicação.
3. **Buffer de eventos perdidos no servidor, retransmitido na reconexão (em vez de reconciliação
   por GET).** Rejeitada: exige decidir tamanho do buffer, tempo de retenção, e o que fazer se o
   cliente ficou offline além da janela do buffer — complexidade que a reconciliação por GET de
   estado completo evita inteiramente, sem perda de corretude (o estado completo já é sempre
   correto, por definição).

## Referências
- [UC016 - Visualizar Partida em Tempo Real](../spec/UC016_InterfaceUsuário_VisualizarPartida.md)
- [UC014 - Registrar Evento Durante Partida](../spec/UC014_GestãoDePartidas_RegistrarEvento.md)
- [UC015 - Finalizar Partida](../spec/UC015_GestãoDePartidas_FinalizarPartida.md)
- [UC017 - Corrigir Eventos da Partida](../spec/UC017_GestãoDePartidas_CorrigirEvento.md)
- [ADR 0001 - Estratégia do Cronômetro da Partida](ADR001_Cronometro.md) — fonte do cálculo de
  `clock_seconds` usado tanto nos eventos SSE (`clock_update`) quanto no `GET` de reconciliação.
- [ADR 0002 - Normalização de Configuração por Modalidade e Histórico de Sets](ADR002_NormalizacaoModalidade.md)
- `docs/ai/planejamento.md` (Fase 6 — Tempo Real, e débito técnico de endpoints `GET` de consulta
  registrado nas Fases 4/5, reaproveitado aqui como endpoint de reconciliação)
