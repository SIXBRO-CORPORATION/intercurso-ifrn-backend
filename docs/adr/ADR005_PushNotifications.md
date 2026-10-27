# ADR 0005: Push Notifications via FCM e Módulo `messaging`

## Status
Aceita. Implementação faseada — esta primeira fase cobre apenas domínio, persistência e migration
do token de dispositivo (ver seção "Escopo desta fase").

## Contexto

O [UC016 - Visualizar Partida em Tempo Real](../spec/UC016_InterfaceUsuário_VisualizarPartida.md)
define, no **Fluxo Alternativo 2** e no **Bloco de Dados 5**, que um Aluno autenticado com token de
dispositivo registrado deve receber Push Notification quando ocorre um evento importante (gol,
cartão vermelho, início/fim de partida), mesmo com o aplicativo fechado — a notificação leva a um
deep link que abre o app direto na tela de detalhes da partida. A regra de acesso (seção "Acesso",
item 2) é explícita: push **exige** ator autenticado como Aluno com token de dispositivo
registrado; visitantes não recebem push, por depender de identidade.

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

### 3. Estratégia de envio (a ser detalhada quando a Fase 3 chegar)

Registrado aqui como direção, não como decisão fechada nesta fase: envio inline best-effort
(`asyncio.create_task` a partir do ponto em `match_controller.py` que já publica no broadcaster SSE
do ADR 0003), usando `send_each_for_multicast` do FCM, sem fila/broker dedicado — mesmo raciocínio
do ADR 0003 (volume baixo, trade-off documentado, não complexidade antecipada). Token que o FCM
reporta como inválido (`UNREGISTERED`) é desativado (`active=False`) no mesmo modelo de soft-delete
já usado nas demais entidades. Esta estratégia será confirmada/revisada quando as fases de
`core/messaging` e do hook no controller forem implementadas.

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

Um usuário pode ter mais de um token ativo (múltiplos dispositivos); o envio futuro faz multicast
para todos os tokens ativos do usuário.

## Escopo desta fase

Este ADR formaliza a decisão completa, mas o patch que o acompanha implementa **apenas**:
- `domain/enums/device_platform.py` e `domain/messaging/device_token.py`
- `persistence/model/messaging/device_token_entity.py` (tabela `device_tokens`)
- `persistence/mappers/messaging/device_token_mapper.py`
- `core/persistence/messaging/device_token_repository_port.py` e o adapter correspondente
- Migration Alembic (`v20`) criando a tabela

Ficam para fases seguintes, nesta ordem: `core/messaging` (port) + `messaging/adapters`
(FCM) + `messaging/config.py`; casos de uso de registro/remoção de token
(`core/business/messaging`); endpoints REST (`POST`/`DELETE
/api/messaging/device-token`); o hook de disparo em `match_controller.py`; e as mudanças no app
React Native (permissão, SDK, registro de token, deep link). Nenhuma dessas camadas é referenciada
por esta fase — por isso não há wiring de injeção de dependência ainda: o port de persistência só
passa a ser consumido quando o caso de uso de registro existir.

## Consequências

**Positivas**
- Um único provedor (FCM) cobre as duas plataformas do app React Native, sem duplicar integração.
- `messaging` como módulo guarda-chuva evita re-arquitetar quando e-mail (ou outro canal de
  mensageria) for necessário — a decisão de nomenclatura já antecipa isso.
- `active` reaproveitado evita uma segunda flag de "token válido" conceitualmente redundante com o
  soft-delete que todas as outras entidades já usam.

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

## Referências
- [UC016 - Visualizar Partida em Tempo Real](../spec/UC016_InterfaceUsuário_VisualizarPartida.md)
  — Fluxo Alternativo 2, Bloco de Dados 5, seção "Acesso".
- [ADR 0003 - Transporte de Tempo Real via SSE](ADR003_EnvioDeEventos.md) — seção 5, que registrou
  esta pendência.
- `docs/ai/planejamento.md` (Fase 6 — Push Notifications).
