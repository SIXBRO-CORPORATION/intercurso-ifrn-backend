# ADR 0005: Push Notifications via FCM e Módulo `messaging`

## Status
Aceita. Implementação faseada (ver seção "Escopo desta fase" para o que já foi entregue).

> **Revisão (decisão de produto:** a leitura original deste ADR — herdada
> literalmente do UC016 — tratava push como um mecanismo único, sempre dirigido a um Aluno
> autenticado com token registrado. O produto decidiu que eventos de partida (gol, cartão,
> início/fim) são **broadcast público**: todo mundo com o app instalado deve receber, autenticado
> ou não, no mesmo espírito do ADR 0004 (leitura de partida já é pública). Isso não invalida o que
> foi construído nas fases anteriores — `device_tokens` e o registro/remoção por usuário continuam
> existindo e exigindo autenticação —, mas eles passam a servir só ao canal **pessoal/dirigido**
> (ex.: "seu time foi aprovado"), não ao broadcast de eventos de partida. Ver seção 5.

## Contexto

O [UC016 - Visualizar Partida em Tempo Real](../spec/UC016_InterfaceUsuário_VisualizarPartida.md)
define, no **Fluxo Alternativo 2** e no **Bloco de Dados 5**, que um Aluno autenticado com token de
dispositivo registrado deve receber Push Notification quando ocorre um evento importante (gol,
cartão vermelho, início/fim de partida), mesmo com o aplicativo fechado — a notificação leva a um
deep link que abre o app direto na tela de detalhes da partida. A regra de acesso (seção "Acesso",
item 2) do próprio UC016 é explícita: push **exige** ator autenticado como Aluno com token de
dispositivo registrado; visitantes não recebem push, por depender de identidade.

**Essa restrição foi revisada** (ver nota de revisão acima): o produto quer que eventos de partida
alcancem qualquer pessoa com o app aberto, visitante incluso — a notificação nesse caso carrega
informação pública da competição (o mesmo placar que já é visível sem login via SSE, ADR 0004), não
dado pessoal. A exigência de autenticação continua valendo, mas só para o canal pessoal/dirigido
(ex.: um aviso que só faz sentido para quem tem conta), que é o cenário que a regra do UC016
realmente protegia.

O [ADR 0003](ADR003_EnvioDeEventos.md), que decidiu o transporte de tempo real (SSE), já deixou
essa pendência registrada em sua seção 5: *"Push Notification é um mecanismo independente ... a
integração com provedor de push é uma decisão separada, já registrada como pendência na Fase 6 do
planejamento."* O [planejamento](../ai/planejamento.md) (Fase 6) descreve a pendência como
"definir provedor (FCM/APNs) e camada de integração ... depende de registro de token de
dispositivo". Este ADR resolve essa decisão, no mesmo espírito dos ADRs 0001-0004: decidir **como**
antes de implementar.

Duas perguntas precisam ser respondidas: (1) qual provedor de push, dado que o app é React Native
e precisa cobrir Android e iOS; e (2) como estruturar o código, já que `core/notifications/`
(mencionado no planejamento) seria um módulo só para push, mas a aplicação eventualmente também
vai precisar enviar e-mail (confirmação de cadastro, aviso de temporada, etc.) — outro mecanismo de
"mensageria" com a mesma forma (compor uma mensagem, decidir destinatários, entregar via um
provedor externo, tratar falha de entrega).

## Decisão

### 1. Provedor único: Firebase Cloud Messaging (FCM)

FCM é adotado como único provedor de push, para Android **e** iOS. FCM entrega para APNs por trás
quando a credencial APNs do projeto está configurada no console do Firebase — não é necessário
integrar diretamente com APNs no backend. Isso evita manter dois clients de provedor (FCM para
Android, APNs direto para iOS) fazendo o mesmo trabalho conceitual, e casa com o SDK do app:
`@react-native-firebase/messaging` cobre as duas plataformas com a mesma API no cliente.

**Alternativa rejeitada:** integração direta com APNs (via HTTP/2 + chave `.p8`) em paralelo ao
FCM para Android. Rejeitada porque duplicaria a camada de integração (dois clients, dois formatos
de payload, dois tratamentos de erro) sem ganho funcional sobre o UC016 — a espec não distingue
comportamento de push por plataforma.

### 2. Módulo `messaging`, não `notifications`

O planejamento menciona `core/notifications/`, mas a decisão aqui é nomear o módulo **`messaging`**
— mais amplo que só push. Segue o padrão arquitetural já usado por `security/` e `storage/`
(módulo técnico de borda, com `config.py` de settings próprias e `adapters/` para integrações
externas, fora da árvore `domain`/`core`/`business`):

- `core/persistence/messaging/` — ports que dependem só de domínio (ex.: o repositório de device
  token desta fase).
- `core/messaging/` *(fase futura)* — ports de envio desacoplados do provedor (`PushSenderPort`,
  e futuramente `EmailSenderPort`), análogo ao `FileStoragePort` de `storage/`.
- `messaging/adapters/` *(fase futura)* — implementações concretas (`FCMPushSenderAdapter` agora;
  um `EmailSenderAdapter` depois, quando a aplicação precisar — ex.: SMTP ou provedor transacional).
- `messaging/config.py` *(fase futura)* — settings (`pydantic_settings`) com credencial de serviço
  do Firebase e, depois, credenciais de e-mail.
- `domain/messaging/` e `persistence/{model,mappers,adapters}/messaging/` — modelagem e persistência
  de dados do domínio de mensageria (token de dispositivo nesta fase).

Push e e-mail compartilham a mesma forma de problema (compor conteúdo, resolver destinatário,
chamar um provedor externo, tratar falha sem derrubar o fluxo principal), então cabem como duas
implementações dentro do mesmo módulo técnico, em vez de dois módulos de borda paralelos
(`notifications/` e, mais tarde, um hipotético `email/`).

### 3. Estratégia de envio: inline, best-effort, sem fila

Confirmado para os dois canais da seção 5: envio inline best-effort (`asyncio.create_task` a partir
do ponto em `match_controller.py` que já publica no broadcaster SSE do ADR 0003), sem fila/broker
dedicado — mesmo raciocínio do ADR 0003 (volume baixo, trade-off documentado, não complexidade
antecipada). No canal dirigido, token que o FCM reporta como inválido (`UNREGISTERED`) é desativado
(`active=False`) no mesmo modelo de soft-delete já usado nas demais entidades; no canal de
broadcast não existe essa noção, porque não há token individual rastreado pelo backend (ver seção
5). O hook de disparo no controller é a próxima fase a ser implementada.

### 4. Persistência do token de dispositivo (escopo desta fase)

Tabela `device_tokens`, uma linha por par (usuário, token físico do FCM):

| Campo | Tipo | Observação |
|---|---|---|
| `user_id` | UUID, FK `users.id` (`CASCADE`) | dono do token |
| `token` | String(500), único | token do FCM; pode mudar (reinstalação, `onTokenRefresh`) |
| `platform` | String(10) | `ANDROID` / `IOS`, mesmo padrão de `role`/`gender` em `UserEntity` |
| `last_used_at` | DateTime, opcional | preenchido pelo caso de uso de registro/uso (fase futura) |
| `id`, `created_at`, `modified_at`, `deleted_at`, `active` | — | colunas padrão de `AbstractEntity` |

`active=False` cobre dois casos com o mesmo campo, sem coluna extra: opt-out do usuário (logout) e
invalidação pelo provedor (token expirado/app desinstalado) — mesma convenção de soft-delete já
usada em todas as outras entidades do projeto.

Um usuário pode ter mais de um token ativo (múltiplos dispositivos); o envio dirigido faz multicast
para todos os tokens ativos do usuário.

### 5. Dois canais de envio: broadcast por tópico vs. dirigido por token

O `messaging` passa a resolver dois problemas de distribuição diferentes, não um só:

| | Broadcast (eventos de partida) | Dirigido (notificação pessoal) |
|---|---|---|
| Exemplo | Gol, cartão, início/fim de partida (UC016) | "Seu time foi aprovado", "você foi escalado" |
| Audiência | Todo mundo com o app instalado | Um usuário (ou lista de usuários) específico |
| Exige autenticação? | Não | Sim |
| Mecanismo FCM | **Topic** (`messaging.Message(topic=...)`) | **Multicast** (`send_each_for_multicast`, seção 4) |
| Inscrição | App assina o tópico no cliente (`subscribeToTopic`), sem depender de login | Backend registra `device_tokens` por usuário (seções 2 e 4, já implementado) |
| Rastreamento no backend | Nenhum — o FCM sabe quem está inscrito, o backend só manda pro nome do tópico | Tabela `device_tokens`, uma linha por token ativo |

Na prática: `PushSenderPort` (`core/messaging/`, seção 2) ganha um segundo método ao lado do
`send` por lista de tokens já decidido — algo como `send_to_topic(topic, title, body, data)` —, e o
`FCMPushSenderAdapter` implementa os dois usando o mesmo client do Firebase Admin SDK (`messaging.
Message(topic=...)` em vez de `MulticastMessage`). Não é um provedor novo nem uma credencial nova,
só um segundo formato de mensagem do mesmo SDK.

O hook em `match_controller.py` (próxima fase) usa exclusivamente o canal de broadcast — ele não
precisa consultar `device_tokens` nem saber quem está com o app aberto, só mandar uma mensagem pro
tópico (ex.: `live_matches`, ou um por temporada/partida se a granularidade de silenciar
notificações por partida específica vier a ser necessária — não decidido nesta fase, fica como
extensão futura). O mecanismo dirigido (`device_tokens` + multicast) fica reservado para casos de
uso pessoais que ainda não existem no sistema — não há, até este ADR, nenhum caso de uso que
dispare notificação pessoal; a infraestrutura (registro/remoção de token) foi construída
antecipando essa necessidade, mas nenhum disparo a consome ainda.

**Por que não usar o canal dirigido (multicast) também para broadcast:** funcionaria, mas exigiria
(a) todo usuário se autenticar e registrar um token só para receber informação pública de partida —
o produto decidiu explicitamente que isso não deve ser uma barreira — e (b) o backend buscar todos
os tokens ativos do banco e multicast em lotes a cada evento, um custo que cresce com o número de
usuários; o Topic resolve a entrega inteiramente do lado do FCM, sem esse fan-out no backend.

## Escopo desta fase

Este ADR formaliza a decisão completa; o que já foi implementado, nesta ordem:
- `domain/enums/device_platform.py` e `domain/messaging/device_token.py`
- `persistence/model/messaging/device_token_entity.py` (tabela `device_tokens`) + migration (`v20`)
- `persistence/mappers/messaging/device_token_mapper.py`
- `core/persistence/messaging/device_token_repository_port.py` e o adapter correspondente
- `core/messaging/push_sender_port.py` (canal dirigido, `send` por lista de tokens) +
  `messaging/adapters/fcm_push_sender_adapter.py` + `messaging/configuration/config.py`
  (credencial do Firebase via variável de ambiente)
- Casos de uso de registro/remoção de token (`core/business/messaging`,
  `business/messaging/{register,remove}_device_token_adapter.py`) e `notification_controller.py`
  (`POST`/`DELETE /api/messaging/device-token`), autenticados

Ficam para fases seguintes: `send_to_topic` no `PushSenderPort`/`FCMPushSenderAdapter` (seção 5); o
hook de disparo em `match_controller.py` (broadcast por tópico, inline best-effort, seção 3); a
inscrição do app no tópico via `@react-native-firebase/messaging` (sem exigir login); e, quando
houver o primeiro caso de uso pessoal real, o disparo via canal dirigido reaproveitando o que já
existe em `device_tokens`.

## Consequências

**Positivas**
- Um único provedor (FCM) cobre as duas plataformas do app React Native, sem duplicar integração.
- `messaging` como módulo guarda-chuva evita re-arquitetar quando e-mail (ou outro canal de
  mensageria) for necessário — a decisão de nomenclatura já antecipa isso.
- `active` reaproveitado evita uma segunda flag de "token válido" conceitualmente redundante com o
  soft-delete que todas as outras entidades já usam.
- O canal de broadcast por tópico (seção 5) elimina o fan-out de multicast para toda a base de
  usuários a cada evento de partida — o custo de distribuição fica inteiramente do lado do FCM, e
  cresce o mesmo independente de quantos usuários o app tiver.
- Separar os dois canais evita que o mecanismo pensado para notificação pessoal (`device_tokens`,
  exige login) vire acidentalmente um bloqueio para o requisito de produto de alcançar visitantes.

**Negativas / trade-offs**
- Dependência de uma credencial externa (Firebase service account) que precisa ser provisionada e
  mantida fora do repositório (variável de ambiente/secret), assim como já ocorre com as credenciais
  do R2 em `storage/config.py`.
- FCM como único provedor cria uma dependência de infraestrutura do Google mesmo para o caminho
  iOS; aceito porque simplifica a integração do backend e é a prática comum em apps React Native
  (via `@react-native-firebase`).
- Multicast sem fila (ponto 3) herda o mesmo trade-off do broadcaster em memória do ADR 0003: não
  sobrevive a múltiplas instâncias sem reconsideração futura. Será revisitado quando a fase de
  envio for implementada, não nesta fase de persistência.
- Inscrição em tópico é um estado que só o FCM conhece: o backend não tem como listar quem está
  inscrito em `live_matches`, nem forçar a desinscrição de um dispositivo específico a partir do
  servidor — a única forma de "remover" um dispositivo do broadcast é o próprio app chamar
  `unsubscribeFromTopic` no cliente. Para o caso de uso (notificação pública, sem necessidade de
  revogação individual) isso é aceitável; não seria se o broadcast precisasse de audiência
  controlada por usuário.
- Dois mecanismos de entrega (tópico e token) significam dois caminhos de teste e de observabilidade
  (taxa de entrega de tópico não é reportada pelo FCM com o mesmo detalhe que `send_each_for_
  multicast` retorna por token) — aceito porque os dois problemas realmente são diferentes, não é
  complexidade acidental.

## Alternativas consideradas

1. **FCM + APNs direto em paralelo.** Rejeitada (ver seção 1) — duplicaria integração sem ganho
   funcional para o UC016.
2. **Módulo `notifications/`, como o planejamento sugeria.** Rejeitada em favor de `messaging/`:
   nomear pelo mecanismo mais específico (push) fecha a porta para reaproveitar a mesma estrutura
   quando e-mail (ou outro canal) for necessário; `messaging` descreve a categoria do problema
   (entregar uma mensagem a alguém via um provedor externo), não um canal específico.
3. **Campo `is_valid`/`revoked` dedicado no token, em vez de reaproveitar `active`.** Rejeitada:
   `RefreshToken` (ADR de autenticação) já tem um campo `revoked` próprio porque sua semântica de
   negócio é diferente de soft-delete (um refresh token revogado continua existindo como registro
   de auditoria, com motivo). Device token não tem esse requisito — reaproveitar `active` é
   suficiente e evita introduzir uma segunda noção de "desativado" para o mesmo conceito.
4. **Multicast para todos os tokens ativos, sem distinguir broadcast de dirigido (ver seção 5).**
   Rejeitada após decisão de produto: exigiria login de todo usuário só para receber informação
   pública de partida, e o custo de fan-out no backend cresce com a base de usuários a cada evento.
   Avaliada e descartada a favor de FCM Topics para o caso de broadcast, mantendo multicast só para
   o que de fato é pessoal.
5. **Dois provedores/módulos separados para broadcast e dirigido (ex.: um `topics/` paralelo a
   `messaging/`).** Rejeitada: os dois usam o mesmo SDK do Firebase Admin e a mesma credencial —
   seriam dois métodos do mesmo `PushSenderPort`/`FCMPushSenderAdapter`, não dois módulos; separar
   em módulos distintos duplicaria configuração e client sem ganho de coesão.

## Referências
- [UC016 - Visualizar Partida em Tempo Real](../spec/UC016_InterfaceUsuário_VisualizarPartida.md)
  — Fluxo Alternativo 2, Bloco de Dados 5, seção "Acesso" (restrição de autenticação revisada para
  o canal de broadcast, ver nota de revisão no topo deste documento).
- [ADR 0003 - Transporte de Tempo Real via SSE](ADR003_EnvioDeEventos.md) — seção 5, que registrou
  esta pendência.
- [ADR 0004 - Modelo de Acesso](ADR004_ModeloDeAcesso.md) — precedente de leitura pública sem
  autenticação, mesmo raciocínio aplicado aqui ao canal de broadcast.
- `docs/ai/planejamento.md` (Fase 6 — Push Notifications).
