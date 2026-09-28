# ADR 0004: Modelo de Acesso — Leitura Pública, Ação Autenticada

## Status
Aceita.

## Contexto

O modelo de produto para o aplicativo é: **qualquer pessoa pode abrir o app e acompanhar o
Intercurso sem fazer login**; a autenticação só é exigida quando a pessoa tenta executar uma ação
que depende de identidade ou de permissão (criar equipe, denunciar, gerenciar partidas etc.).

Esse modelo não estava escrito em nenhum documento do projeto, e o código o implementava apenas
pela metade. O tema surgiu na revisão geral do repositório: `GET /api/match/{match_id}` responde
sem autenticação e devolve `matricula` dos jogadores. Ao discutir se isso era falha do código ou da
documentação, ficou claro que a pergunta correta era "qual é o modelo de acesso do produto?", e que
ele nunca havia sido decidido por escrito.

### Como estava documentado antes desta decisão

| Documento | O que dizia sobre acesso |
|---|---|
| UC016 — Visualizar Partida | Pré-condição: "O ator deve estar autenticado como **Aluno**". Era o único UC de visualização, e dizia o oposto do modelo esperado. |
| UC001–UC004, UC009–UC015, UC017 | Pré-condição: autenticado com permissão de **Monitor**. |
| UC005–UC008, UC018 | Pré-condição: autenticado como **Aluno**. |
| UC018 — Criar Reporte | "Anônimo" refere-se apenas à identidade do denunciante **para os monitores** (`reporter_id = NULL`). O denunciante continua precisando estar autenticado como Aluno. |
| ADR003 — Envio de Eventos | Não trata de quem pode ler. Reaproveita `GET /api/match/{id}` como endpoint de reconciliação após reconexão. Não menciona o ticket de conexão. |
| README e planejamento | Nenhuma menção a modelo de acesso ou a navegação sem login. |

Divergência adicional do UC016 relevante para este tema: o UC descrevia WebSocket em
`/seasons/{id}/live` e `/matches/{id}/live`; o ADR003 trocou o transporte para SSE e os caminhos
reais são `/api/season/{id}/live` e `/api/match/{id}/live`.

### Como está no código hoje

**Rotas de leitura (`GET`)**

| Rota | Proteção atual |
|---|---|
| `GET /api/match/{id}` | **Nenhuma** (pública) |
| `GET /api/match/{id}/live` (SSE) | Ticket obrigatório (`?ticket=`) |
| `GET /api/season/{id}/live` (SSE) | Ticket obrigatório (`?ticket=`) |
| `GET /api/season/active` | Usuário autenticado |
| `GET /api/season/` e `GET /api/season/{id}` | Monitor |
| `GET /api/team/`, `GET /api/team/{id}`, `GET /api/team/invite/{token}` | Usuário autenticado |
| `GET /api/bracket/preview` | Monitor |
| `GET /api/auth/me` | Usuário autenticado |
| `GET /api/auth/login/suap`, `GET /api/auth/callback` | Públicas (fluxo de login) |

As rotas de escrita (`POST`/`PUT`/`PATCH`/`DELETE`) não são afetadas por esta decisão.

**Ticket de tempo real**
- Emitido por `POST /api/realtime/ticket`, que hoje exige `require_authenticated_user`.
- É um JWT de 30 segundos com `sub = user_id` (UUID obrigatório), escopo e canal.
- Existe porque o `EventSource` do navegador não envia headers de autenticação.
- O canal de temporada tem um defeito à parte (retorna 500 na emissão do ticket), registrado em
  issue própria.

**Outros fatos relevantes**
- `GET /api/match/{id}` usa `MatchManagementResponse`, schema de gestão, que inclui `matricula`
  dos jogadores.
- Não há `GET` público de lista de partidas de uma temporada, de classificação de grupo ou de
  chaveamento. Fora do preview de monitor, o acompanhamento depende do feed SSE.
- Já existe a dependência `get_optional_current_user` (hoje usada apenas em `auth_controller`), que
  permite rotas com usuário opcional.

### Inconsistências que motivaram esta decisão

1. **Documentação × produto:** o UC016 exigia Aluno autenticado; o produto espera visitante.
2. **Público pela metade:** um visitante conseguia o snapshot (`GET /api/match/{id}`), mas não
   recebia atualizações ao vivo, porque o ticket exige login.
3. **Ponto de entrada bloqueado:** `GET /api/season/active` exige login, então o app não consegue
   nem descobrir a temporada ativa sem autenticar.
4. **Lacuna de leitura:** não há endpoints públicos de lista de partidas, classificação e
   chaveamento.
5. **Dado pessoal em endpoint público:** `matricula` é exposta a qualquer pessoa. Isso é problema
   independente de a rota ser pública ou não.
6. **Ticket acoplado a usuário:** o `sub` é um UUID de usuário, o que impede ticket anônimo sem
   alteração.

## Decisão

**Regra geral: leitura pública, ação autenticada.**

### Matriz de acesso

| Capacidade | Visitante | Aluno | Monitor |
|---|:-:|:-:|:-:|
| Ver temporada ativa | ✔ | ✔ | ✔ |
| Ver partidas (lista, placar, cronômetro, eventos) | ✔ | ✔ | ✔ |
| Ver classificação e chaveamento | ✔ | ✔ | ✔ |
| Feed ao vivo (SSE de temporada e de partida) | ✔ | ✔ | ✔ |
| Ver nome de jogadores/times em partidas | ✔ | ✔ | ✔ |
| Ver matrícula de jogadores | ✘ | ✘ | Somente em telas de gestão |
| Ver equipes inscritas (nome, modalidade) | ✔ | ✔ | ✔ |
| Detalhe de equipe com membros e convites | ✘ | Somente a própria equipe | ✔ |
| Criar/gerir equipe, aceitar convite, submeter | ✘ | ✔ | ✔ |
| Denunciar (UC018) | ✘ | ✔ | — |
| Receber push notification | ✘ | ✔ | ✔ |
| Gestão de temporada, modalidade, chaveamento, partida, correção | ✘ | ✘ | ✔ |

Em resumo, por ator:

- **Visitante:** temporada ativa, partidas, placar, eventos, classificação, chaveamento e os feeds
  ao vivo — sem login.
- **Aluno:** tudo que o Visitante vê, mais criar e gerenciar equipe, aceitar convite, denunciar
  (UC018) e receber push — recursos que dependem de identidade.
- **Monitor:** tudo que já está nos UCs de gestão (UC001–UC004, UC009–UC015, UC017).

### Princípios

1. **Endpoint público usa schema público.** Rotas de visitante nunca reutilizam schemas de gestão.
   Devolvem somente o necessário para acompanhar o jogo — nome do jogador é exibido, mas
   **matrícula nunca**, nem e-mail ou outros identificadores de usuário além do estritamente
   necessário.
2. **Ticket SSE aceita visitante.** Com leitura pública, o ticket deixa de provar identidade e
   passa a ser uma admissão curta, com escopo de canal, que também valida a existência do canal.
   Mudança mínima: `POST /api/realtime/ticket` passa a usar `get_optional_current_user`, e o
   `sub` é o UUID do usuário ou um marcador `anonymous`. A emissão anônima tem limite de taxa
   por IP.
3. **Login sob demanda.** Ações protegidas continuam respondendo 401/403. O cliente dispara o login
   nesse momento e retoma a ação, sem exigir autenticação na abertura do app.
4. **Push exige identidade.** Notificações dependem de um usuário e de um token de dispositivo, por
   isso são o único recurso do UC016 que permanece restrito a autenticados.
5. **Campos públicos de equipe** ficam limitados a nome e modalidade; qualquer campo novo em
   schema público é revisado como dado exposto a qualquer pessoa antes de ser adicionado.

## Consequências

**Positivas**
- Documentação, código e produto passam a falar do mesmo modelo.
- Elimina a barreira de login para o caso de uso principal (acompanhar jogos).
- Endpoints públicos podem ser cacheados, aliviando o banco em dia de jogo.
- Remove a exposição de matrícula.

**Riscos e custos**
- O broadcaster é em memória, por processo. Conexões SSE anônimas abrem espaço para abuso; é
  necessário limite de conexões (por IP e por canal) antes de abrir a emissão anônima do ticket.
- Rotas públicas são alvo de scraping; exigem paginação e limites de taxa.
- Qualquer campo novo em schemas públicos passa a ser visível a todos e deve ser revisado como tal.

## Alterações necessárias

### Documentação
- [x] UC016: pré-condição de visualização removida (nenhuma; Aluno apenas para push); atores
      ajustados; WebSocket trocado por SSE; caminhos corrigidos para
      `/api/season/{id}/live` e `/api/match/{id}/live`.
- [ ] ADR003: nota sobre autenticação de leitura e sobre o ticket (referenciando este ADR).
- [ ] README: seção "Modelo de acesso" com a matriz acima.
- [ ] Planejamento: registrar as tarefas de código abaixo.

### Código (sugestão de PRs independentes)
1. Corrigir o 500 do ticket de temporada (issue já aberta).
2. Criar schema público de partida (sem `matricula`) e usá-lo em `GET /api/match/{id}`.
3. Ticket anônimo: `get_optional_current_user` na emissão, `sub` opcional em `verify_ticket`,
   limite de taxa por IP.
4. Limite de conexões SSE por IP e por canal.
5. `GET /api/season/active` público.
6. Endpoints públicos de lista de partidas da temporada, classificação e chaveamento, com schemas
   públicos e paginação.
7. Testes: visitante recebe SSE; resposta pública não contém `matricula`; rotas de escrita seguem
   retornando 401 sem token.

## Referências
- [UC016 — Visualizar Partida](../spec/UC016_InterfaceUsuário_VisualizarPartida.md)
- [UC018 — Criar Reporte](../spec/UC018_GestãoDeReportes_CriarReporte.md)
- [ADR 0003 — Envio de Eventos](ADR003_EnvioDeEventos.md)
