# Especificação de Caso de Uso: Visualizar Partida em Tempo Real

## 1. Descrição
Este caso de uso permite que alunos visualizem partidas em tempo real, recebendo atualizações instantâneas de placar, eventos (gols, cartões, expulsões) e cronômetro através de conexão WebSocket, além de receber Push Notifications para eventos importantes.

## 2. Pré-condições
- O ator deve estar autenticado como **Aluno**;
- Deve existir ao menos uma partida com status **IN_PROGRESS** ou **SCHEDULED**.

## 3. Fluxo Principal: Visualizar Feed de Jogos ao Vivo
1. O aluno acessa a aba "Jogos" do aplicativo;
2. O sistema conecta ao WebSocket do canal da temporada (`/seasons/{season_id}/live`);
3. O sistema exibe lista de partidas da temporada conforme Bloco de Dados 1;
4. Para partidas **IN_PROGRESS:**
   - Sistema exibe placar atualizado em tempo real;
   - Sistema exibe cronômetro atualizado;
   - Sistema exibe indicador visual "AO VIVO";
5. O aluno visualiza updates de todas as partidas simultaneamente;
6. Ao receber evento via WebSocket:
   - Sistema atualiza placar instantaneamente;
   - Sistema exibe animação de notificação (gol/cartão);
   - Sistema atualiza cronômetro automaticamente;
7. Aluno permanece na tela recebendo updates contínuos.

## 4. Fluxos Alternativos

### Fluxo Alternativo 1: Visualizar Detalhes de Partida Específica
1. Aluno está no feed de jogos;
2. Aluno clica em uma partida específica;
3. Sistema desconecta do canal da temporada;
4. Sistema conecta ao WebSocket do canal da partida (`/matches/{match_id}/live`);
5. Sistema exibe detalhes completos conforme Bloco de Dados 2;
6. Aluno recebe updates detalhados:
   - Timeline completa de eventos (gols, cartões, períodos);
   - Placar atualizado em tempo real;
   - Cronômetro atualizado a cada segundo;
   - Estatísticas da partida (se disponível);
7. Ao receber evento via WebSocket:
   - Sistema adiciona evento à timeline instantaneamente;
   - Sistema atualiza placar;
   - Sistema exibe notificação visual do evento;
8. Aluno pode voltar ao feed clicando "Voltar";
9. Sistema desconecta do canal da partida e reconecta ao da temporada.

### Fluxo Alternativo 2: Receber Push Notification
1. Aluno não está com aplicativo aberto;
2. Evento importante ocorre (gol, cartão vermelho, início/fim de partida);
3. Sistema backend envia Push Notification ao dispositivo;
4. Aluno recebe notificação no dispositivo;
5. Aluno clica na notificação;
6. Sistema abre aplicativo diretamente na tela de detalhes da partida;
7. Sistema conecta ao WebSocket da partida;
8. Aluno visualiza detalhes atualizados.

### Fluxo Alternativo 3: Visualizar Partida Finalizada
1. Aluno acessa partida com status FINISHED;
2. Sistema **não** conecta ao WebSocket;
3. Sistema exibe informações estáticas:
   - Placar final;
   - Timeline completa de eventos;
   - Estatísticas finais;
   - Vencedor destacado;
4. Aluno navega pela timeline completa do jogo.

### Fluxo Alternativo 4: Visualizar Partida Agendada
1. Aluno acessa partida com status SCHEDULED;
2. Sistema **não** conecta ao WebSocket;
3. Sistema exibe informações:
   - Times que jogarão;
   - Data/horário agendado (se definido);
   - Fase/grupo da partida;
   - Modalidade;
4. Aluno pode receber notificação quando partida iniciar.

### Fluxo Alternativo 5: Perda de Conexão WebSocket
1. Aluno está visualizando partida ao vivo;
2. Conexão WebSocket cai (problema de rede);
3. Sistema detecta desconexão;
4. Sistema exibe indicador visual "Reconectando...";
5. Sistema tenta reconectar automaticamente;
6. **Se reconexão bem-sucedida:**
   - Sistema sincroniza estado atual do servidor;
   - Sistema atualiza placar/cronômetro para estado correto;
   - Sistema remove indicador e volta ao normal;
7. **Se reconexão falhar:**
   - Sistema exibe mensagem "Sem conexão. Toque para recarregar";
   - Aluno toca e sistema recarrega dados.

### Fluxo Alternativo 6: Sair da Tela de Partida
1. Aluno está visualizando detalhes de partida;
2. Aluno navega para outra tela;
3. Sistema desconecta do WebSocket da partida automaticamente;
4. Conexão é liberada para economizar recursos.

## 5. Bloco de Dados

### Bloco de Dados 1 – Feed de Jogos (Lista)

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Modalidade               | S             | Nome da modalidade                                    |
| Fase/Grupo               | S             | Qual fase ou grupo                                    |
| Time 1                   | S             | Nome e logo                                           |
| Time 2                   | S             | Nome e logo                                           |
| Placar                   | S             | Placar atual (se IN_PROGRESS) ou final (se FINISHED)  |
| Status                   | S             | SCHEDULED, IN_PROGRESS, FINISHED                      |
| Indicador Ao Vivo        | S             | Badge/ícone "AO VIVO" se IN_PROGRESS                  |
| Cronômetro               | S             | Tempo atual (se IN_PROGRESS)                          |
| Data/Horário             | S             | Quando será jogado (se SCHEDULED)                     |

### Bloco de Dados 2 – Detalhes da Partida

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Informações Gerais       | S             | Modalidade, fase, categoria, data/hora                |
| Time 1                   | S             | Nome, logo, placar                                    |
| Time 2                   | S             | Nome, logo, placar                                    |
| Cronômetro               | S             | Tempo atual e período (se IN_PROGRESS)                |
| Timeline de Eventos      | S             | Lista ordenada de todos os eventos                    |
| Estatísticas             | S             | Artilheiros, cartões, etc (se disponível)             |
| Vencedor                 | S             | Time vencedor destacado (se FINISHED)                 |

### Bloco de Dados 3 – Evento na Timeline

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Tipo                     | S             | Gol, cartão, período, etc                             |
| Time                     | S             | Time relacionado ao evento                            |
| Jogador                  | S             | Jogador envolvido (se aplicável)                      |
| Tempo                    | S             | Minuto em que ocorreu                                 |
| Ícone                    | S             | Ícone visual do tipo de evento                        |
| Descrição                | S             | Texto descritivo (ex: "Gol de João Silva")            |

### Bloco de Dados 4 – Eventos WebSocket

| Evento                   | Dados                                          | Descrição                                             |
|--------------------------|------------------------------------------------|-------------------------------------------------------|
| match_started            | match_id, teams                                | Partida iniciou                                       |
| score_update             | match_id, team1_score, team2_score             | Placar atualizado                                     |
| goal_scored              | team, player, clock, new_score                 | Gol/ponto marcado                                     |
| card_issued              | card_type, player, team                        | Cartão aplicado                                       |
| player_expelled          | player, reason                                 | Jogador expulso                                       |
| clock_update             | seconds, period, running                       | Cronômetro atualizado                                 |
| period_ended             | period                                         | Período encerrado                                     |
| period_started           | period                                         | Novo período iniciado                                 |
| set_finished             | set_number, score, winner                      | Set finalizado (vôlei)                                |
| match_finished           | match_id, final_score, winner                  | Partida finalizada                                    |
| event_deleted            | event_id, updated_score                        | Evento corrigido/deletado                             |

### Bloco de Dados 5 – Push Notification

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Título                   | S             | Ex: "⚽ Gol do Time A!"                                |
| Corpo                    | S             | Ex: "João Silva marcou aos 15'32. Placar: 3x1"       |
| Deep Link                | S             | Link direto para detalhes da partida                  |
| Ícone                    | S             | Ícone do tipo de evento                               |

## 6. Regras de Negócio

### Conexão WebSocket:
1. Sistema conecta automaticamente ao WebSocket ao entrar em telas de partidas;
2. **Feed de jogos:** Conecta ao canal da temporada (`/seasons/{season_id}/live`);
3. **Detalhes de partida:** Conecta ao canal da partida (`/matches/{match_id}/live`);
4. Sistema desconecta automaticamente ao sair da tela;
5. Apenas **uma conexão ativa** por tela (não acumula conexões);
6. Sistema tenta reconectar automaticamente em caso de perda de conexão;
7. Conexão WebSocket **não é usada** para partidas FINISHED ou SCHEDULED.

### Atualizações em Tempo Real:
8. Placar atualiza **instantaneamente** ao receber evento via WebSocket;
9. Cronômetro atualiza automaticamente (pode ser a cada segundo ou sob demanda);
10. Timeline de eventos atualiza **instantaneamente**;
11. Sistema exibe animações visuais para eventos importantes (gol, cartão);
12. Sistema mantém interface responsiva mesmo com múltiplas atualizações.

### Push Notifications:
13. Push enviado para eventos importantes:
    - Início de partida
    - Gol/ponto marcado
    - Cartão vermelho/expulsão
    - Fim de partida
14. Aluno recebe Push **mesmo com app fechado**;
15. Clicar em Push abre app diretamente na partida;
16. Push contém informações contextuais (time, jogador, placar).

### Sincronização:
17. Ao reconectar WebSocket, sistema sincroniza estado atual do servidor;
18. Sistema atualiza placar/cronômetro para valores corretos após reconexão;
19. Sistema carrega eventos perdidos durante desconexão;
20. Sincronização deve ser transparente para o aluno.

### Performance:
21. Sistema otimiza consumo de dados em conexões móveis;
22. Sistema permite visualizar partidas sem conexão (dados em cache) - V2;
23. WebSocket envia updates eficientes (apenas deltas, não estado completo);
24. Sistema libera conexões ao sair das telas.

## 7. Critérios de Aceitação
- O sistema deve conectar ao WebSocket automaticamente ao entrar nas telas;
- O sistema deve desconectar ao sair das telas;
- O sistema deve atualizar placar instantaneamente via WebSocket;
- O sistema deve atualizar timeline de eventos instantaneamente;
- O sistema deve atualizar cronômetro automaticamente;
- O sistema deve exibir indicador "AO VIVO" para partidas IN_PROGRESS;
- O sistema deve reconectar automaticamente em caso de perda de conexão;
- O sistema deve sincronizar estado após reconexão;
- O sistema deve enviar Push Notifications para eventos importantes;
- O sistema deve abrir app na partida ao clicar em Push;
- O sistema deve exibir mensagens claras sobre estado da conexão;
- O sistema deve funcionar para múltiplas partidas simultâneas no feed;
- O sistema deve exibir animações visuais para eventos importantes;
- O sistema não deve conectar WebSocket para partidas FINISHED/SCHEDULED.

## 8. Pós-condições

### Feed de Jogos:
- Aluno conectado ao canal da temporada;
- Recebe updates de todas as partidas ao vivo;
- Visualiza placares atualizados em tempo real.

### Detalhes da Partida:
- Aluno conectado ao canal da partida específica;
- Recebe updates detalhados (timeline, placar, cronômetro);
- Visualiza eventos instantaneamente conforme ocorrem.

### Ao Sair:
- Conexão WebSocket desconectada;
- Recursos liberados;
- Push Notifications continuam funcionando.

## 9. Cenários de Teste

| Cenário                                    | Dado                                           | Quando                              | Então                                                    |
|--------------------------------------------|------------------------------------------------|-------------------------------------|----------------------------------------------------------|
| Conectar ao feed de jogos                  | Aluno acessa aba "Jogos"                       | Tela carrega                        | Sistema conecta ao canal da temporada via WebSocket      |
| Visualizar partida ao vivo                 | Partida IN_PROGRESS no feed                    | Visualiza placar                    | Sistema exibe placar atualizado e indicador "AO VIVO"    |
| Receber atualização de gol                 | Gol marcado durante visualização               | WebSocket envia goal_scored         | Sistema atualiza placar instantaneamente e anima         |
| Atualizar cronômetro                       | Partida ao vivo                                | Cronômetro rodando                  | Sistema atualiza tempo automaticamente                   |
| Acessar detalhes de partida                | Clica em partida no feed                       | Tela de detalhes carrega            | Sistema conecta ao canal da partida específica           |
| Visualizar timeline de eventos             | Detalhes de partida ao vivo                    | Visualiza timeline                  | Sistema exibe todos os eventos ordenados cronologicamente|
| Receber evento na timeline                 | Cartão aplicado durante visualização           | WebSocket envia card_issued         | Sistema adiciona evento à timeline instantaneamente      |
| Receber Push Notification                  | Gol marcado, app fechado                       | Sistema envia Push                  | Aluno recebe notificação no dispositivo                  |
| Abrir app via Push                         | Clica em Push de gol                           | Tela abre                           | App abre diretamente na partida específica               |
| Visualizar partida finalizada              | Acessa partida FINISHED                        | Tela carrega                        | Sistema exibe dados estáticos, sem WebSocket             |
| Visualizar partida agendada                | Acessa partida SCHEDULED                       | Tela carrega                        | Sistema exibe info de agendamento, sem WebSocket         |
| Perda de conexão WebSocket                 | Partida ao vivo, rede cai                      | Conexão perdida                     | Sistema exibe "Reconectando..." e tenta reconectar       |
| Reconexão bem-sucedida                     | Sistema reconecta após perda                   | Conexão restabelecida               | Sistema sincroniza estado e volta ao normal              |
| Reconexão falha                            | Tentativas de reconexão falham                 | Timeout esgotado                    | Sistema exibe "Sem conexão. Toque para recarregar"       |
| Sair da tela de partida                    | Aluno volta ao feed                            | Navega para trás                    | Sistema desconecta do canal da partida                   |
| Múltiplas partidas simultâneas             | Feed com 3 partidas IN_PROGRESS                | Visualiza feed                      | Sistema atualiza placares de todas simultaneamente       |
| Evento deletado (correção)                 | Monitor deleta gol via UC017                   | WebSocket envia event_deleted       | Sistema remove evento da timeline e atualiza placar      |
| Cronômetro pausado                         | Monitor pausa cronômetro                       | WebSocket envia clock_update        | Sistema exibe cronômetro pausado                         |
| Período encerrado                          | Monitor finaliza período                       | WebSocket envia period_ended        | Sistema exibe "Intervalo" ou "Fim do 1º tempo"           |
| Animação de gol                            | Gol marcado durante visualização               | WebSocket recebe goal_scored        | Sistema exibe animação visual (ex: balão, confete)       |

## 10. Artefatos Relacionados
- [UC013 - Iniciar Partida](UC013_IniciarPartida.md)
- [UC014 - Registrar Eventos Durante Partida](UC014_RegistrarEventos.md)
- [UC015 - Finalizar Partida](UC015_FinalizarPartida.md)
- [UC017 - Corrigir Eventos da Partida](UC017_CorrigirEventos.md)