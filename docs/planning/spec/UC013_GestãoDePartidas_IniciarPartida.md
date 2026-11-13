# Especificação de Caso de Uso: Iniciar Partida

## 1. Descrição
Este caso de uso permite que o monitor inicie uma partida agendada, acessando a interface de gerenciamento em tempo real onde poderá registrar eventos, controlar o cronômetro e atualizar o placar durante o jogo.

## 2. Pré-condições
- O ator deve estar autenticado com permissão de **Monitor**;
- Deve existir uma partida com status **SCHEDULED**;
- Ambos os times da partida devem estar **APPROVED**;
- Monitor não deve estar gerenciando outra partida simultaneamente (apenas uma partida IN_PROGRESS por monitor).

## 3. Fluxo Principal: Iniciar Partida
1. O monitor acessa o módulo "Gerenciamento de Partidas";
2. O sistema exibe lista de partidas agendadas;
3. O monitor seleciona uma partida específica;
4. O monitor clica em "Iniciar Partida";
5. O sistema valida conforme Regras de Negócio;
6. O sistema carrega interface de gerenciamento da partida conforme Bloco de Dados 1;
7. O sistema exibe todos os componentes necessários (placar, jogadores, botões);
8. O monitor clica no botão "Play" (Início Real);
9. O sistema exibe modal: "Começar partida?";
10. O monitor confirma;
11. O sistema atualiza status para IN_PROGRESS;
12. O sistema define `started_at = now()`;
13. O sistema inicializa cronômetro: `clock_seconds = 0`, `clock_running = true`, `current_period = 1`;
14. O sistema cria evento MATCH_START;
15. O sistema envia notificação via WebSocket para canal da partida e temporada;
16. O sistema envia Push Notification para alunos;
17. O cronômetro começa a contar.

## 4. Fluxos Alternativos

### Fluxo Alternativo 1: Partida Não Está em SCHEDULED
1. O monitor tenta iniciar partida que não está em SCHEDULED;
2. O sistema bloqueia a operação e exibe mensagem de erro;
3. O sistema informa o status atual da partida.

### Fluxo Alternativo 2: Times Não Aprovados
1. O monitor tenta iniciar partida com times não aprovados;
2. O sistema bloqueia a operação e exibe mensagem de erro;
3. O sistema informa quais times não estão aprovados.

### Fluxo Alternativo 3: Monitor Já Gerenciando Outra Partida
1. O monitor tenta iniciar nova partida enquanto gerencia outra;
2. O sistema bloqueia a operação e exibe mensagem de erro;
3. O sistema informa qual partida está em andamento.

### Fluxo Alternativo 4: Cancelar Início Antes do Play
1. Monitor clica em "Iniciar Partida" e acessa interface;
2. Monitor decide não iniciar e sai da tela;
3. Sistema mantém partida em SCHEDULED sem alterações.

### Fluxo Alternativo 5: Cancelar Modal de Confirmação
1. Monitor clica em "Play" e modal aparece;
2. Monitor clica em "Cancelar";
3. Sistema fecha modal e mantém partida aguardando;
4. Monitor pode clicar em "Play" novamente quando quiser.

## 5. Bloco de Dados

### Bloco de Dados 1 – Interface de Gerenciamento

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Informações da Partida   | S             | Modalidade, fase, categoria (GROUP/KNOCKOUT)          |
| Time 1                   | S             | Nome, logo, placar inicial (0)                        |
| Time 2                   | S             | Nome, logo, placar inicial (0)                        |
| Lista de Jogadores Time 1| S             | Todos os jogadores do time (clicáveis)                |
| Lista de Jogadores Time 2| S             | Todos os jogadores do time (clicáveis)                |
| Placar                   | S             | Exibição do placar (0 x 0 inicialmente)               |
| Cronômetro               | S             | Tempo inicial (00:00), período atual (1)              |
| Configuração Modalidade  | S             | Períodos, duração por período, sistema de pontuação   |
| Botões de Ação           | S             | Play, pausar, fim de período, finalizar, etc          |
| Timeline de Eventos      | S             | Lista vazia inicialmente                              |

### Bloco de Dados 2 – Partida Iniciada

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Status                   | S             | Atualizado de SCHEDULED para IN_PROGRESS              |
| Data de Início           | S             | Timestamp automático do início real                   |
| Cronômetro Segundos      | S             | Inicia em 0                                           |
| Cronômetro Rodando       | S             | true (rodando)                                        |
| Período Atual            | S             | 1 (primeiro período)                                  |
| Placar Time 1            | S             | 0                                                     |
| Placar Time 2            | S             | 0                                                     |

### Bloco de Dados 3 – Evento de Início

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Tipo de Evento           | S             | MATCH_START                                           |
| Timestamp                | S             | Momento exato do início                               |
| Monitor Responsável      | S             | ID do monitor que iniciou                             |

## 6. Regras de Negócio
1. Apenas **monitor** pode iniciar partida;
2. Partida deve estar em status **SCHEDULED**;
3. Ambos os times devem estar **APPROVED**;
4. Monitor pode gerenciar apenas **uma partida IN_PROGRESS por vez**;
5. Status muda para **IN_PROGRESS** apenas quando monitor clica "Play" no modal;
6. Antes do "Play", partida permanece em SCHEDULED (permite cancelamento);
7. Ao clicar "Play" e confirmar:
   - `started_at` é preenchido com timestamp atual
   - Cronômetro inicia em 0 segundos
   - `clock_running = true`
   - `current_period = 1`
   - Placares iniciam em 0
8. Sistema cria evento **MATCH_START** na timeline;
9. Sistema envia notificação via **WebSocket** para:
   - Canal da partida (`/matches/{match_id}/live`)
   - Canal da temporada (`/seasons/{season_id}/live`)
10. Sistema envia **Push Notification** para alunos;
11. Cronômetro atualiza automaticamente no backend a cada segundo;
12. Interface de gerenciamento carrega configurações da modalidade:
    - Número de períodos
    - Duração de cada período
    - Sistema de pontuação (gols, pontos, sets)
13. A operação deve ser registrada para auditoria;
14. Após início, monitor acessa funcionalidades de registrar eventos (UC014).

## 7. Critérios de Aceitação
- O sistema deve bloquear início se partida não estiver em SCHEDULED;
- O sistema deve bloquear início se times não estiverem APPROVED;
- O sistema deve bloquear início se monitor já gerencia outra partida;
- O sistema deve carregar interface de gerenciamento ao clicar "Iniciar";
- O sistema deve exibir modal de confirmação ao clicar "Play";
- O sistema deve mudar status para IN_PROGRESS apenas após confirmação;
- O sistema deve inicializar cronômetro em 0 e período em 1;
- O sistema deve criar evento MATCH_START;
- O sistema deve enviar notificações via WebSocket e Push;
- O sistema deve carregar configurações da modalidade;
- O sistema deve permitir cancelamento antes do "Play";
- O sistema deve exibir mensagens claras de sucesso ou erro;
- O sistema deve registrar a operação para auditoria.

## 8. Pós-condições
- Partida tem status atualizado para IN_PROGRESS;
- Data de início registrada (`started_at`);
- Cronômetro inicializado e rodando;
- Período atual definido como 1;
- Placares zerados;
- Evento MATCH_START criado;
- Notificações enviadas via WebSocket e Push;
- Monitor pode registrar eventos durante a partida;
- Operação registrada para auditoria.

## 9. Cenários de Teste

| Cenário                                    | Dado                                           | Quando                              | Então                                                    |
|--------------------------------------------|------------------------------------------------|-------------------------------------|----------------------------------------------------------|
| Início bem-sucedido                        | Partida SCHEDULED, times APPROVED              | Clica "Play" e confirma             | Sistema muda para IN_PROGRESS e inicia cronômetro        |
| Partida não SCHEDULED                      | Partida com status IN_PROGRESS                 | Tenta iniciar                       | Sistema bloqueia e exibe erro                            |
| Times não aprovados                        | Partida com time PENDING_APPROVAL              | Tenta iniciar                       | Sistema bloqueia e lista times pendentes                 |
| Monitor com partida em andamento           | Monitor já gerencia outra partida              | Tenta iniciar nova                  | Sistema bloqueia e informa partida atual                 |
| Cancelar antes do Play                     | Interface carregada, sem clicar Play           | Sai da tela                         | Sistema mantém partida em SCHEDULED                      |
| Cancelar modal de confirmação              | Modal "Começar partida?" aberto                | Clica "Cancelar"                    | Sistema fecha modal sem iniciar                          |
| Cronômetro inicializado                    | Partida iniciada com sucesso                   | Verifica cronômetro                 | Sistema exibe 00:00 e começa a contar                    |
| Período inicial                            | Partida iniciada                               | Verifica período                    | Sistema define current_period = 1                        |
| Placares zerados                           | Partida iniciada                               | Verifica placares                   | Ambos times com 0 pontos                                 |
| Evento MATCH_START criado                  | Partida iniciada                               | Verifica timeline                   | Sistema registra evento de início                        |
| WebSocket notificado                       | Partida iniciada                               | Verifica conexões WebSocket         | Sistema envia match_started para canais                  |
| Push Notification enviado                  | Partida iniciada                               | Verifica notificações               | Alunos recebem notificação de início                     |
| Configuração da modalidade carregada       | Partida de Futsal iniciada                     | Verifica interface                  | Sistema exibe 2 períodos de 20min                        |
| Timestamp de início registrado             | Partida iniciada                               | Verifica `started_at`               | Sistema registra data/hora exata do Play                 |
| Auditoria de início                        | Partida iniciada                               | Verifica logs                       | Sistema registra monitor, partida e data/hora            |

## 10. Artefatos Relacionados
- [UC011 - Criar Chaveamento](UC011_CriarChaveamento.md)
- [UC012 - Gerenciar Chaveamento](UC012_GerenciarChaveamento.md)
- [UC014 - Registrar Eventos Durante Partida](UC014_RegistrarEventos.md)
- [UC015 - Finalizar Partida](UC015_FinalizarPartida.md)
- [UC016 - Visualizar Partida em Tempo Real](UC016_VisualizarPartida.md)