# Especificação de Caso de Uso: Finalizar Partida

## 1. Descrição
Este caso de uso permite que o monitor finalize uma partida em andamento, determinando o vencedor (ou registrando empate), atualizando o chaveamento automaticamente e encerrando todas as atividades relacionadas à partida. Em caso de empate em mata-mata, o sistema permite disputa de pênaltis com registro separado do placar oficial.

## 2. Pré-condições
- O ator deve estar autenticado com permissão de **Monitor**;
- Deve existir uma partida com status **IN_PROGRESS**;
- Monitor deve ser o responsável pela partida.

## 3. Fluxo Principal: Finalizar Partida Sem Empate
1. O monitor está na interface de gerenciamento da partida;
2. O monitor clica em "Finalizar Partida";
3. O sistema valida conforme Regras de Negócio;
4. O sistema verifica o placar e identifica que **não há empate**;
5. O sistema determina automaticamente o vencedor baseado no placar;
6. O sistema atualiza status para FINISHED;
7. O sistema define `finished_at = now()`;
8. O sistema pausa cronômetro (`clock_running = false`);
9. O sistema define `winner_id` com o time vencedor;
10. O sistema cria evento MATCH_END;
11. **Se partida for mata-mata (KNOCKOUT):**
    - Sistema avança time vencedor automaticamente para próxima fase;
    - Sistema atualiza partida TBD da próxima fase com o vencedor;
12. **Se partida for fase de grupos (GROUP):**
    - Sistema atualiza BracketGroupTeam com pontos/vitórias;
    - Time vencedor recebe 3 pontos;
    - Time perdedor não ganha pontos;
13. O sistema envia WebSocket: `match_finished`;
14. O sistema envia Push Notification: "Fim de Jogo! [Time A] [X]x[Y] [Time B]";
15. O sistema exibe mensagem de sucesso.

## 4. Fluxos Alternativos

### Fluxo Alternativo 1: Finalizar Partida com Empate (Mata-Mata) - Pênaltis
1. O monitor clica em "Finalizar Partida";
2. O sistema verifica o placar e identifica **empate** (ex: 2x2);
3. O sistema verifica que `match_category = KNOCKOUT`;
4. O sistema exibe popup: "A partida terminou empatada. Iniciar disputa de pênaltis?";
5. Monitor tem duas opções:
   - **Opção A - Iniciar Pênaltis:**
     - Monitor clica em "Iniciar Pênaltis";
     - Sistema cria período especial "PENALTY_SHOOTOUT";
     - Sistema exibe interface simplificada de registro de pênaltis;
     - Monitor registra cada cobrança usando botões: "Time A: Gol" / "Time A: Perdeu" / "Time B: Gol" / "Time B: Perdeu";
     - Sistema conta pênaltis separadamente em `penalty_score`;
     - Eventos são criados com tipo "PENALTY_GOAL" ou "PENALTY_MISS";
     - **Pênaltis NÃO somam ao placar oficial** (`team1_score` e `team2_score` permanecem 2x2);
     - Ao final, monitor clica "Encerrar Pênaltis";
     - Sistema salva resultado em campo `penalty_result`: `{"team1_penalties": 5, "team2_penalties": 4}`;
     - Sistema define vencedor baseado em pênaltis;
     - **Placar oficial permanece 2x2**, mas `winner_id` é definido pelos pênaltis;
     - Sistema continua fluxo principal a partir do passo 6;
   - **Opção B - Cancelar:**
     - Monitor clica em "Cancelar";
     - Partida continua IN_PROGRESS;
     - Monitor pode registrar prorrogação se aplicável.

### Fluxo Alternativo 2: Finalizar Partida com Empate (Fase de Grupos)
1. O monitor clica em "Finalizar Partida";
2. O sistema verifica o placar e identifica **empate** (ex: 1x1);
3. O sistema verifica que `match_category = GROUP`;
4. O sistema **não** exibe popup (empate é resultado válido);
5. O sistema atualiza status para FINISHED;
6. O sistema define `winner_id = NULL`;
7. O sistema atualiza BracketGroupTeam:
   - Ambos os times recebem 1 ponto;
   - Ambos têm `draws++`;
8. Sistema continua fluxo de notificações e finalização;
9. Sistema exibe mensagem de sucesso.

### Fluxo Alternativo 3: Partida Não Está em IN_PROGRESS
1. O monitor tenta finalizar partida em outro status;
2. O sistema bloqueia a operação e exibe mensagem de erro;
3. O sistema informa o status atual da partida.

### Fluxo Alternativo 4: Cancelar Finalização
1. Monitor clica em "Finalizar Partida";
2. Sistema exibe confirmação (se não houver empate mata-mata);
3. Monitor clica em "Cancelar";
4. Sistema fecha modal sem realizar alterações;
5. Partida continua IN_PROGRESS.

### Fluxo Alternativo 5: Finalizar Semifinal - Avançar Vencedor e Perdedor
1. Monitor finaliza partida com `match_type = SEMIFINAL`;
2. Sistema identifica vencedor e perdedor da semifinal;
3. Sistema avança **vencedor** automaticamente para a FINAL;
4. Sistema avança **perdedor** automaticamente para partida de 3º LUGAR;
5. Sistema atualiza ambas as partidas TBD:
   - Final: atualiza `team1_id` ou `team2_id` com vencedor;
   - 3º Lugar: atualiza `team1_id` ou `team2_id` com perdedor;
6. Sistema continua fluxo normal de finalização;
7. Sistema envia notificações.

## 5. Bloco de Dados

### Bloco de Dados 1 – Partida para Finalização

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Time 1                   | S             | Nome e placar oficial                                 |
| Time 2                   | S             | Nome e placar oficial                                 |
| Placar Final             | S             | Placar oficial da partida (tempo regulamentar)        |
| Categoria                | S             | GROUP ou KNOCKOUT                                     |
| Há Empate                | S             | Booleano indicando empate                             |
| Fase/Grupo               | S             | Qual fase ou grupo pertence                           |

### Bloco de Dados 2 – Partida Finalizada

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Status                   | S             | Atualizado de IN_PROGRESS para FINISHED               |
| Data de Finalização      | S             | Timestamp automático                                  |
| Vencedor                 | S             | ID do time vencedor ou NULL (empate em grupos)        |
| Placar Final Oficial     | S             | Placar do tempo regulamentar (ex: 2x2)                |
| Resultado Pênaltis       | S             | JSON com pênaltis (se aplicável): {"team1": 5, "team2": 4} |
| Cronômetro Pausado       | S             | clock_running = false                                 |

### Bloco de Dados 3 – Interface de Pênaltis

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Placar Oficial           | S             | Mantém placar do tempo regulamentar (não muda)        |
| Pênaltis Time 1          | E/S           | Contador separado de pênaltis convertidos             |
| Pênaltis Time 2          | E/S           | Contador separado de pênaltis convertidos             |
| Botões de Registro       | E             | "Time A: Gol", "Time A: Perdeu", etc                  |
| Timeline de Pênaltis     | S             | Lista de cobranças (PENALTY_GOAL, PENALTY_MISS)       |

### Bloco de Dados 4 – Resultado Exibido (Pênaltis)

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Placar Oficial           | S             | Ex: 2x2 (tempo regulamentar)                          |
| Placar Pênaltis          | S             | Ex: 5x4                                               |
| Resultado Completo       | S             | Exibição: "2(5) x 2(4)" indicando pênaltis            |
| Vencedor                 | S             | Definido pelos pênaltis                               |

### Bloco de Dados 5 – Atualização do Chaveamento

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Próxima Partida          | S             | Partida TBD que receberá o vencedor (mata-mata)       |
| Classificação Atualizada | S             | Pontos/vitórias/empates atualizados (grupos)          |
| Time Promovido           | S             | Time que avançou para próxima fase                    |

## 6. Regras de Negócio

### Geral:
1. Apenas **monitor** pode finalizar partida;
2. Partida deve estar em **IN_PROGRESS**;
3. Ao finalizar, status muda para **FINISHED**;
4. `finished_at` é preenchido com timestamp atual;
5. Cronômetro é pausado (`clock_running = false`);
6. Sistema cria evento **MATCH_END** na timeline;
7. Sistema envia **WebSocket** e **Push Notification**;
8. A operação deve ser registrada para auditoria.

### Determinação de Vencedor:
9. **Se não há empate:** Sistema determina vencedor automaticamente pelo placar;
10. **Se há empate em mata-mata (KNOCKOUT):**
    - Sistema exibe interface de disputa de pênaltis;
    - Monitor registra cobranças individuais;
    - **Pênaltis NÃO somam ao placar oficial**;
    - Placar oficial = tempo regulamentar (ex: 2x2);
    - Pênaltis ficam em campo separado `penalty_result`;
    - Vencedor definido pelos pênaltis;
    - Estatísticas de artilharia **não contam gols de pênaltis**;
11. **Se há empate em grupos (GROUP):**
    - Sistema finaliza direto sem popup;
    - `winner_id = NULL`;
    - Empate é resultado válido.

### Atualização do Chaveamento (Mata-Mata):
12. Sistema avança vencedor **automaticamente** para próxima fase;
13. Sistema localiza partida TBD da próxima fase;
14. Sistema atualiza `team1_id` ou `team2_id` com o vencedor;
15. Se não houver próxima fase (final), apenas registra vencedor.

### Atualização do Chaveamento (Grupos):
16. Sistema atualiza tabela **BracketGroupTeam** com resultados:
    - **Vitória:** Time vencedor recebe 3 pontos, `wins++`;
    - **Empate:** Ambos times recebem 1 ponto, `draws++`;
    - **Derrota:** Time perdedor não ganha pontos, `losses++`;
17. Sistema atualiza `goals_for` e `goals_against` de cada time;
18. Classificação é calculada automaticamente baseada em pontos.

### Pênaltis (Disputa de Desempate):
19. Gols de pênaltis (disputa após empate) **NÃO somam ao placar oficial**;
20. Placar oficial permanece o do tempo regulamentar (ex: 2x2);
21. Sistema registra resultado dos pênaltis em campo separado: `penalty_result`;
22. Formato: `{"team1_penalties": 5, "team2_penalties": 4, "winner_id": 123}`;
23. Vencedor é definido pelos pênaltis, mas placar oficial é do tempo regulamentar;
24. Para estatísticas: Gols de pênaltis **não contam** para artilharia individual;
25. Timeline mostra eventos de pênaltis com tag especial "PENALTY_GOAL" ou "PENALTY_MISS";
26. Interface exibe resultado completo como "2(5) x 2(4)" indicando pênaltis.

### Atualização Automática após Semifinais:
27. Ao finalizar partida com `match_type = SEMIFINAL`:
28. **Vencedor** avança automaticamente para partida `match_type = FINAL`;
29. **Perdedor** avança automaticamente para partida `match_type = THIRD_PLACE`; 
30. Sistema localiza partidas por `match_type` (não por posição no bracket); 
31. Se não houver partida de 3º lugar (formatos sem semifinais), perdedor apenas registra derrota.

## 7. Critérios de Aceitação
- O sistema deve bloquear finalização se partida não estiver IN_PROGRESS;
- O sistema deve determinar vencedor automaticamente se não houver empate;
- O sistema deve exibir interface de pênaltis em empate de mata-mata;
- O sistema deve registrar pênaltis separadamente do placar oficial;
- O sistema deve manter placar oficial inalterado durante pênaltis;
- O sistema deve finalizar direto em empate de grupos (sem pênaltis);
- O sistema deve atualizar status para FINISHED;
- O sistema deve pausar cronômetro ao finalizar;
- O sistema deve definir winner_id corretamente;
- O sistema deve avançar vencedor automaticamente em mata-mata;
- O sistema deve atualizar pontos/classificação em grupos;
- O sistema deve criar evento MATCH_END;
- O sistema deve enviar WebSocket e Push Notification;
- O sistema deve exibir resultado como "X(pênaltis) x Y(pênaltis)" quando aplicável;
- O sistema deve exibir mensagens claras de sucesso ou erro;
- O sistema deve registrar a operação para auditoria.

## 8. Pós-condições

### Geral:
- Partida tem status atualizado para FINISHED;
- Data de finalização registrada;
- Cronômetro pausado;
- Evento MATCH_END criado;
- Notificações enviadas via WebSocket e Push;
- Operação registrada para auditoria.

### Mata-Mata:
- `winner_id` definido (não pode ser NULL);
- Vencedor avançado automaticamente para próxima fase;
- Partida TBD da próxima fase atualizada;
- Se houve pênaltis: `penalty_result` registrado separadamente.

### Grupos:
- `winner_id` definido ou NULL (empate);
- BracketGroupTeam atualizado com pontos/vitórias/empates;
- Classificação do grupo recalculada.

## 9. Cenários de Teste

| Cenário                                    | Dado                                           | Quando                              | Então                                                    |
|--------------------------------------------|------------------------------------------------|-------------------------------------|----------------------------------------------------------|
| Finalização sem empate                     | Partida 3x1, IN_PROGRESS                       | Clica em "Finalizar"                | Sistema define vencedor e finaliza automaticamente       |
| Finalização com empate (mata-mata)         | Partida 2x2, KNOCKOUT                          | Clica em "Finalizar"                | Sistema exibe interface de pênaltis                      |
| Registrar pênaltis                         | Interface de pênaltis aberta                   | Registra cobranças 5x4              | Sistema conta pênaltis separadamente                     |
| Placar oficial inalterado (pênaltis)       | Pênaltis registrados, placar era 2x2           | Finaliza com pênaltis 5x4           | Placar oficial permanece 2x2                             |
| Vencedor definido por pênaltis             | Pênaltis 5x4, placar oficial 2x2              | Verifica winner_id                  | Sistema define vencedor pelos pênaltis                   |
| Resultado exibido com pênaltis             | Partida finalizada 2(5) x 2(4)                 | Visualiza resultado                 | Sistema exibe "2(5) x 2(4)"                              |
| Pênaltis não contam para artilharia        | Jogador marcou 2 gols + 1 pênalti             | Verifica estatísticas               | Artilharia conta apenas 2 gols                           |
| Timeline com eventos de pênaltis           | Pênaltis registrados                           | Verifica timeline                   | Eventos têm tag PENALTY_GOAL ou PENALTY_MISS             |
| Cancelar disputa de pênaltis               | Interface de pênaltis, empate 2x2              | Clica "Cancelar"                    | Partida continua IN_PROGRESS                             |
| Finalização com empate (grupos)            | Partida 1x1, GROUP                             | Clica em "Finalizar"                | Sistema finaliza direto sem pênaltis, winner_id=NULL     |
| Partida não IN_PROGRESS                    | Partida SCHEDULED                              | Tenta finalizar                     | Sistema bloqueia e exibe erro                            |
| Cancelar finalização                       | Modal de confirmação aberto                    | Clica em "Cancelar"                 | Sistema fecha sem alterar partida                        |
| Timestamp de finalização                   | Partida finalizada                             | Verifica `finished_at`              | Sistema registra data/hora exata                         |
| Cronômetro pausado                         | Partida finalizada                             | Verifica `clock_running`            | Sistema define como false                                |
| Evento MATCH_END criado                    | Partida finalizada                             | Verifica timeline                   | Sistema registra evento de fim                           |
| Vencedor avança (mata-mata)                | Partida de oitavas finalizada                  | Verifica próxima fase               | Sistema coloca vencedor nas quartas automaticamente      |
| Pontos atualizados (grupos)                | Partida de grupo finalizada 2x0                | Verifica BracketGroupTeam           | Vencedor +3 pts, perdedor +0 pts                         |
| Empate em grupos (pontos)                  | Partida de grupo empatada 1x1                  | Verifica BracketGroupTeam           | Ambos times +1 ponto                                     |
| Penalty_result registrado                  | Pênaltis 5x4                                   | Verifica campo penalty_result       | JSON: {"team1_penalties": 5, "team2_penalties": 4}       |
| WebSocket enviado                          | Partida finalizada                             | Verifica conexões WebSocket         | Sistema envia match_finished                             |
| Push Notification enviado                  | Partida finalizada 3x2                         | Verifica notificações               | Alunos recebem "Fim de Jogo! Time A 3x2 Time B"          |
| Push com pênaltis                          | Partida 2(5) x 2(4)                            | Verifica notificações               | Alunos recebem "Fim! Time A 2(5) x 2(4) Time B"          |
| Auditoria de finalização                   | Partida finalizada                             | Verifica logs                       | Sistema registra monitor, resultado e data/hora          |

## 10. Artefatos Relacionados
- [UC013 - Iniciar Partida](UC013_IniciarPartida.md)
- [UC014 - Registrar Eventos Durante Partida](UC014_RegistrarEventos.md)
- [UC016 - Visualizar Partida em Tempo Real](UC016_VisualizarPartida.md)
- [UC011 - Criar Chaveamento](UC011_CriarChaveamento.md)
- [UC017 - Corrigir Eventos da Partida](UC017_CorrigirEventos.md)