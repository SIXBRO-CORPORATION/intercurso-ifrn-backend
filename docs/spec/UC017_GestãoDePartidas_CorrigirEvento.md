# Especificação de Caso de Uso: Corrigir Eventos da Partida

## 1. Descrição
Este caso de uso permite que o monitor corrija erros durante ou após uma partida, incluindo desfazer o último evento registrado ou deletar eventos específicos da timeline, garantindo a integridade dos dados da partida. Correções em partidas finalizadas geram alertas especiais sobre impacto no chaveamento.

## 2. Pré-condições
- O ator deve estar autenticado com permissão de **Monitor**;
- Deve existir uma partida com status **IN_PROGRESS** ou **FINISHED**;
- Deve existir ao menos um evento registrado na partida.

## 3. Fluxo Principal: Desfazer Último Evento
1. O monitor está na interface de gerenciamento da partida;
2. O sistema exibe botão "Desfazer" acessível;
3. O monitor clica em "Desfazer";
4. O sistema identifica o último evento registrado **nesta sessão/dispositivo**;
5. O sistema valida conforme Regras de Negócio;
6. O sistema exibe confirmação: "Desfazer [tipo de evento]? ([Jogador] - [Tempo])";
7. O monitor confirma;
8. O sistema marca evento como `deleted = true` (soft delete);
9. O sistema recalcula placar removendo o evento;
10. **Se evento era expulsão ou 2º cartão amarelo:**
    - Sistema remove status EXPELLED do jogador;
    - Jogador volta a ficar ativo e clicável;
11. O sistema atualiza interface com novo placar e timeline;
12. O sistema envia WebSocket: `event_deleted` e `score_updated`;
13. O sistema exibe mensagem de sucesso.

## 4. Fluxos Alternativos

### Fluxo Alternativo 1: Deletar Evento Específico da Timeline
1. Monitor acessa "Timeline de Eventos" da partida;
2. Sistema exibe lista completa de eventos ordenados cronologicamente;
3. Monitor clica em evento específico;
4. Monitor clica em "Deletar Evento";
5. Sistema exibe confirmação com detalhes do evento;
6. Monitor confirma;
7. Sistema valida conforme Regras de Negócio;
8. Sistema marca evento como `deleted = true`;
9. Sistema recalcula placar e estatísticas;
10. **Se evento era expulsão ou 2º amarelo:** Sistema reativa jogador;
11. Sistema atualiza interface e timeline;
12. Sistema envia WebSocket: `event_deleted` e `score_updated`;
13. Sistema exibe mensagem de sucesso.

### Fluxo Alternativo 2: Tentar Desfazer Evento Não Permitido
1. Monitor tenta desfazer evento do tipo PERIOD_START, PERIOD_END ou MATCH_START;
2. Sistema bloqueia a operação;
3. Sistema exibe mensagem: "Este tipo de evento não pode ser desfeito";
4. Botão "Desfazer" permanece disponível para outros eventos.

### Fluxo Alternativo 3: Desfazer Sem Eventos Recentes
1. Monitor acabou de entrar na interface (nova sessão);
2. Não há eventos registrados nesta sessão/dispositivo;
3. Sistema desabilita botão "Desfazer";
4. Monitor pode usar "Timeline" para deletar eventos específicos.

### Fluxo Alternativo 4: Deletar Expulsão (Reativar Jogador)
1. Monitor acessa timeline e seleciona evento EXPULSION;
2. Monitor deleta o evento;
3. Sistema remove status EXPELLED do jogador;
4. Sistema verifica se há outros cartões do jogador:
   - Se era expulsão por 2º amarelo: mantém os 2 amarelos mas remove expulsão;
   - Se era vermelho direto: remove expulsão e cartão vermelho;
5. Jogador volta a aparecer ativo na interface (sem opacidade);
6. Monitor pode selecionar jogador normalmente para marcar gols.

### Fluxo Alternativo 5: Deletar 2º Cartão Amarelo (Reverter Expulsão)
1. Monitor acessa timeline e seleciona 2º cartão amarelo;
2. Monitor deleta o cartão;
3. Sistema remove evento CARD_YELLOW;
4. Sistema verifica se há expulsão vinculada e remove automaticamente;
5. Jogador perde status EXPELLED e volta ao jogo;
6. Jogador fica com apenas 1 cartão amarelo na partida.

### Fluxo Alternativo 6: Cancelar Deleção
1. Monitor clica em deletar evento;
2. Sistema exibe confirmação;
3. Monitor clica em "Cancelar";
4. Sistema fecha modal sem realizar alterações;
5. Evento permanece na timeline.

### Fluxo Alternativo 7: Corrigir Após Partida Finalizada - Placar Alterado
1. Partida tem status FINISHED;
2. Monitor acessa timeline para correção;
3. Monitor deleta evento de gol;
4. Sistema recalcula placar final;
5. **Sistema detecta que vencedor pode ter mudado**;
6. Sistema exibe alerta grande em destaque:
   ```
   ⚠️ ATENÇÃO CRÍTICA: PLACAR ALTERADO EM PARTIDA FINALIZADA
   
   Placar anterior: Time A 2 x 1 Time B (Vencedor: Time A)
   Placar corrigido: Time A 1 x 1 Time B (EMPATE)
   
   🚨 O VENCEDOR DA PARTIDA PODE TER MUDADO!
   
   Você deve IMEDIATAMENTE:
   1. Verificar se o time correto avançou no chaveamento
   2. Corrigir manualmente a próxima fase se necessário (UC012)
   3. Notificar os alunos sobre a correção
   4. Registrar justificativa da alteração
   
   Esta correção foi registrada em auditoria.
   ```
7. Sistema mantém `winner_id` original (não atualiza automaticamente);
8. Sistema registra correção pós-jogo em auditoria com destaque;
9. Monitor deve corrigir chaveamento manualmente se necessário.

### Fluxo Alternativo 8: Deletar Evento de Pênalti
1. Monitor deleta evento de tipo PENALTY_GOAL ou PENALTY_MISS;
2. Sistema atualiza campo `penalty_result` recalculando pênaltis;
3. **Sistema não altera placar oficial** (pênaltis são separados);
4. Se vencedor foi definido por pênaltis, sistema exibe alerta de Fluxo Alternativo 7;
5. Sistema registra correção para auditoria.

## 5. Bloco de Dados

### Bloco de Dados 1 – Evento para Desfazer/Deletar

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Tipo de Evento           | S             | GOAL, POINT, CARD_YELLOW, CARD_RED, EXPULSION, PENALTY_GOAL, PENALTY_MISS |
| Jogador                  | S             | Nome do jogador envolvido                             |
| Time                     | S             | Time do jogador                                       |
| Tempo                    | S             | Momento em que ocorreu (minuto)                       |
| Impacto                  | S             | O que será revertido (placar, status de expulsão, pênaltis) |
| Pode Desfazer            | S             | Boolean indicando se tipo é permitido                 |

### Bloco de Dados 2 – Confirmação de Deleção

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Mensagem                 | S             | "Desfazer Gol de João Silva aos 15'32?"              |
| Evento Completo          | S             | Detalhes do evento que será deletado                  |
| Aviso                    | S             | "O placar será atualizado" ou avisos específicos      |
| Botões                   | E             | "Confirmar" e "Cancelar"                              |

### Bloco de Dados 3 – Alerta de Correção Pós-Jogo

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Tipo de Alerta           | S             | CRITICAL (vencedor pode ter mudado)                   |
| Placar Anterior          | S             | Placar antes da correção                              |
| Placar Corrigido         | S             | Placar após correção                                  |
| Vencedor Anterior        | S             | Time que era vencedor                                 |
| Status Atual             | S             | Empate, nova vitória, etc                             |
| Ações Necessárias        | S             | Lista de tarefas para o monitor                       |
| Impacto no Chaveamento   | S             | Se time avançou incorretamente                        |

### Bloco de Dados 4 – Timeline de Eventos

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Lista de Eventos         | S             | Todos os eventos não deletados, ordenados             |
| Ícone do Evento          | S             | Visual do tipo de evento                              |
| Descrição                | S             | Texto descritivo do evento                            |
| Tempo                    | S             | Quando ocorreu                                        |
| Ações                    | S             | Botão "Deletar" para eventos permitidos               |

### Bloco de Dados 5 – Resultado da Correção

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Evento Deletado          | S             | ID do evento removido                                 |
| Novo Placar              | S             | Placar recalculado                                    |
| Jogador Reativado        | S             | Se aplicável, jogador que voltou a ficar ativo        |
| Impactos                 | S             | Outras mudanças (cartões, expulsões, pênaltis)        |
| Alerta Gerado            | S             | Se correção pós-jogo gerou alerta crítico             |

## 6. Regras de Negócio

### Geral:
1. Apenas **monitor** pode corrigir eventos;
2. Eventos podem ser corrigidos durante **IN_PROGRESS** ou **FINISHED**;
3. Sistema realiza **soft delete** (marca `deleted = true`);
4. Eventos deletados **não aparecem** em listagens e timeline;
5. Sistema **recalcula placar** após deletar gol/ponto;
6. Sistema **recalcula estatísticas** após qualquer deleção;
7. Sistema envia **WebSocket** notificando correção;
8. **Push Notifications enviadas não podem ser removidas** dos dispositivos;
9. A operação deve ser registrada para auditoria.

### Desfazer (Botão):
10. Botão "Desfazer" deleta **último evento da sessão/dispositivo atual**;
11. Não deleta baseado apenas em timestamp (pode haver eventos simultâneos);
12. Botão só funciona para eventos **recentes da mesma sessão**;
13. Ao entrar na interface (nova sessão), botão fica desabilitado até novo evento.

### Deletar da Timeline:
14. Monitor pode deletar **qualquer evento** via timeline;
15. Timeline exibe todos os eventos não deletados ordenados;
16. Monitor seleciona evento específico e clica "Deletar".

### Eventos Permitidos:
17. **Podem ser desfeitos/deletados:**
    - GOAL, POINT (gols/pontos)
    - CARD_YELLOW, CARD_RED (cartões)
    - EXPULSION (expulsões)
    - PENALTY_GOAL, PENALTY_MISS (pênaltis)
    - TIMEOUT (pedido de tempo)
18. **NÃO podem ser desfeitos/deletados:**
    - MATCH_START, MATCH_END (início/fim de partida)
    - PERIOD_START, PERIOD_END (início/fim de período)
19. Sistema bloqueia deleção de eventos não permitidos.

### Reversão de Expulsão:
20. Ao deletar EXPULSION: jogador perde status EXPELLED e volta ativo;
21. Ao deletar 2º CARD_YELLOW: sistema remove automaticamente EXPULSION vinculada;
22. Ao deletar CARD_RED direto: sistema remove EXPULSION vinculada;
23. Jogador reativado volta a ser clicável e pode marcar gols;
24. Interface atualiza visual do jogador (remove opacidade/cinza).

### Recálculo de Placar:
25. Ao deletar GOAL/POINT: placar decrementa (`team_score--`);
26. Ao deletar PENALTY_GOAL/PENALTY_MISS: atualiza apenas `penalty_result`, não placar oficial;
27. Sistema mantém consistência entre eventos e placar;
28. Para vôlei: sistema atualiza pontuação do set em `metadata`.

### Correções Pós-Jogo (CRÍTICO):
29. Correções em partidas FINISHED são permitidas;
30. Placar final pode mudar com correções;
31. **Sistema NÃO atualiza winner_id ou chaveamento automaticamente** (V1);
32. Sistema exibe **alerta crítico grande e detalhado** se placar mudar:
    - Destaca mudança de vencedor em vermelho;
    - Lista ações obrigatórias do monitor;
    - Instrui verificação manual do chaveamento;
    - Solicita notificação aos alunos;
33. Monitor é **totalmente responsável** por propagar correção manualmente;
34. Correções pós-jogo são registradas com **destaque especial** em auditoria;
35. Sistema mantém histórico completo (evento original + deleção) para investigação.

### Integridade de Dados:
36. Sistema garante que placar sempre reflete eventos não deletados;
37. Sistema valida consistência após cada correção;
38. Eventos deletados mantêm dados originais (soft delete para auditoria);
39. Sistema previne corrupção de dados em caso de erro.

## 7. Critérios de Aceitação
- O sistema deve permitir desfazer último evento da sessão;
- O sistema deve permitir deletar eventos específicos via timeline;
- O sistema deve bloquear deleção de eventos não permitidos;
- O sistema deve marcar eventos como deleted (soft delete);
- O sistema deve recalcular placar após deletar gol/ponto;
- O sistema deve recalcular pênaltis separadamente do placar oficial;
- O sistema deve remover status EXPELLED ao deletar expulsão;
- O sistema deve reativar jogador após deletar expulsão/2º amarelo;
- O sistema deve enviar WebSocket notificando correção;
- O sistema deve atualizar interface instantaneamente;
- O sistema deve permitir correções em partidas FINISHED;
- O sistema deve exibir alerta crítico se placar de partida finalizada mudar;
- O sistema deve exibir confirmação antes de deletar;
- O sistema deve exibir mensagens claras de sucesso ou erro;
- O sistema deve registrar todas as correções para auditoria com destaque especial para pós-jogo;
- O sistema deve garantir integridade entre eventos e placar.

## 8. Pós-condições

### Evento Desfeito/Deletado:
- Evento marcado como `deleted = true`;
- Evento não aparece mais na timeline;
- Placar recalculado (se aplicável);
- Operação registrada para auditoria.

### Jogador Reativado:
- Status EXPELLED removido;
- Jogador volta a ser clicável;
- Visual atualizado (sem opacidade/cinza);
- Jogador pode marcar gols novamente.

### Correção Pós-Jogo:
- Placar final corrigido;
- Alerta crítico exibido ao monitor;
- `winner_id` original mantido (não atualiza automaticamente);
- Monitor ciente da necessidade de verificar chaveamento;
- Correção registrada com destaque especial em auditoria.

### Notificações:
- WebSocket enviado com `event_deleted` e `score_updated`;
- Interface dos alunos atualizada instantaneamente;
- Push Notifications já enviadas permanecem nos dispositivos.

## 9. Cenários de Teste

| Cenário                                    | Dado                                           | Quando                              | Então                                                    |
|--------------------------------------------|------------------------------------------------|-------------------------------------|----------------------------------------------------------|
| Desfazer último gol                        | Gol marcado há pouco                           | Clica "Desfazer"                    | Sistema deleta gol, decrementa placar e notifica         |
| Desfazer cartão amarelo                    | Cartão dado recentemente                       | Clica "Desfazer"                    | Sistema deleta cartão e notifica                         |
| Desfazer expulsão                          | Jogador expulso recentemente                   | Clica "Desfazer"                    | Sistema deleta expulsão e reativa jogador                |
| Deletar evento específico da timeline      | Timeline com vários eventos                    | Seleciona evento e deleta           | Sistema deleta evento selecionado e recalcula            |
| Tentar desfazer PERIOD_START               | Período iniciado recentemente                  | Clica "Desfazer"                    | Sistema bloqueia e exibe erro                            |
| Tentar desfazer MATCH_START                | Partida iniciada recentemente                  | Tenta desfazer                      | Sistema bloqueia operação                                |
| Desfazer sem eventos na sessão             | Monitor acabou de entrar                       | Verifica botão "Desfazer"           | Botão está desabilitado                                  |
| Deletar 2º amarelo (reverter expulsão)     | Jogador com 2 amarelos e expulso               | Deleta 2º amarelo da timeline       | Sistema remove amarelo e expulsão, reativa jogador       |
| Deletar vermelho direto                    | Jogador expulso por vermelho                   | Deleta cartão vermelho              | Sistema remove cartão e expulsão, reativa jogador        |
| Jogador reativado volta clicável           | Expulsão deletada                              | Verifica interface                  | Jogador aparece normal (sem opacidade) e clicável        |
| Recalcular placar após deletar gol         | Placar 3x2, deleta 1 gol                       | Verifica placar                     | Placar atualiza para 2x2                                 |
| Deletar pênalti não altera placar oficial  | Pênaltis 5x4, placar oficial 2x2              | Deleta 1 PENALTY_GOAL               | Placar oficial permanece 2x2, pênaltis viram 4x4        |
| Correção em partida finalizada             | Partida FINISHED, deleta gol                   | Confirma deleção                    | Sistema permite e recalcula placar final                 |
| Alerta crítico - vencedor mudou            | Partida FINISHED 2x1, deleta gol, fica 1x1     | Deleta evento                       | Sistema exibe alerta vermelho crítico e detalhado        |
| Alerta crítico - placar invertido          | Partida FINISHED 2x1, deleta 2 gols, fica 0x1  | Deleta eventos                      | Sistema alerta que vencedor inverteu                     |
| Winner_id não atualiza automaticamente     | Correção pós-jogo muda vencedor                | Verifica winner_id                  | Mantém winner_id original, alerta monitor para correção manual |
| Cancelar deleção                           | Modal de confirmação aberto                    | Clica "Cancelar"                    | Sistema fecha sem deletar                                |
| Timeline atualizada                        | Evento deletado                                | Verifica timeline                   | Evento não aparece mais na lista                         |
| WebSocket enviado                          | Evento deletado                                | Verifica conexões WebSocket         | Sistema envia event_deleted                              |
| Placar atualizado para alunos              | Gol deletado durante partida                   | Verifica tela de alunos             | Placar atualiza instantaneamente via WebSocket           |
| Push não é removido                        | Deletar gol que gerou Push                     | Verifica dispositivos               | Push permanece nos dispositivos dos alunos               |
| Soft delete (dados mantidos)               | Evento deletado                                | Verifica banco de dados             | Evento marcado deleted=true, dados originais preservados |
| Auditoria de correção                      | Evento deletado                                | Verifica logs                       | Sistema registra monitor, evento deletado e data/hora    |
| Auditoria pós-jogo destacada               | Correção em partida FINISHED                   | Verifica logs                       | Sistema registra como correção pós-jogo com destaque     |
| Consistência placar vs eventos             | Múltiplas correções                            | Valida placar                       | Placar sempre reflete eventos não deletados              |
| Texto do alerta crítico                    | Correção pós-jogo, vencedor mudou              | Lê alerta exibido                   | Texto inclui placares, ações obrigatórias e avisos       |

## 10. Artefatos Relacionados
- [UC013 - Iniciar Partida](UC013_IniciarPartida.md)
- [UC014 - Registrar Eventos Durante Partida](UC014_RegistrarEventos.md)
- [UC015 - Finalizar Partida](UC015_FinalizarPartida.md)
- [UC016 - Visualizar Partida em Tempo Real](UC016_VisualizarPartida.md)
- [UC012 - Gerenciar Chaveamento](UC012_GerenciarChaveamento.md)