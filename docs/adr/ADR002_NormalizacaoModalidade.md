# ADR 0002: Normalização de Configuração por Modalidade e Histórico de Sets

## Status
Proposta (ainda não implementada — aguardando priorização de migrations)

## Contexto

O [UC014 - Registrar Evento](../spec/UC014_GestãoDePartidas_RegistrarEvento.md) prevê, para o
vôlei, que o sistema mantenha a pontuação do set atual, o histórico de sets já disputados e a
contagem de sets vencidos por time (Bloco de Dados 5, RN9-10 e RN34-40), além de uma configuração
por modalidade de quantos pontos valem um set e quantos sets são necessários para vencer a
partida.

Na implementação atual (ver `business/match/end_set_adapter.py` e `domain/modality_configuration.py`)
esses dados foram temporariamente armazenados em dois campos `Any`/JSON já existentes no domínio:

- `ModalityConfiguration.metadata`: chaves livres `points_per_set`, `final_set_points`,
  `sets_to_win`.
- `Match.metadata_json`: chaves livres `current_set_score`, `current_set_number`, `sets` (lista de
  objetos com `set_number`/`score`/`winner_team_id`) e `sets_won`.

Essa escolha resolveu a entrega do UC014 sem exigir migration nova, mas tem custos reais que
ficaram mais claros depois da implementação:

1. **Sem schema, sem FK, sem constraint.** Não há garantia de que `winner_team_id` dentro de
   `metadata_json.sets` seja um time válido da partida, nem que `set_number` não se repita.
2. **Não é consultável.** Uma pergunta simples como "quantos sets o time X venceu na temporada"
   exige carregar e parsear o JSON de cada partida em código de aplicação; não dá para expressar
   isso como uma query SQL direta.
3. **Risco de *lost update* por concorrência.** Cada fim de set faz um *read-modify-write* do
   blob `metadata_json` inteiro (lê o dict, modifica, grava de volta). Duas requisições
   concorrentes na mesma partida (pouco provável, mas possível — ex.: duplo clique, retry de
   rede) podem se sobrescrever sem nenhum mecanismo de lock otimista ou constraint impedindo.
4. **Placar duplicado com semânticas diferentes.** `Match.team1_score`/`team2_score` (RN9: sempre
   incrementado a cada ponto) e `metadata_json.current_set_score` (resetado a cada fim de set)
   representam "placar" de duas formas incompatíveis para o vôlei: o primeiro vira um contador de
   pontos corridos da partida inteira (sem significado visual direto), enquanto o placar que
   importa (o do set atual) fica escondido dentro do JSON.
5. **`ModalityConfiguration.metadata` como `Any` genérico não escala.** Cada nova modalidade com
   configuração própria (ex.: handebol com posse de bola, basquete com faltas por período)
   acumularia mais chaves livres no mesmo campo, sem nenhuma forma de validação ou de saber, só
   olhando o schema do banco, quais campos pertencem a qual modalidade.

Nenhum desses pontos é levantado pela especificação de negócio (ela intencionalmente não define
"como" persistir isso) — são decisões de modelagem de dados que precisam ser tomadas à parte,
assim como o [ADR 0001](ADR001_Cronometro.md) fez para o cronômetro.

## Decisão

Substituir os dois campos JSON por um modelo normalizado, seguindo o padrão *Class Table
Inheritance*: uma tabela de configuração/dados específicos por modalidade, associada 1:1 à tabela
genérica já existente, em vez de colunas `NULL`-áveis genéricas ou de um blob JSON.

### 1. Configuração específica do vôlei

```
volleyball_modality_configuration
  id                          PK
  modality_configuration_id   FK -> modality_configuration.id (UNIQUE)
  points_per_set               INT NOT NULL DEFAULT 25
  final_set_points              INT NOT NULL DEFAULT 15
  sets_to_win                   INT NOT NULL DEFAULT 2
```

`ModalityConfiguration` (genérica) continua guardando o que já é comum a todas as modalidades
(`score_type`, etc.); modalidades com necessidades próprias ganham sua própria tabela satélite,
sempre 1:1 com `modality_configuration`. O mesmo padrão se replica no futuro para outras
modalidades que precisem de configuração específica (ex.: uma eventual
`handball_modality_configuration`), sem inflar a tabela genérica nem misturar campos de
modalidades diferentes na mesma linha.

### 2. Histórico de sets

```
match_set
  id                PK
  match_id          FK -> match.id
  set_number        INT NOT NULL
  team1_points       INT NOT NULL
  team2_points       INT NOT NULL
  winner_team_id     FK -> team.id
  UNIQUE (match_id, set_number)
```

Cada set finalizado vira uma linha nova (`INSERT`), não uma reescrita de blob. A constraint
`UNIQUE (match_id, set_number)` impede duplicar o mesmo set e torna qualquer *race condition*
visível como erro de constraint no banco, em vez de causar um *lost update* silencioso.

### 3. Placar do set atual e contagem de sets vencidos

Para resolver a duplicidade de semântica de placar (ponto 4 do Contexto), a decisão de semântica
é: **para modalidades com `score_type = SETS`, `team1_score`/`team2_score` (em `Match`) passam a
representar o placar do set atual** (resetado para `0x0` a cada fim de set, RN38), no mesmo estilo
que já é usado para gols/pontos em outras modalidades — em vez de introduzir um terceiro conceito
de "placar do set" isolado.

Já a contagem de sets vencidos por time é **estado de uma partida específica**, não configuração:
nasce zerada a cada `Match` novo e muda a cada `SET_END`. Por isso ela **não** entra em
`volleyball_modality_configuration` — essa tabela é 1:1 com `modality_configuration` (compartilhada
por todas as partidas daquele chaveamento/modalidade) e colocar ali um contador que muda por
partida quebraria essa cardinalidade (deixaria de ser "configuração" e passaria a exigir uma linha
por partida, o que descaracteriza a tabela).

Isso deixa duas opções válidas para onde guardar a contagem, com um trade-off entre pureza e
performance de leitura:

- **(a) Derivar sempre a partir de `match_set`:** `SELECT winner_team_id, COUNT(*) FROM match_set
  WHERE match_id = :match_id GROUP BY winner_team_id`. É a opção mais normalizada — não existe
  contador para dessincronizar do histórico, porque não existe contador.
- **(b) Cache em `Match`** (`team1_sets_won`/`team2_sets_won INT NULL`), atualizado no mesmo
  `save()` que insere a linha em `match_set` no fim de cada set:

  ```
  Match
    ...
    team1_sets_won   INT NULL   -- cache; fonte da verdade é match_set (opção b)
    team2_sets_won   INT NULL
  ```

**Decisão: opção (b)**, por consistência com o padrão que o projeto já usa para `team1_score`/
`team2_score` (contadores cacheados em `Match`, não derivados de `COUNT(*) FROM match_event` a
cada leitura). Manter os dois padrões diferentes (placar derivado por agregação vs. placar
cacheado) no mesmo domínio seria mais inconsistente do que o ganho teórico teria valor aqui, dado
o volume de dados do sistema. Fica registrado que (a) é a alternativa "mais pura" caso o cache
venha a causar bugs de dessincronia na prática.

### 4. `Match.metadata_json` e `ModalityConfiguration.metadata`

Os dois campos genéricos continuam existindo no domínio (não há motivo para removê-los — servem
de extensão futura sem migration), mas deixam de ser usados para o que passa a ter tabela própria.
Uso de metadata continua legítimo apenas para payloads de auditoria por evento individual
(`MatchEvent.metadata_json`), que é heterogêneo por natureza (cada tipo de evento tem campos
diferentes) e não sofre dos mesmos problemas de concorrência (é sempre um `INSERT` novo, nunca um
*read-modify-write*).

### 5. Fluxo de criação e leitura das tabelas

O desenho acima só é completo se ficar claro **quem escreve** em cada tabela e **em que
momento**, e **de onde** cada leitura busca o dado. Isso não estava explícito na primeira versão
deste ADR.

**Momento 1 — Criação/edição da configuração de modalidade (UC004 - Cadastrar Modalidade, fora do
escopo do UC014/deste ADR, mas com dependência direta nele):**
- Quando `ModalityConfiguration.score_type = SETS` é definido, o fluxo de criação da modalidade
  precisa, na mesma operação, criar a linha correspondente em `volleyball_modality_configuration`
  (com os valores informados pelo gestor, ou os defaults `25`/`15`/`2` se ele não informar nada).
  Isso é responsabilidade do adapter que hoje cria `ModalityConfiguration`
  (`business/modality/create_modality_adapter.py`) — quando esse ADR for implementado, esse
  adapter passa a criar as duas linhas na mesma transação, não apenas a genérica.
- Isso implica uma decisão de UC004 que este ADR não decide sozinho: se `score_type = SETS`
  **exige** essa configuração no momento da criação (validação obrigatória) ou se pode ficar
  ausente e cair em defaults até alguém preencher depois. Fica registrado aqui como pendência a
  resolver quando o UC004 for revisitado — não é decisão que este ADR, focado em UC014, deva
  tomar sozinho.

**Momento 2 — Leitura durante a partida (UC014, `EndSetAdapter`/`RegisterGoalAdapter`):**
- Caminho de leitura: `match.bracket_id → Bracket.modality_id → ModalityConfiguration
  (find_by_modality) → volleyball_modality_configuration (find_by_modality_configuration_id)`.
  É o mesmo caminho que `business/match/_shared.load_modality_configuration` já percorre hoje até
  `ModalityConfiguration`; a única mudança é o passo adicional até a tabela satélite quando
  `score_type = SETS`.
- **Se a linha em `volleyball_modality_configuration` não existir** (modalidade configurada como
  `SETS` mas sem a configuração específica preenchida — cenário que só deveria ocorrer se o UC004
  permitir o campo ausente, ver Momento 1): mantém o mesmo comportamento defensivo que o código
  atual já tem (`config_metadata.get("points_per_set", DEFAULT_POINTS_PER_SET)`), ou seja, cai
  nos defaults `25`/`15`/`2` em vez de falhar a operação. Isso deve ficar explícito como
  comportamento esperado (não um bug) quando implementado.

**Momento 3 — Início da partida (UC013):** nenhuma inicialização nova é necessária. Uma partida
nova simplesmente ainda não tem linhas em `match_set`, e `team1_sets_won`/`team2_sets_won` nascem
`NULL`/`0`.

**Momento 4 — Fim de um set (UC014, `EndSetAdapter`):** um único `INSERT` em `match_set` +
`UPDATE` em `Match` (reset de `team1_score`/`team2_score` para `0x0`, incremento do cache
`team1_sets_won`/`team2_sets_won`), na mesma transação.

**Momento 5 — Correção pós-jogo (UC017 - Corrigir Evento, RN28):** ao editar/excluir um evento
`SET_END` (ou um `GOAL`/`POINT` que afete o placar do set em andamento), o fluxo de correção
precisa:
1. Ajustar ou remover a linha correspondente em `match_set` (se o próprio fim de set foi
   revertido);
2. Recalcular `team1_sets_won`/`team2_sets_won` — seja via `COUNT(*)` em `match_set` no momento da
   correção (mais simples e sempre correto, já que é uma operação pouco frequente e não precisa
   do "cache" de leitura rápida), seja decrementando manualmente. Recomendo `COUNT(*)` aqui
   especificamente, mesmo tendo decidido pelo cache na leitura normal (Momento 2), porque
   correção é um caminho raro onde correção-por-recontagem é mais segura que
   incrementar/decrementar contadores à mão;
3. Recalcular `team1_score`/`team2_score` (placar do set atual) a partir dos eventos
   `GOAL`/`POINT` restantes após o ponto de correção — mesma lógica que RN25/RN27 já preveem para
   modalidades sem sets, aplicada ao set em andamento.

Este ADR não decide os detalhes de implementação do UC017 (fora de escopo), só deixa registrado
que esse fluxo de recontagem precisa existir quando o UC017 for implementado sobre este modelo.

## Consequências

**Positivas**
- Consultas diretas em SQL para relatórios (sets vencidos por time na temporada, histórico de
  sets de uma partida) sem precisar parsear JSON em código de aplicação.
- Constraint `UNIQUE (match_id, set_number)` elimina o risco de *lost update* que existe hoje no
  `read-modify-write` do blob.
- Cada modalidade com necessidade própria ganha uma tabela satélite dedicada, sem inflar
  `modality_configuration` com colunas `NULL` que só fazem sentido para uma modalidade.
- Placar do set atual (`team1_score`/`team2_score`) e contagem de sets (`team1_sets_won`/
  `team2_sets_won`) deixam de ter dois "placares" concorrentes com semânticas diferentes.

**Negativas / trade-offs**
- Exige migrations novas (criação de `volleyball_modality_configuration` e `match_set`, adição de
  `team1_sets_won`/`team2_sets_won` em `match`) e um script de *backfill* para qualquer partida de
  vôlei já em andamento com dados em `metadata_json` no momento do deploy — janela que precisa ser
  planejada (ex.: aplicar em horário sem partidas de vôlei ativas, ou migration que já converte o
  JSON existente para as novas tabelas).
- Um join a mais (`modality_configuration` → `volleyball_modality_configuration`) para ler a
  configuração do vôlei, contra uma leitura direta de `metadata` hoje. Custo desprezível dado o
  volume de dados do sistema, mas é uma trade-off real de simplicidade de código por
  consultabilidade dos dados.
- Cada nova modalidade com necessidade de configuração própria exige uma migration/tabela nova
  (o que é, ao mesmo tempo, a vantagem de normalizar: fica explícito e validado no schema, mas é
  mais trabalho do que adicionar uma chave num JSON).

## Alternativas consideradas

1. **Manter `metadata`/`metadata_json` como estão hoje.** Rejeitada como solução definitiva pelos
   motivos do Contexto (sem FK/constraint, não consultável, risco de *lost update*), embora tenha
   sido aceitável como solução temporária para viabilizar a entrega do UC014 sem bloquear em
   migrations.
2. **Colunas `NULL`-áveis direto em `ModalityConfiguration`** (ex.: `points_per_set INT NULL`,
   `final_set_points INT NULL`, `sets_to_win INT NULL`). Rejeitada: cada modalidade nova acumula
   mais colunas que só fazem sentido para ela, tornando o schema cada vez mais esparso e difícil
   de entender sem ler código (qual campo pertence a qual modalidade).
3. **Tabela genérica única de "configuração específica" com um discriminador de tipo** (ex.:
   `modality_specific_config(modality_configuration_id, key, value)`, tipo *EAV*). Rejeitada:
   reintroduz os mesmos problemas do JSON (sem tipagem forte por campo, sem validação) só que
   espalhado em mais linhas, sem ganhar as vantagens reais da normalização.

## Referências
- [UC014 - Registrar Evento Durante Partida](../spec/UC014_GestãoDePartidas_RegistrarEvento.md)
- [UC017 - Corrigir Eventos da Partida](../spec/UC017_GestãoDePartidas_CorrigirEvento.md)
- [ADR 0001 - Estratégia do Cronômetro da Partida](ADR001_Cronometro.md)
- `domain/match.py`, `domain/modality_configuration.py`, `business/match/end_set_adapter.py`
  (implementação atual, baseada em `metadata`/`metadata_json`, que este ADR propõe substituir)
- `business/modality/create_modality_adapter.py` (ponto de escrita da nova tabela satélite no
  Momento 1 do fluxo acima)
