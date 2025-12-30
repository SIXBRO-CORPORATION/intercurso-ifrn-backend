# Especificação de Caso de Uso: Criar Chaveamento

## 1. Descrição
Este caso de uso permite que o monitor crie o chaveamento de uma modalidade após o encerramento do período de inscrições, definindo o formato da competição, realizando o sorteio dos times e gerando automaticamente todas as partidas do campeonato. A criação do chaveamento transiciona automaticamente a temporada para status IN_PROGRESS.

## 2. Pré-condições
- O ator deve estar autenticado com permissão de **Monitor**;
- Deve existir uma temporada ativa com status **REGISTRATION_CLOSED**;
- Período de inscrição deve ter encerrado;
- Deve existir ao menos uma modalidade com times aprovados (mínimo 2 times);
- Não deve existir chaveamento ativo para a modalidade selecionada.

## 3. Fluxo Principal: Criar Chaveamento
1. O monitor acessa o módulo "Gestão de Chaveamentos";
2. O sistema exibe lista de modalidades da temporada ativa;
3. O monitor seleciona uma modalidade;
4. O sistema exibe quantidade de times aprovados na modalidade;
5. O sistema exibe opções de formato conforme Bloco de Dados 1;
6. O monitor seleciona o formato desejado;
7. O sistema gera configuração sugerida baseada no número de times;
8. O monitor revisa a configuração e clica em "Sortear";
9. O sistema valida os dados conforme Regras de Negócio;
10. **O sistema atualiza temporada para IN_PROGRESS automaticamente (primeira vez)**;
11. O sistema cria o Bracket com status ACTIVE;
12. O sistema cria BracketGroups conforme formato escolhido;
13. O sistema sorteia times aleatoriamente e distribui nos grupos/chaves;
14. O sistema cria entrada "BYE" se número de times for ímpar;
15. O sistema cria todas as partidas com status SCHEDULED e times TBD nas fases avançadas;
16. O sistema marca partidas contra BYE como FINISHED automaticamente;
17. O sistema envia notificação aos alunos: "🏆 Chaveamento publicado!";
18. O sistema exibe mensagem de sucesso e apresenta o chaveamento gerado.

## 4. Fluxos Alternativos

### Fluxo Alternativo 1: Menos de 2 Times Aprovados
1. O monitor seleciona modalidade com menos de 2 times aprovados;
2. O sistema bloqueia a criação e exibe mensagem de erro;
3. O sistema informa quantidade mínima necessária.

### Fluxo Alternativo 2: Chaveamento Já Existe
1. O monitor tenta criar chaveamento para modalidade que já possui bracket ativo;
2. O sistema bloqueia a operação e exibe mensagem de erro;
3. O sistema informa que já existe chaveamento criado.

### Fluxo Alternativo 3: Ajustar Configuração Antes de Sortear
1. O monitor visualiza configuração sugerida pelo sistema;
2. O monitor ajusta parâmetros (número de grupos, times por grupo, etc);
3. O sistema valida nova configuração;
4. O monitor confirma e prossegue com sorteio.

### Fluxo Alternativo 4: Cancelar Criação
1. Monitor está na tela de configuração do chaveamento;
2. Monitor clica em "Cancelar";
3. Sistema descarta configurações e retorna à listagem de modalidades.

### Fluxo Alternativo 5: Temporada em Status Inválido
1. Monitor tenta criar chaveamento com temporada em REGISTRATION_OPEN;
2. Sistema bloqueia operação;
3. Sistema exibe erro: "Período de inscrições ainda está aberto. Aguarde o encerramento.";

### Fluxo Alternativo 6: Primeiro Chaveamento da Temporada
1. Monitor cria primeiro chaveamento da temporada;
2. Temporada está em REGISTRATION_CLOSED;
3. Sistema detecta que é o primeiro chaveamento;
4. Sistema exibe confirmação: "Criar chaveamento? Isso iniciará oficialmente a fase de jogos.";
5. Monitor confirma;
6. Sistema cria chaveamento E atualiza temporada para IN_PROGRESS;
7. Sistema envia notificação aos alunos.

### Fluxo Alternativo 7: Chaveamentos Subsequentes
1. Monitor cria chaveamento adicional (2ª, 3ª modalidade...);
2. Temporada já está em IN_PROGRESS;
3. Sistema cria chaveamento normalmente sem alterar status da temporada;
4. Sistema envia notificação apenas sobre o novo chaveamento.

## 5. Bloco de Dados

### Bloco de Dados 1 – Formatos de Competição

| Formato                  | Descrição                                      | Configurações                                    |
|--------------------------|------------------------------------------------|--------------------------------------------------|
| KNOCKOUT                 | Mata-mata (eliminação direta)                  | Número de rodadas, disputa de 3º lugar          |
| GROUP_STAGE_KNOCKOUT     | Fase de grupos + mata-mata                     | Grupos, times por grupo, classificados por grupo |
| ROUND_ROBIN              | Todos contra todos (pontos corridos)           | Número de turnos                                 |
| TRIANGULAR               | 3 times jogam entre si                         | Turno único ou ida e volta                       |

### Bloco de Dados 2 – Chaveamento Criado

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Modalidade               | E             | Modalidade selecionada                                |
| Formato                  | E             | Formato escolhido (KNOCKOUT, GROUP_STAGE_KNOCKOUT...) |
| Configuração             | E/S           | JSON com parâmetros do formato                        |
| Quantidade de Times      | S             | Total de times participantes (incluindo BYE se houver)|
| Status                   | S             | Sempre criado como ACTIVE                             |
| Grupos/Chaves            | S             | Lista de grupos criados (se aplicável)                |
| Partidas Criadas         | S             | Total de partidas geradas                             |
| BYE Criado               | S             | Se número ímpar, sistema criou placeholder BYE        |
| Data de Criação          | S             | Timestamp automático                                  |

### Bloco de Dados 3 – Partidas Geradas

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Time 1                   | S             | Time sorteado, TBD ou BYE                             |
| Time 2                   | S             | Time sorteado, TBD ou BYE                             |
| Grupo/Fase               | S             | A qual grupo ou fase pertence                         |
| Categoria                | S             | GROUP ou KNOCKOUT                                     |
| Status                   | S             | SCHEDULED (ou FINISHED se contra BYE)                 |
| Data Agendada            | S             | Null inicialmente (monitor define depois)             |

### Bloco de Dados 4 – Entry BYE (Times Ímpares)

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Nome                     | S             | "BYE" (placeholder do sistema)                        |
| É Placeholder            | S             | true (não é time real)                                |
| Partida Associada        | S             | Partida onde BYE foi sorteado                         |
| Vencedor Automático      | S             | Time que enfrentou BYE (vence por W.O.)               |

## 6. Regras de Negócio
1. Apenas **monitor** pode criar chaveamento;
2. Temporada deve estar em **REGISTRATION_CLOSED** ou **IN_PROGRESS**;
3. Período de inscrição deve ter encerrado;
4. Modalidade deve ter ao menos **2 times aprovados**;
5. Apenas um chaveamento ativo por modalidade/temporada;
6. Formato escolhido aplica-se a **todas as fases** da modalidade;
7. Sorteio é **totalmente aleatório** (sem cabeças de chave na V1);
8. Sistema cria **todas as partidas de todas as fases** de uma vez:
   - Primeira fase: com times definidos pelo sorteio
   - Fases seguintes: com times TBD (a serem determinados)
9. Partidas de mata-mata têm `match_category = KNOCKOUT`;
10. Partidas de grupos têm `match_category = GROUP`;
11. Sistema distribui times nos grupos de forma equilibrada;
12. **Times Ímpares - BYE Automático:**
    - Sistema cria automaticamente entrada "BYE" (placeholder) se número for ímpar;
    - BYE é sorteado como se fosse um time normal;
    - Time sorteado contra BYE vence automaticamente por W.O. (Walkover);
    - Sistema cria partida com status FINISHED e vencedor já definido;
    - Sistema avança time vencedor automaticamente para próxima fase;
    - BYE não existe nas fases seguintes (serviu apenas para equilibrar primeira rodada);
13. Chaveamento criado tem status **ACTIVE**;
14. **Transição de Status da Temporada:**
    - Se é o **primeiro chaveamento** criado E temporada está em REGISTRATION_CLOSED:
      - Sistema atualiza temporada para **IN_PROGRESS** automaticamente;
      - Sistema envia notificação aos alunos: "🏆 Fase de jogos iniciada!";
    - Se temporada já está em IN_PROGRESS (chaveamentos subsequentes):
      - Sistema apenas cria o chaveamento sem alterar status da temporada;
15. A operação deve ser registrada para auditoria.

## 7. Critérios de Aceitação
- O sistema deve bloquear criação se período de inscrição não encerrou;
- O sistema deve bloquear criação se modalidade tem menos de 2 times;
- O sistema deve bloquear criação se já existe chaveamento ativo;
- O sistema deve exibir opções de formato baseadas no número de times;
- O sistema deve permitir ajuste de configuração antes do sorteio;
- O sistema deve sortear times aleatoriamente;
- O sistema deve criar todas as partidas (primeira fase + fases seguintes TBD);
- O sistema deve criar BYE automaticamente para números ímpares;
- O sistema deve marcar partidas contra BYE como FINISHED com vencedor;
- O sistema deve definir `match_category` corretamente (GROUP/KNOCKOUT);
- O sistema deve criar chaveamento com status ACTIVE;
- O sistema deve atualizar temporada para IN_PROGRESS no primeiro chaveamento;
- O sistema deve enviar notificações aos alunos;
- O sistema deve exibir mensagens claras de sucesso ou erro;
- O sistema deve registrar a operação para auditoria.

## 8. Pós-condições
- Bracket criado com status ACTIVE;
- BracketGroups criados conforme formato;
- Times distribuídos nos grupos/chaves;
- Todas as partidas criadas com status SCHEDULED (ou FINISHED se contra BYE);
- Fases avançadas com times TBD;
- BYE criado se número ímpar (com partida FINISHED e vencedor definido);
- `match_category` definido para cada partida;
- **Se primeiro chaveamento:** Temporada atualizada para IN_PROGRESS;
- Notificações enviadas aos alunos;
- Chaveamento pronto para monitor agendar datas e iniciar partidas;
- Operação registrada para auditoria.

## 9. Cenários de Teste

| Cenário                                    | Dado                                           | Quando                              | Então                                                    |
|--------------------------------------------|------------------------------------------------|-------------------------------------|----------------------------------------------------------|
| Criação bem-sucedida (Mata-mata)           | 8 times aprovados, formato KNOCKOUT            | Clica em "Sortear"                  | Sistema cria bracket e 7 partidas (oitavas, quartas...) |
| Criação bem-sucedida (Grupos)              | 12 times, formato GROUP_STAGE_KNOCKOUT         | Clica em "Sortear"                  | Sistema cria grupos e partidas de grupo + mata-mata     |
| Menos de 2 times                           | Modalidade com 1 time aprovado                 | Tenta criar chaveamento             | Sistema bloqueia e exibe erro                            |
| Chaveamento já existe                      | Modalidade já possui bracket ativo             | Tenta criar novo                    | Sistema bloqueia e exibe erro                            |
| Ajuste de configuração                     | Sistema sugere 4 grupos de 3 times             | Monitor ajusta para 3 de 4          | Sistema aceita e sorteia com nova config                |
| Sorteio aleatório                          | 8 times aprovados                              | Clica em "Sortear"                  | Times distribuídos aleatoriamente                        |
| Times ímpares - BYE criado                 | 7 times aprovados                              | Clica em "Sortear"                  | Sistema cria BYE e partida contra ele                    |
| Partida contra BYE finalizada              | Time sorteado contra BYE                       | Após sorteio                        | Partida tem status FINISHED com vencedor definido       |
| Time avança automaticamente (BYE)          | Time venceu por W.O. contra BYE                | Verifica próxima fase               | Time já colocado na próxima rodada                      |
| Partidas TBD criadas                       | Formato mata-mata escolhido                    | Após sorteio                        | Sistema cria partidas das fases seguintes com TBD       |
| Match_category definido                    | Chaveamento misto (grupos + mata-mata)         | Após criação                        | Partidas de grupo têm GROUP, eliminatórias têm KNOCKOUT |
| Cancelamento de criação                    | Na tela de configuração                        | Clica em "Cancelar"                 | Sistema descarta e retorna sem criar                    |
| Primeiro chaveamento - Temporada IN_PROGRESS | Temporada REGISTRATION_CLOSED, 1º chaveamento | Clica em "Sortear"                  | Sistema cria chaveamento E muda temporada para IN_PROGRESS |
| Chaveamento subsequente                    | Temporada já IN_PROGRESS, 2ª modalidade        | Clica em "Sortear"                  | Sistema cria chaveamento sem alterar status da temporada |
| Notificação de início de jogos             | Primeiro chaveamento criado                    | Após criação                        | Alunos recebem "🏆 Fase de jogos iniciada!"             |
| Notificação de novo chaveamento            | Chaveamento subsequente criado                 | Após criação                        | Alunos recebem notificação sobre novo chaveamento       |
| Temporada ainda aberta                     | Temporada REGISTRATION_OPEN                    | Tenta criar chaveamento             | Sistema bloqueia e exibe erro                            |
| Status do bracket                          | Chaveamento criado com sucesso                 | Verifica status                     | Status é ACTIVE                                         |
| Confirmação no primeiro chaveamento        | Temporada CLOSED, criando 1º chaveamento       | Sistema exibe confirmação           | Mensagem avisa que iniciará fase de jogos               |
| Auditoria de criação                       | Chaveamento criado                             | Verifica logs                       | Sistema registra monitor, data/hora e configuração      |
| Auditoria de transição de temporada        | Primeiro chaveamento, temporada → IN_PROGRESS  | Verifica logs                       | Sistema registra transição automática de status         |

## 10. Artefatos Relacionados
- [UC001 - Criar Temporada](UC001_GestaoDeTemporadas_CriarTemporada.md)
- [UC002 - Gerenciar Temporada](UC002_GestaoDeTemporadas_GerenciarTemporada.md)
- [UC009 - Aprovar Equipes](UC009_GestaoDeEquipes_AprovarEquipes.md)
- [UC012 - Gerenciar Chaveamento](UC012_GerenciarChaveamento.md)
- [UC013 - Iniciar Partida](UC013_IniciarPartida.md)