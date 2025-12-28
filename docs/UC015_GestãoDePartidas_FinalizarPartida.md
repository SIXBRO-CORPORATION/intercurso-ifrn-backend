# Especificação de Caso de Uso: Finalizar Partida

## 1. Descrição
Este caso de uso permite que o monitor finalize uma partida em andamento, determinando o vencedor (ou registrando empate), atualizando o chaveamento automaticamente e encerrando todas as atividades relacionadas à partida.

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

### Fluxo Alternativo 1: Finalizar Partida com Empate (Mata-Mata)
1. O monitor clica em "Finalizar Partida";
2. O sistema verifica o placar e identifica **empate** (ex: 2x2);
3. O sistema verifica que `match_category = KNOCKOUT`;
4. O sistema exibe popup: "A partida terminou empatada. Quem avança para a próxima fase?";
5. Monitor tem duas opções:
   - **Opção A - Selecionar Vencedor:**
     - Monitor seleciona um dos times;
     - Monitor confirma;
     - Sistema define `winner_id` com time selecionado;
     - Sistema continua fluxo principal a partir do passo 6;
   - **Opção B - Cancelar (Pênaltis):**
     - Monitor clica em "Cancelar";
     - Popup fecha;
     - Partida continua IN_PROGRESS;
     - Monitor pode registrar gols de pênaltis (vão para placar oficial);
     - Monitor clica "Finalizar" novamente quando decidir vencedor.

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

## 5. Bloco de Dados

### Bloco de Dados 1 – Partida para Finalização

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Time 1                   | S             | Nome e placar                                         |
| Time 2                   | S             | Nome e placar                                         |
| Placar Final             | S             | Placar atual da partida                               |
| Categoria                | S             | GROUP ou KNOCKOUT                                     |
| Há Empate                | S             | Booleano indicando empate                             |
| Fase/Grupo               | S             | Qual fase ou grupo pertence                           |

### Bloco de Dados 2 – Partida Finalizada

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Status                   | S             | Atualizado de IN_PROGRESS para FINISHED               |
| Data de Finalização      | S             | Timestamp automático                                  |
| Vencedor                 | S             | ID do time vencedor ou NULL (empate em grupos)        |
| Placar Final             | S             | Placar definitivo da partida                          |
| Cronômetro Pausado       | S             | clock_running = false                                 |

### Bloco de Dados 3 – Popup de Empate (Mata-Mata)

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Mensagem                 | S             | "A partida terminou empatada. Quem avança?"           |
| Opções de Times          | E             | Time 1 ou Time 2 (botões/radio)                       |
| Botões                   | E             | "Confirmar" e "Cancelar"                              |

### Bloco de Dados 4 – Atualização do Chaveamento

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
    - Sistema **exige** que monitor selecione vencedor via popup;
    - Monitor pode cancelar para registrar pênaltis;
    - Gols de pênaltis somam ao placar oficial;
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

### Pênaltis (V1):
19. Gols marcados durante pênaltis **somam ao placar oficial**;
20. Monitor registra gols normalmente durante cobrança;
21. Placar final reflete resultado real (incluindo pênaltis);
22. Sistema não diferencia gols de tempo normal e pênaltis (V2).

## 7. Critérios de Aceitação
- O sistema deve bloquear finalização se partida não estiver IN_PROGRESS;
- O sistema deve determinar vencedor automaticamente se não houver empate;
- O sistema deve exibir popup em empate de mata-mata;
- O sistema deve permitir cancelar popup para registrar pênaltis;
- O sistema deve finalizar direto em empate de grupos (sem popup);
- O sistema deve atualizar status para FINISHED;
- O sistema deve pausar cronômetro ao finalizar;
- O sistema deve definir winner_id corretamente;
- O sistema deve avançar vencedor automaticamente em mata-mata;
- O sistema deve atualizar pontos/classificação em grupos;
- O sistema deve criar evento MATCH_END;
- O sistema deve enviar WebSocket e Push Notification;
- O sistema deve registrar gols de pênaltis no placar oficial;
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
- Partida TBD da próxima fase atualizada.

### Grupos:
- `winner_id` definido ou NULL (empate);
- BracketGroupTeam atualizado com pontos/vitórias/empates;
- Classificação do grupo recalculada.

## 9. Cenários de Teste

| Cenário                                    | Dado                                           | Quando                              | Então                                                    |
|--------------------------------------------|------------------------------------------------|-------------------------------------|----------------------------------------------------------|
| Finalização sem empate                     | Partida 3x1, IN_PROGRESS                       | Clica "Finalizar"                   | Sistema define vencedor e finaliza automaticamente       |
| Finalização com empate (mata-mata)         | Partida 2x2, KNOCKOUT                          | Clica "Finalizar"                   | Sistema exibe popup "Quem avança?"                       |
| Selecionar vencedor no popup               | Popup aberto, empate mata-mata                 | Seleciona Time A e confirma         | Sistema define Time A como vencedor e finaliza           |
| Cancelar popup para pênaltis               | Popup aberto, empate mata-mata                 | Clica "Cancelar"                    | Partida continua IN_PROGRESS para pênaltis               |
| Registrar pênaltis e finalizar             | Pênaltis registrados, placar 4x3               | Clica "Finalizar" novamente         | Sistema finaliza com placar 4x3 (inclui pênaltis)       |
| Finalização com empate (grupos)            | Partida 1x1, GROUP                             | Clica "Finalizar"                   | Sistema finaliza direto sem popup, winner_id=NULL        |
| Partida não IN_PROGRESS                    | Partida SCHEDULED                              | Tenta finalizar                     | Sistema bloqueia e exibe erro                            |
| Cancelar finalização                       | Modal de confirmação aberto                    | Clica "Cancelar"                    | Sistema fecha sem alterar partida                        |
| Timestamp de finalização                   | Partida finalizada                             | Verifica `finished_at`              | Sistema registra data/hora exata                         |
| Cronômetro pausado                         | Partida finalizada                             | Verifica `clock_running`            | Sistema define como false                                |
| Evento MATCH_END criado                    | Partida finalizada                             | Verifica timeline                   | Sistema registra evento de fim                           |
| Vencedor avança (mata-mata)                | Partida de oitavas finalizada                  | Verifica próxima fase               | Sistema coloca vencedor nas quartas automaticamente      |
| Pontos atualizados (grupos)                | Partida de grupo finalizada 2x0                | Verifica BracketGroupTeam           | Vencedor +3 pts, perdedor +0 pts                         |
| Empate em grupos (pontos)                  | Partida de grupo empatada 1x1                  | Verifica BracketGroupTeam           | Ambos times +1 ponto                                     |
| Gols de pênaltis no placar                 | Pênaltis registrados como gols normais         | Verifica placar final               | Placar reflete todos os gols (normal + pênaltis)         |
| WebSocket enviado                          | Partida finalizada                             | Verifica conexões WebSocket         | Sistema envia match_finished                             |
| Push Notification enviado                  | Partida finalizada 3x2                         | Verifica notificações               | Alunos recebem "Fim de Jogo! Time A 3x2 Time B"          |
| Auditoria de finalização                   | Partida finalizada                             | Verifica logs                       | Sistema registra monitor, resultado e data/hora          |

## 10. Artefatos Relacionados
- [UC013 - Iniciar Partida](UC013_IniciarPartida.md)
- [UC014 - Registrar Eventos Durante Partida](UC014_RegistrarEventos.md)
- [UC016 - Visualizar Partida em Tempo Real](UC016_VisualizarPartida.md)
- [UC011 - Criar Chaveamento](UC011_CriarChaveamento.md)