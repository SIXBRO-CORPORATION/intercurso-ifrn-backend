# ADR 0001: Estratégia do Cronômetro da Partida (UC014)

## Status
Aceito

## Contexto

O [UC014 - Registrar Evento](../UC014_GestãoDePartidas_RegistrarEvento.md) define o controle de
cronômetro (pausar, retomar, `clock_seconds`, `clock_running`) durante uma partida `IN_PROGRESS`.
O domínio `Match` já persiste `clock_seconds`, `clock_running` e `current_period`
(ver `domain/match.py`), inicializados pelo UC013 (`start_match_adapter.py`).

A espec de negócio estabelece, entre outras, as seguintes regras:

- **RN3**: "Todos os eventos registram `clock_seconds` atual **automaticamente**."
- **RN24**: "Cronômetro atualiza automaticamente **no backend** a cada segundo."
- **RN25**: "Cronômetro não para automaticamente ao atingir tempo configurado (permite
  acréscimos)."
- **RN28**: "Sistema envia WebSocket: `clock_update` periodicamente."
- Bloco de Dados 1 (Gol/Ponto): "Tempo do Cronômetro" é campo de **Saída (S)**, nunca de Entrada.

Essas regras deixam claro *quem é a fonte da verdade* do tempo (o backend), mas não deixam
explícito *como* isso deve ser implementado. Existe um risco concreto de uma leitura literal da
RN24 levar a uma implementação ingênua: um job (`APScheduler`, já usado no projeto em
`scheduling/`) que roda a cada 1 segundo, itera todas as partidas `IN_PROGRESS` e faz um
`UPDATE` incrementando `clock_seconds` no banco. Essa abordagem atende ao texto da regra, mas não
escala: escreve no banco constantemente por partida simultânea, mesmo quando ninguém está olhando
o cronômetro naquele instante.

Este ADR registra a decisão de design para evitar essa armadilha antes da implementação do UC014.

## Decisão

O cronômetro será implementado como um **snapshot calculado sob demanda**, não como um contador
persistido tick a tick.

1. **Estado persistido** (em `Match`, já existente): `clock_seconds` guarda o tempo acumulado
   *até o último snapshot* (ou seja, até a última pausa/retomada/transição de período), e
   `clock_running` indica se o relógio está correndo a partir daquele snapshot. Não é necessário
   um novo campo de timestamp de referência: `updated_at` (ou campo equivalente de auditoria já
   existente em `AbstractDomain`) pode ser reaproveitado como o "instante do snapshot"; caso não
   sirva por já ser usado para outra finalidade, adicionar `clock_updated_at: datetime` a
   `Match`.
2. **Cálculo do tempo atual** é feito em memória, sempre que necessário (ao registrar um evento,
   ao responder uma consulta de estado, ao fazer broadcast via WebSocket):
   - Se `clock_running = False`: tempo atual = `clock_seconds` (snapshot puro).
   - Se `clock_running = True`: tempo atual = `clock_seconds + (agora - clock_updated_at)`.
3. **Persistência ocorre apenas em mudanças de estado**, não a cada segundo:
   - Pausar: grava o tempo calculado no momento como novo `clock_seconds`, `clock_running = False`.
   - Retomar: grava `clock_running = True`, `clock_updated_at = agora`.
   - Fim de período: mesma lógica de pausa, mais o avanço de `current_period`.
   - Qualquer `MatchEvent` (gol, cartão, etc.): usa o tempo **calculado** no momento da chamada
     para preencher `clock_seconds` do evento; não grava esse valor de volta em `Match`.
4. **O cliente nunca envia `clock_seconds`.** Os endpoints de ação (pausar, retomar, marcar
   gol/cartão, fim de período) recebem apenas a intenção (ex.: `match_id`, `player_id`,
   `event_type`); o tempo é sempre determinado pelo servidor a partir do snapshot acima —
   coerente com o campo ser de Saída (S) no Bloco de Dados 1.
5. **`clock_update` via WebSocket (RN28)** é emitido por um broadcaster leve e periódico
   (ex.: a cada 2–5s, não necessariamente 1s) que **lê e calcula** o tempo atual de cada partida
   `IN_PROGRESS` com clientes conectados e publica o valor — sem gravar nada no banco nesse ciclo.
   Esse mesmo broadcast também deve ser disparado de forma síncrona nas transições de estado
   (pausar/retomar/fim de período), para não depender só do intervalo periódico.
6. O front-end é responsável apenas por **interpolar visualmente** o cronômetro entre um
   `clock_update` e outro (ex.: `setInterval` local de 1s somando ao último valor recebido), e por
   ressincronizar sempre que receber um novo `clock_update`. O front nunca é a fonte da verdade;
   ele apenas reflete o estado do servidor.

## Consequências

**Positivas**
- Sem escrita constante no banco por partida em andamento — custo de persistência proporcional a
  mudanças de estado (pausas, gols, cartões, períodos), não ao tempo decorrido.
- Todos os clientes (monitor, alunos assistindo via UC016, outros dispositivos) veem o mesmo tempo,
  pois todos derivam do mesmo snapshot no servidor.
- `clock_seconds` de cada `MatchEvent` é confiável para auditoria (RN41/42): é sempre calculado no
  servidor, nunca aceito como entrada do cliente.
- Reconexão é trivial: um cliente que reabrir a tela busca o snapshot atual e recalcula localmente,
  sem precisar de estado próprio anterior.

**Negativas / trade-offs**
- Exige que todo código que precise do "tempo atual" (registro de evento, fim de período, resposta
  de consulta de partida, broadcast) passe pela mesma função de cálculo — vale extrair isso como um
  helper único (ex.: `Match.current_clock_seconds(now: datetime) -> int`) para não duplicar a
  lógica.
- Se o servidor cair sem checkpoint recente e sem persistência periódica de segurança, o snapshot em
  memória de partidas com `clock_running = True` no momento do crash pode ficar levemente
  desatualizado ao reiniciar. Mitigação: como o snapshot já é gravado em toda transição de estado
  (pausa/retomada/período/evento), a janela de perda potencial é pequena e não crítica — na pior
  hipótese, o monitor pausa e retoma manualmente para "recalibrar" o snapshot.

## Alternativas consideradas

1. **Job persistindo `clock_seconds += 1` a cada segundo por partida em andamento.** Rejeitada:
   atende ao texto literal da RN24, mas gera escrita constante no banco e tráfego de WebSocket
   desnecessário, sem ganho de precisão sobre a abordagem por snapshot.
2. **Cronômetro mantido inteiramente no front-end, enviado pelo cliente ao registrar um evento.**
   Rejeitada: contraria diretamente a RN3 e a RN24 (o Bloco de Dados 1 marca o tempo como Saída, não
   Entrada), abre espaço para divergência entre clientes, drift de relógio do dispositivo, perda de
   estado em caso de reload, e fragiliza a auditoria (RN41/42), já que o tempo do evento passaria a
   ser uma alegação do cliente, não um dado do sistema.

## Referências
- [UC014 - Registrar Evento Durante Partida](../spec/UC014_GestãoDePartidas_RegistrarEvento.md)
- [UC013 - Iniciar Partida](../spec/UC013_GestãoDePartidas_IniciarPartida.md)
- [UC016 - Visualizar Partida em Tempo Real](../spec/UC016_InterfaceUsuário_VisualizarPartida.md)
- `domain/match.py`, `business/match/start_match_adapter.py`
- `docs/AI/planejamento.md` (Fase 5, item pendente UC014)
