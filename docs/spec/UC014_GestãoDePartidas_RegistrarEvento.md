# Especificação de Caso de Uso: Registrar Eventos Durante Partida

## 1. Descrição
Este caso de uso permite que o monitor registre todos os eventos que ocorrem durante uma partida em andamento, incluindo gols/pontos, cartões, expulsões, controle de cronômetro e gestão de períodos/sets.

## 2. Pré-condições
- O ator deve estar autenticado com permissão de **Monitor**;
- Deve existir uma partida com status **IN_PROGRESS**;
- Monitor deve ser o responsável pela partida (mesmo que a iniciou).

## 3. Fluxo Principal: Marcar Gol/Ponto
1. O monitor está na interface de gerenciamento da partida;
2. O sistema exibe lista de jogadores de ambos os times;
3. O monitor clica em um jogador específico;
4. O sistema exibe opções de ação (Gol/Ponto, Cartão Amarelo, Cartão Vermelho);
5. O monitor seleciona "Gol" ou "Ponto";
6. O sistema valida conforme Regras de Negócio;
7. O sistema cria evento GOAL ou POINT com `clock_seconds` atual;
8. O sistema incrementa placar do time: `team_score++`;
9. Para vôlei, sistema atualiza pontuação do set atual em `metadata`;
10. O sistema atualiza interface com novo placar;
11. O sistema envia WebSocket: `score_update` e `goal_scored`/`point_scored`;
12. O sistema envia Push Notification: "⚽ Gol! [Time] - [Jogador] ([Tempo]')";
13. O sistema exibe confirmação visual.

## 4. Fluxos Alternativos

### Fluxo Alternativo 1: Registrar Cartão Amarelo
1. O monitor clica em um jogador;
2. O monitor seleciona "Cartão Amarelo";
3. O sistema verifica se jogador já possui cartão amarelo nesta partida;
4. **Se jogador NÃO tem amarelo anterior:**
   - Sistema cria evento CARD_YELLOW;
   - Sistema registra em `metadata`: `{"previous_cards": 0}`;
   - Sistema envia WebSocket: `card_issued`;
   - Sistema envia Push Notification: "🟨 Cartão amarelo para [Jogador]";
5. **Se jogador JÁ tem 1 amarelo anterior:**
   - Sistema exibe alerta: "⚠️ Este jogador já possui 1 amarelo. Isso resultará em EXPULSÃO. Confirmar?";
   - Monitor confirma;
   - Sistema cria evento CARD_YELLOW com `metadata`: `{"previous_cards": 1}`;
   - Sistema cria evento EXPULSION com `metadata`: `{"triggered_by": "second_yellow", "auto_generated": true}`;
   - Sistema marca jogador como EXPELLED nesta partida;
   - Sistema envia WebSocket: `card_issued` e `player_expelled`;
   - Sistema envia Push Notifications para ambos eventos;
   - Jogador fica desabilitado visualmente na interface (cinza, opacidade reduzida, ícone vermelho).

### Fluxo Alternativo 2: Registrar Cartão Vermelho Direto
1. O monitor clica em um jogador;
2. O monitor seleciona "Cartão Vermelho";
3. O sistema cria evento CARD_RED;
4. O sistema cria evento EXPULSION;
5. O sistema marca jogador como EXPELLED nesta partida;
6. Sistema envia WebSocket: `card_issued` e `player_expelled`;
7. Sistema envia Push Notifications;
8. Jogador fica desabilitado visualmente na interface.

### Fluxo Alternativo 3: Pausar Cronômetro
1. O monitor clica em "Pausar";
2. O sistema define `clock_running = false`;
3. O cronômetro para de contar;
4. O sistema envia WebSocket: `clock_update` com `running: false`;
5. Interface exibe indicador de cronômetro pausado.

### Fluxo Alternativo 4: Retomar Cronômetro
1. O monitor clica em "Retomar" (cronômetro pausado);
2. O sistema define `clock_running = true`;
3. O cronômetro volta a contar;
4. O sistema envia WebSocket: `clock_update` com `running: true`;
5. Interface exibe cronômetro rodando.

### Fluxo Alternativo 5: Fim de Período
1. Cronômetro continua rodando (inclui acréscimos);
2. Monitor decide encerrar o período e clica em "Fim de Período";
3. O sistema exibe confirmação: "Finalizar [1º/2º] período?";
4. Monitor confirma;
5. O sistema valida conforme Regras de Negócio;
6. O sistema cria evento PERIOD_END;
7. O sistema pausa cronômetro (`clock_running = false`);
8. O sistema incrementa `current_period++`;
9. O sistema envia WebSocket: `period_ended`;
10. Interface exibe "Período encerrado. Clique para iniciar próximo período";
11. Monitor clica em "Iniciar Próximo Período";
12. Sistema cria evento PERIOD_START;
13. Sistema retoma cronômetro;
14. Sistema envia WebSocket: `period_started`.

### Fluxo Alternativo 6: Fim de Set (Vôlei)
1. Set atinge 25 pontos (ou 15 no 5º set) com diferença de 2;
2. Sistema exibe sugestão: "Set Finalizado: [25x23]. Iniciar próximo set?";
3. Monitor confirma;
4. Sistema valida pontuação conforme regras do vôlei;
5. Sistema registra set vencido em `metadata.sets` da partida;
6. Sistema incrementa contagem de sets do time vencedor;
7. Sistema reseta pontuação do set atual para 0x0;
8. Sistema envia WebSocket: `set_finished`;
9. **Se algum time atingiu número de sets necessários (ex: 2 de 3):**
   - Sistema exibe sugestão: "Time atingiu [2] sets. Finalizar partida?";
   - Monitor pode confirmar (vai para UC015) ou continuar.

### Fluxo Alternativo 7: Jogador Expulso Tenta Marcar Gol
1. Monitor tenta marcar gol/ponto para jogador expulso;
2. Sistema bloqueia a operação;
3. Sistema exibe mensagem: "Jogador expulso não pode marcar pontos";
4. Jogador permanece desabilitado na interface.

### Fluxo Alternativo 8: Cancelar Registro de Evento
1. Monitor clica em jogador e seleciona ação;
2. Sistema exibe confirmação;
3. Monitor clica em "Cancelar";
4. Sistema fecha modal sem registrar evento.

## 5. Bloco de Dados

### Bloco de Dados 1 – Evento de Gol/Ponto

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Tipo de Evento           | E             | GOAL ou POINT (dependendo da modalidade)              |
| Time                     | E             | Time que marcou                                       |
| Jogador                  | E             | Jogador que marcou (obrigatório)                      |
| Tempo do Cronômetro      | S             | Segundos do cronômetro no momento do evento           |
| Novo Placar              | S             | Placar atualizado                                     |
| Metadata                 | S             | Para vôlei: pontuação do set atual                    |

### Bloco de Dados 2 – Evento de Cartão

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Tipo de Evento           | E             | CARD_YELLOW ou CARD_RED                               |
| Time                     | E             | Time do jogador                                       |
| Jogador                  | E             | Jogador que recebeu cartão (obrigatório)              |
| Cartões Anteriores       | S             | Quantidade de amarelos anteriores                     |
| Gera Expulsão            | S             | Se 2º amarelo ou vermelho direto                      |
| Metadata                 | S             | Informações adicionais (motivo, etc)                  |

### Bloco de Dados 3 – Evento de Expulsão

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Tipo de Evento           | S             | EXPULSION                                             |
| Jogador                  | S             | Jogador expulso                                       |
| Motivo                   | S             | "second_yellow" ou "direct_red"                       |
| Auto-gerado              | S             | true se gerado automaticamente                        |

### Bloco de Dados 4 – Estado do Cronômetro

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Segundos                 | S             | Tempo atual em segundos                               |
| Rodando                  | S             | true ou false                                         |
| Período Atual            | S             | Número do período (1, 2, 3...)                        |

### Bloco de Dados 5 – Fim de Set (Vôlei)

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Número do Set            | S             | Qual set foi finalizado (1, 2, 3...)                  |
| Placar do Set            | S             | Pontuação final do set (ex: 25x23)                    |
| Vencedor do Set          | S             | Time que venceu o set                                 |
| Sets Totais              | S             | Contagem de sets por time (ex: 2x1)                   |

## 6. Regras de Negócio

### Geral:
1. Apenas **monitor** pode registrar eventos;
2. Partida deve estar em **IN_PROGRESS**;
3. Todos os eventos registram `clock_seconds` atual automaticamente;
4. Todos os eventos são enviados via **WebSocket** em tempo real;
5. Eventos importantes geram **Push Notifications**.

### Gol/Ponto:
6. **Jogador é obrigatório** ao marcar gol/ponto;
7. Jogador deve pertencer ao time;
8. Jogador **não pode estar expulso**;
9. Sistema incrementa placar automaticamente: `team_score++`;
10. Para vôlei, sistema atualiza pontuação do set em `metadata`;
11. Sistema envia WebSocket: `score_update` + `goal_scored`/`point_scored`;
12. Sistema envia Push: "⚽ Gol! [Time] - [Jogador] ([Tempo]')".

### Cartões:
13. **Jogador é obrigatório** ao dar cartão;
14. Jogador deve pertencer ao time;
15. Sistema verifica cartões anteriores do jogador **nesta partida**;
16. **Se 2º amarelo:** Sistema exibe alerta obrigatório antes de confirmar;
17. **2 amarelos = expulsão automática** (evento EXPULSION gerado);
18. **Vermelho direto = expulsão imediata**;
19. Jogador expulso recebe status EXPELLED **nesta partida**;
20. Jogador expulso **não pode marcar gols/pontos**;
21. Jogador expulso permanece visível na interface (cinza, opacidade, ícone vermelho);
22. Sistema envia WebSocket: `card_issued` + `player_expelled` (se aplicável);
23. Sistema envia Push Notifications.

### Cronômetro:
24. Cronômetro atualiza automaticamente no backend a cada segundo;
25. Cronômetro **não para automaticamente** ao atingir tempo configurado (permite acréscimos);
26. Monitor pode pausar/retomar cronômetro a qualquer momento;
27. Monitor decide quando encerrar período manualmente;
28. Sistema envia WebSocket: `clock_update` periodicamente.

### Períodos:
29. Monitor encerra período clicando "Fim de Período";
30. Sistema pausa cronômetro ao fim do período;
31. Sistema incrementa `current_period++`;
32. Sistema cria eventos PERIOD_END e PERIOD_START;
33. Monitor inicia próximo período manualmente.

### Sets (Vôlei):
34. Set finaliza quando time atinge **25 pontos com diferença de 2** (ou 15 no 5º set);
35. Sistema **sugere** fim de set, mas monitor deve confirmar;
36. Sistema registra set vencido em `metadata.sets`;
37. Sistema incrementa contagem de sets do time vencedor;
38. Sistema reseta pontuação do set para 0x0;
39. Se time atinge sets necessários (ex: 2 de 3), sistema sugere finalizar partida;
40. Cronômetro é menos relevante no vôlei (pontuação prevalece).

### Auditoria:
41. Todos os eventos devem ser registrados para auditoria;
42. Cada evento registra: monitor responsável, timestamp, dados completos.

## 7. Critérios de Aceitação
- O sistema deve bloquear registro se partida não estiver IN_PROGRESS;
- O sistema deve exigir jogador ao marcar gol/ponto/cartão;
- O sistema deve bloquear jogador expulso de marcar pontos;
- O sistema deve incrementar placar automaticamente ao marcar gol;
- O sistema deve exibir alerta ao dar 2º amarelo;
- O sistema deve gerar expulsão automática com 2 amarelos;
- O sistema deve marcar jogador como EXPELLED após expulsão;
- O sistema deve manter jogador expulso visível mas desabilitado;
- O sistema deve permitir pausar/retomar cronômetro;
- O sistema deve permitir monitor encerrar período manualmente;
- O sistema deve sugerir fim de set no vôlei (25 pts com dif. 2);
- O sistema deve enviar WebSocket para todos os eventos;
- O sistema deve enviar Push Notifications para eventos importantes;
- O sistema deve registrar timestamp de cada evento;
- O sistema deve exibir mensagens claras de confirmação/erro;
- O sistema deve registrar todas as operações para auditoria.

## 8. Pós-condições

### Gol/Ponto:
- Evento GOAL/POINT criado;
- Placar atualizado;
- WebSocket e Push enviados;
- Operação registrada para auditoria.

### Cartão:
- Evento CARD_YELLOW/CARD_RED criado;
- Se 2º amarelo ou vermelho: evento EXPULSION criado;
- Jogador marcado como EXPELLED (se aplicável);
- WebSocket e Push enviados;
- Operação registrada para auditoria.

### Cronômetro:
- Estado atualizado (pausado/rodando);
- WebSocket enviado;
- Interface atualizada.

### Período:
- Eventos PERIOD_END/START criados;
- Período incrementado;
- Cronômetro pausado/retomado;
- WebSocket enviado.

### Set (Vôlei):
- Set registrado em metadata;
- Contagem de sets atualizada;
- Pontuação do set resetada;
- WebSocket enviado.

## 9. Cenários de Teste

| Cenário                                    | Dado                                           | Quando                              | Então                                                    |
|--------------------------------------------|------------------------------------------------|-------------------------------------|----------------------------------------------------------|
| Marcar gol com sucesso                     | Partida IN_PROGRESS, jogador válido            | Clica jogador e "Gol"               | Sistema registra, atualiza placar e notifica            |
| Marcar ponto para jogador expulso          | Jogador com status EXPELLED                    | Tenta marcar ponto                  | Sistema bloqueia e exibe erro                           |
| Primeiro cartão amarelo                    | Jogador sem cartões anteriores                 | Dá cartão amarelo                   | Sistema registra cartão e notifica                      |
| Segundo cartão amarelo                     | Jogador com 1 amarelo anterior                 | Dá 2º amarelo                       | Sistema exibe alerta, gera expulsão e notifica          |
| Cartão vermelho direto                     | Jogador sem cartões                            | Dá vermelho direto                  | Sistema registra cartão, gera expulsão e notifica       |
| Jogador expulso fica visível               | Jogador expulso                                | Verifica interface                  | Jogador aparece cinza/opaco com ícone vermelho          |
| Pausar cronômetro                          | Cronômetro rodando                             | Clica "Pausar"                      | Cronômetro para e notifica via WebSocket                |
| Retomar cronômetro                         | Cronômetro pausado                             | Clica "Retomar"                     | Cronômetro volta a contar e notifica                    |
| Fim de período                             | Período em andamento                           | Clica "Fim de Período"              | Sistema pausa, incrementa período e notifica            |
| Iniciar próximo período                    | Período encerrado                              | Clica "Iniciar Próximo"             | Sistema cria evento e retoma cronômetro                 |
| Fim de set no vôlei (25 pts)               | Vôlei, set em 25x23                            | Sistema sugere fim                  | Monitor confirma, sistema registra set                  |
| Fim de set sem diferença de 2              | Vôlei, set em 25x24                            | Jogo continua                       | Sistema não sugere fim (falta diferença de 2)           |
| Vôlei atinge 2 sets                        | Time vence 2º set (2x0)                        | Sistema sugere finalizar            | Monitor pode confirmar ou continuar                     |
| Cancelar registro de gol                   | Modal de confirmação aberto                    | Clica "Cancelar"                    | Sistema fecha sem registrar                             |
| Timestamp automático                       | Qualquer evento registrado                     | Verifica `clock_seconds`            | Sistema registra tempo exato do cronômetro              |
| WebSocket enviado                          | Gol marcado                                    | Verifica conexões WebSocket         | Sistema envia score_update e goal_scored                |
| Push Notification enviado                  | Gol marcado                                    | Verifica notificações               | Alunos recebem "⚽ Gol! Time - Jogador"                 |
| Auditoria de eventos                       | Vários eventos registrados                     | Verifica logs                       | Sistema registra monitor, timestamp e dados completos   |

## 10. Artefatos Relacionados
- [UC013 - Iniciar Partida](UC013_IniciarPartida.md)
- [UC015 - Finalizar Partida](UC015_FinalizarPartida.md)
- [UC016 - Visualizar Partida em Tempo Real](UC016_VisualizarPartida.md)
- [UC017 - Corrigir Eventos da Partida](UC017_CorrigirEventos.md)
- [ADR 0001 - Estratégia do Cronômetro da Partida](adr/0001-cronometro-partida-uc014.md) — decisão
  técnica de como as regras 3, 24, 25 e 28 (cronômetro autoritativo no backend) devem ser
  implementadas, evitando escrita persistida a cada segundo.

## 11. Sugestão de UI
1. Monitor acessa partida agendada
2. Clica "Iniciar Partida" → status SCHEDULED → IN_PROGRESS
3. Interface mostra:
   - Placar grande
   - Botões rápidos: +1 para cada time
   - Lista de jogadores de cada time (clicáveis)
   - Botões de cartão
   - Linha do tempo de eventos
4. Para marcar gol:
   - Opção A: Clica "+1 Time A" → popup pergunta "Qual jogador?" (opcional)
   - Opção B: Clica direto no jogador → popup "Gol? Cartão? Substituição?"
5. Finaliza partida → status IN_PROGRESS → FINISHED