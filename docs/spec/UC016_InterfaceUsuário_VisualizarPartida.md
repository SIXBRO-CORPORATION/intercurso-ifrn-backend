# Especificação de Caso de Uso: Visualizar Partida em Tempo Real

## 1. Descrição
Este caso de uso permite que **qualquer pessoa**, autenticada ou não, acompanhe partidas em tempo
real — placar, eventos (gols, cartões, expulsões) e cronômetro — através de conexão SSE
(Server-Sent Events). Apenas o recebimento de **Push Notification** exige que o ator esteja
autenticado como **Aluno**, por depender de identidade e de um token de dispositivo associado a
uma conta.

> Modelo de acesso definido em [ADR 0004 — Modelo de Acesso](../adr/ADR004_ModeloDeAcesso.md):
> leitura pública, ação autenticada.

## 2. Pré-condições
- Para **visualizar** (feed, detalhes, feed ao vivo): nenhuma. O ator pode ser **Visitante**,
  **Aluno** ou **Monitor**;
- Para **receber Push Notification**: o ator deve estar autenticado como **Aluno** e possuir um
  token de dispositivo registrado;
- Deve existir ao menos uma partida com status **IN_PROGRESS**, **SCHEDULED** ou **FINISHED**.

## 3. Fluxo Principal: Visualizar Feed de Jogos ao Vivo
1. O ator (visitante, aluno ou monitor) acessa a aba "Jogos" do aplicativo;
2. O sistema solicita um ticket de admissão de curta duração em
   `POST /api/realtime/ticket` — a emissão aceita usuário autenticado ou anônimo
   (`get_optional_current_user`); emissões anônimas têm limite de taxa por IP;
3. O sistema conecta ao canal SSE da temporada (`GET /api/season/{season_id}/live?ticket=...`);
4. O sistema exibe lista de partidas da temporada conforme Bloco de Dados 1;
5. Para partidas **IN_PROGRESS:**
   - Sistema exibe placar atualizado em tempo real;
   - Sistema exibe cronômetro atualizado;
   - Sistema exibe indicador visual "AO VIVO";
6. O ator visualiza updates de todas as partidas simultaneamente;
7. Ao receber evento via SSE:
   - Sistema atualiza placar instantaneamente;
   - Sistema exibe animação de notificação (gol/cartão);
   - Sistema atualiza cronômetro automaticamente;
8. O ator permanece na tela recebendo updates contínuos.

## 4. Fluxos Alternativos

### Fluxo Alternativo 1: Visualizar Detalhes de Partida Específica
1. O ator está no feed de jogos;
2. O ator clica em uma partida específica;
3. Sistema desconecta do canal SSE da temporada;
4. Sistema solicita novo ticket de admissão e conecta ao canal SSE da partida
   (`GET /api/match/{match_id}/live?ticket=...`);
5. Sistema exibe detalhes completos conforme Bloco de Dados 2;
6. O ator recebe updates detalhados:
   - Timeline completa de eventos (gols, cartões, períodos);
   - Placar atualizado em tempo real;
   - Cronômetro atualizado a cada segundo;
   - Estatísticas da partida (se disponível);
7. Ao receber evento via SSE:
   - Sistema adiciona evento à timeline instantaneamente;
   - Sistema atualiza placar;
   - Sistema exibe notificação visual do evento;
8. O ator pode voltar ao feed clicando "Voltar";
9. Sistema desconecta do canal da partida e reconecta ao da temporada.

### Fluxo Alternativo 2: Receber Push Notification (exclusivo do Aluno)
1. Aluno autenticado, com token de dispositivo registrado, não está com aplicativo aberto;
2. Evento importante ocorre (gol, cartão vermelho, início/fim de partida);
3. Sistema backend envia Push Notification ao dispositivo;
4. Aluno recebe notificação no dispositivo;
5. Aluno clica na notificação;
6. Sistema abre aplicativo diretamente na tela de detalhes da partida;
7. Sistema solicita ticket e conecta ao canal SSE da partida;
8. Aluno visualiza detalhes atualizados.

> Visitantes não recebem Push, pois o recurso depende de identidade (usuário) e de um token de
> dispositivo vinculado a uma conta.

### Fluxo Alternativo 3: Visualizar Partida Finalizada
1. O ator acessa partida com status FINISHED;
2. Sistema **não** conecta ao canal SSE;
3. Sistema exibe informações estáticas:
   - Placar final;
   - Timeline completa de eventos;
   - Estatísticas finais;
   - Vencedor destacado;
4. O ator navega pela timeline completa do jogo.

### Fluxo Alternativo 4: Visualizar Partida Agendada
1. O ator acessa partida com status SCHEDULED;
2. Sistema **não** conecta ao canal SSE;
3. Sistema exibe informações:
   - Times que jogarão;
   - Data/horário agendado (se definido);
   - Fase/grupo da partida;
   - Modalidade;
4. O ator pode receber notificação quando a partida iniciar, caso seja Aluno autenticado com
   push habilitado.

### Fluxo Alternativo 5: Perda de Conexão SSE
1. O ator está visualizando partida ao vivo;
2. Conexão SSE cai (problema de rede);
3. Sistema detecta desconexão;
4. Sistema exibe indicador visual "Reconectando...";
5. Sistema solicita novo ticket de admissão e tenta reconectar automaticamente;
6. **Se reconexão bem-sucedida:**
   - Sistema sincroniza estado atual do servidor (`GET /api/match/{id}` com o schema público, sem
     `matricula`);
   - Sistema atualiza placar/cronômetro para estado correto;
   - Sistema remove indicador e volta ao normal;
7. **Se reconexão falhar:**
   - Sistema exibe mensagem "Sem conexão. Toque para recarregar";
   - O ator toca e sistema recarrega dados.

### Fluxo Alternativo 6: Sair da Tela de Partida
1. O ator está visualizando detalhes de partida;
2. O ator navega para outra tela;
3. Sistema desconecta do canal SSE da partida automaticamente;
4. Conexão é liberada para economizar recursos.

## 5. Bloco de Dados

### Bloco de Dados 1 – Feed de Jogos (Lista)

> Fonte: `GET /api/match/?season_id=...` (público, paginado). Filtros: `modality_id`, `status`,
> `date_from`, `date_to` (o cliente envia o intervalo no fuso local). `team1`/`team2` são `null`
> enquanto o time não está definido. Detalhes em
> [ADR 0004](../adr/ADR004_ModeloDeAcesso.md#estado-de-implementação).

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

> Nenhum campo deste bloco de dados inclui `matricula` ou qualquer outro identificador pessoal do
> jogador além do nome — ver Princípio 1 do ADR 0004.

### Bloco de Dados 3 – Evento na Timeline

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Tipo                     | S             | Gol, cartão, período, etc                             |
| Time                     | S             | Time relacionado ao evento                            |
| Jogador                  | S             | Nome do jogador envolvido (se aplicável); sem matrícula|
| Tempo                    | S             | Minuto em que ocorreu                                 |
| Ícone                    | S             | Ícone visual do tipo de evento                        |
| Descrição                | S             | Texto descritivo (ex: "Gol de João Silva")            |

### Bloco de Dados 4 – Eventos SSE

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

### Bloco de Dados 5 – Push Notification (exclusivo do Aluno)

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Título                   | S             | Ex: "⚽ Gol do Time A!"                                |
| Corpo                    | S             | Ex: "João Silva marcou aos 15'32. Placar: 3x1"       |
| Deep Link                | S             | Link direto para detalhes da partida                  |
| Ícone                    | S             | Ícone do tipo de evento                               |

## 6. Regras de Negócio

### Acesso:
1. A visualização de partidas (feed, detalhes, feed ao vivo) **não exige autenticação**;
2. O recebimento de Push Notification exige ator autenticado como **Aluno** com token de
   dispositivo registrado;
3. Endpoints de leitura usados por este UC devolvem schema público, sem `matricula`, e-mail ou
   qualquer identificador de usuário além do necessário para exibir o jogo.

### Conexão SSE e ticket de admissão:
4. Toda conexão SSE exige um ticket de admissão de curta duração, emitido por
   `POST /api/realtime/ticket`;
5. A emissão do ticket aceita usuário autenticado **ou anônimo** (`sub` = UUID do usuário ou
   marcador `anonymous`); emissões anônimas têm limite de taxa por IP;
6. O ticket prova apenas admissão a um canal específico por tempo curto — não prova identidade;
7. Sistema conecta automaticamente ao canal SSE ao entrar em telas de partidas;
8. **Feed de jogos:** Conecta ao canal da temporada (`/api/season/{season_id}/live`);
9. **Detalhes de partida:** Conecta ao canal da partida (`/api/match/{match_id}/live`);
10. Sistema desconecta automaticamente ao sair da tela;
11. Apenas **uma conexão ativa** por tela (não acumula conexões);
12. Sistema tenta reconectar automaticamente em caso de perda de conexão, solicitando novo ticket;
13. Conexão SSE **não é usada** para partidas FINISHED ou SCHEDULED;
14. Conexões SSE têm limite por IP e por canal, para conter abuso de conexões anônimas.

### Atualizações em Tempo Real:
15. Placar atualiza **instantaneamente** ao receber evento via SSE;
16. Cronômetro atualiza automaticamente (pode ser a cada segundo ou sob demanda);
17. Timeline de eventos atualiza **instantaneamente**;
18. Sistema exibe animações visuais para eventos importantes (gol, cartão);
19. Sistema mantém interface responsiva mesmo com múltiplas atualizações.

### Push Notifications:
20. Push enviado para eventos importantes:
    - Início de partida
    - Gol/ponto marcado
    - Cartão vermelho/expulsão
    - Fim de partida
21. Apenas Aluno autenticado com dispositivo registrado recebe Push, **mesmo com app fechado**;
22. Clicar em Push abre app diretamente na partida;
23. Push contém informações contextuais (time, jogador, placar).

### Sincronização:
24. Ao reconectar SSE, sistema sincroniza estado atual do servidor via `GET /api/match/{id}`
    (schema público);
25. Sistema atualiza placar/cronômetro para valores corretos após reconexão;
26. Sistema carrega eventos perdidos durante desconexão;
27. Sincronização deve ser transparente para o ator, autenticado ou não.

### Performance:
28. Sistema otimiza consumo de dados em conexões móveis;
29. Sistema permite visualizar partidas sem conexão (dados em cache) - V2;
30. SSE envia updates eficientes (apenas deltas, não estado completo);
31. Sistema libera conexões ao sair das telas;
32. Endpoints públicos de leitura devem suportar cache e paginação, por estarem sujeitos a maior
    volume de acesso e a scraping.

## 7. Critérios de Aceitação
- Um visitante não autenticado deve conseguir visualizar o feed de jogos, os detalhes de uma
  partida e receber updates ao vivo, sem realizar login;
- O sistema deve emitir ticket de admissão anônimo quando o ator não estiver autenticado,
  respeitando o limite de taxa por IP;
- Nenhuma resposta deste UC deve conter `matricula` de jogador;
- O sistema deve conectar ao canal SSE automaticamente ao entrar nas telas;
- O sistema deve desconectar ao sair das telas;
- O sistema deve atualizar placar instantaneamente via SSE;
- O sistema deve atualizar timeline de eventos instantaneamente;
- O sistema deve atualizar cronômetro automaticamente;
- O sistema deve exibir indicador "AO VIVO" para partidas IN_PROGRESS;
- O sistema deve reconectar automaticamente em caso de perda de conexão;
- O sistema deve sincronizar estado após reconexão;
- O sistema deve enviar Push Notifications apenas para Alunos autenticados com dispositivo
  registrado, para eventos importantes;
- O sistema deve abrir app na partida ao clicar em Push;
- O sistema deve exibir mensagens claras sobre estado da conexão;
- O sistema deve funcionar para múltiplas partidas simultâneas no feed;
- O sistema deve exibir animações visuais para eventos importantes;
- O sistema não deve conectar SSE para partidas FINISHED/SCHEDULED.

## 8. Pós-condições

### Feed de Jogos:
- Ator (visitante, aluno ou monitor) conectado ao canal da temporada;
- Recebe updates de todas as partidas ao vivo;
- Visualiza placares atualizados em tempo real.

### Detalhes da Partida:
- Ator conectado ao canal da partida específica;
- Recebe updates detalhados (timeline, placar, cronômetro);
- Visualiza eventos instantaneamente conforme ocorrem.

### Ao Sair:
- Conexão SSE desconectada;
- Recursos liberados;
- Push Notifications continuam funcionando para Alunos autenticados.

## 9. Cenários de Teste

| Cenário                                    | Dado                                           | Quando                              | Então                                                    |
|--------------------------------------------|------------------------------------------------|-------------------------------------|----------------------------------------------------------|
| Visitante conecta ao feed sem login        | Visitante não autenticado acessa aba "Jogos"   | Tela carrega                        | Sistema emite ticket anônimo e conecta ao canal SSE da temporada|
| Conectar ao feed de jogos                  | Ator acessa aba "Jogos"                        | Tela carrega                        | Sistema conecta ao canal da temporada via SSE            |
| Visualizar partida ao vivo                 | Partida IN_PROGRESS no feed                    | Visualiza placar                    | Sistema exibe placar atualizado e indicador "AO VIVO"    |
| Receber atualização de gol                 | Gol marcado durante visualização               | SSE envia goal_scored               | Sistema atualiza placar instantaneamente e anima         |
| Atualizar cronômetro                       | Partida ao vivo                                | Cronômetro rodando                  | Sistema atualiza tempo automaticamente                   |
| Acessar detalhes de partida                | Clica em partida no feed                       | Tela de detalhes carrega            | Sistema conecta ao canal da partida específica           |
| Resposta pública sem matrícula             | Visitante acessa `GET /api/match/{id}`         | Sistema responde                    | Payload não contém `matricula` de nenhum jogador         |
| Visualizar timeline de eventos             | Detalhes de partida ao vivo                    | Visualiza timeline                  | Sistema exibe todos os eventos ordenados cronologicamente|
| Receber evento na timeline                 | Cartão aplicado durante visualização           | SSE envia card_issued               | Sistema adiciona evento à timeline instantaneamente      |
| Receber Push Notification                  | Gol marcado, Aluno autenticado com app fechado | Sistema envia Push                  | Aluno recebe notificação no dispositivo                  |
| Visitante não recebe Push                  | Gol marcado, visitante sem conta               | Sistema avalia destinatários        | Sistema não envia Push (visitante não tem device token)  |
| Abrir app via Push                         | Clica em Push de gol                           | Tela abre                           | App abre diretamente na partida específica               |
| Visualizar partida finalizada              | Acessa partida FINISHED                        | Tela carrega                        | Sistema exibe dados estáticos, sem SSE                   |
| Visualizar partida agendada                | Acessa partida SCHEDULED                       | Tela carrega                        | Sistema exibe info de agendamento, sem SSE               |
| Perda de conexão SSE                       | Partida ao vivo, rede cai                      | Conexão perdida                     | Sistema exibe "Reconectando..." e tenta reconectar       |
| Reconexão bem-sucedida                     | Sistema reconecta após perda                   | Conexão restabelecida               | Sistema sincroniza estado e volta ao normal              |
| Reconexão falha                            | Tentativas de reconexão falham                 | Timeout esgotado                    | Sistema exibe "Sem conexão. Toque para recarregar"       |
| Sair da tela de partida                    | Ator volta ao feed                             | Navega para trás                    | Sistema desconecta do canal da partida                   |
| Múltiplas partidas simultâneas             | Feed com 3 partidas IN_PROGRESS                | Visualiza feed                      | Sistema atualiza placares de todas simultaneamente       |
| Evento deletado (correção)                 | Monitor deleta gol via UC017                   | SSE envia event_deleted             | Sistema remove evento da timeline e atualiza placar      |
| Cronômetro pausado                         | Monitor pausa cronômetro                       | SSE envia clock_update              | Sistema exibe cronômetro pausado                         |
| Período encerrado                          | Monitor finaliza período                       | SSE envia period_ended              | Sistema exibe "Intervalo" ou "Fim do 1º tempo"           |
| Animação de gol                            | Gol marcado durante visualização               | SSE recebe goal_scored              | Sistema exibe animação visual (ex: balão, confete)       |
| Ticket anônimo com taxa excedida           | Muitas emissões anônimas do mesmo IP           | Visitante solicita novo ticket      | Sistema recusa emissão por limite de taxa excedido       |

## 10. Artefatos Relacionados
- [ADR 0004 - Modelo de Acesso](../adr/ADR004_ModeloDeAcesso.md)
- [ADR 0003 - Envio de Eventos](../adr/ADR003_EnvioDeEventos.md)
- [UC013 - Iniciar Partida](UC013_IniciarPartida.md)
- [UC014 - Registrar Eventos Durante Partida](UC014_RegistrarEventos.md)
- [UC015 - Finalizar Partida](UC015_FinalizarPartida.md)
- [UC017 - Corrigir Eventos da Partida](UC017_CorrigirEventos.md)
