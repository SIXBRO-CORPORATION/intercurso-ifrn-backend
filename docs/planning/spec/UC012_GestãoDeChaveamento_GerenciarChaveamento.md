# Especificação de Caso de Uso: Gerenciar Chaveamento

## 1. Descrição
Este caso de uso permite que o monitor realize ajustes no chaveamento criado, incluindo re-sortear times, editar partidas agendadas (datas e times), e deletar partidas específicas antes do início da competição.

## 2. Pré-condições
- O ator deve estar autenticado com permissão de **Monitor**;
- Deve existir um chaveamento criado com status **ACTIVE** ou **DRAFT**.

## 3. Fluxo Principal: Re-sortear Chaveamento
1. O monitor acessa o módulo "Gestão de Chaveamentos";
2. O sistema exibe lista de chaveamentos criados;
3. O monitor seleciona um chaveamento;
4. O monitor clica em "Re-sortear";
5. O sistema exibe confirmação com aviso sobre perda de dados;
6. O monitor confirma a operação;
7. O sistema valida conforme Regras de Negócio;
8. O sistema deleta todas as partidas atuais;
9. O sistema realiza novo sorteio aleatório dos times;
10. O sistema recria todas as partidas com nova distribuição;
11. O sistema exibe mensagem de sucesso.

## 4. Fluxos Alternativos

### Fluxo Alternativo 1: Editar Data/Horário de Partida
1. O monitor acessa lista de partidas do chaveamento;
2. O monitor seleciona uma partida específica;
3. O monitor clica em "Editar";
4. O sistema exibe formulário com data/horário agendado;
5. O monitor altera os dados e confirma;
6. O sistema valida e atualiza a partida;
7. O sistema exibe mensagem de sucesso.

### Fluxo Alternativo 2: Trocar Times de Partida
1. O monitor acessa partida específica;
2. O monitor clica em "Trocar Times";
3. O sistema exibe lista de times da modalidade;
4. O monitor seleciona novos times para team1 e/ou team2;
5. O monitor confirma;
6. O sistema valida conforme Regras de Negócio;
7. O sistema atualiza a partida com novos times;
8. O sistema exibe mensagem de sucesso.

### Fluxo Alternativo 3: Deletar Partida Específica
1. O monitor acessa lista de partidas;
2. O monitor seleciona partida e clica em "Deletar";
3. O sistema exibe confirmação;
4. O monitor confirma;
5. O sistema valida conforme Regras de Negócio;
6. O sistema deleta a partida (soft delete);
7. O sistema exibe mensagem de sucesso.

### Fluxo Alternativo 4: Partida Já Iniciada
1. O monitor tenta editar/deletar partida com status IN_PROGRESS ou FINISHED;
2. O sistema bloqueia a operação e exibe mensagem de erro;
3. O sistema informa que apenas partidas SCHEDULED podem ser alteradas.

### Fluxo Alternativo 5: Re-sortear com Partidas Iniciadas
1. O monitor tenta re-sortear chaveamento com partidas já iniciadas;
2. O sistema bloqueia a operação e exibe mensagem de erro;
3. O sistema lista partidas que já foram iniciadas.

### Fluxo Alternativo 6: Cancelar Operação
1. Monitor inicia qualquer operação de edição;
2. Sistema exibe modal de confirmação;
3. Monitor clica em "Cancelar";
4. Sistema fecha modal sem realizar alterações.

## 5. Bloco de Dados

### Bloco de Dados 1 – Chaveamento para Gestão

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Modalidade               | S             | Nome da modalidade                                    |
| Formato                  | S             | Formato atual do chaveamento                          |
| Total de Partidas        | S             | Quantidade de partidas criadas                        |
| Partidas Iniciadas       | S             | Quantidade de partidas já com status IN_PROGRESS+     |
| Partidas Finalizadas     | S             | Quantidade de partidas FINISHED                       |
| Status                   | S             | DRAFT ou ACTIVE                                       |
| Ações Disponíveis        | S             | Botões de re-sortear, editar, etc                     |

### Bloco de Dados 2 – Partida para Edição

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Time 1                   | E/S           | Time atual ou novo time                               |
| Time 2                   | E/S           | Time atual ou novo time                               |
| Data Agendada            | E/S           | Data/hora da partida                                  |
| Grupo/Fase               | S             | Fase ou grupo da partida                              |
| Status                   | S             | Deve ser SCHEDULED para permitir edição               |
| Categoria                | S             | GROUP ou KNOCKOUT                                     |

### Bloco de Dados 3 – Confirmação de Re-sorteio

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Partidas Afetadas        | S             | Total de partidas que serão deletadas                 |
| Aviso                    | S             | Mensagem sobre perda de datas agendadas               |
| Confirmação              | E             | Monitor deve confirmar ação                           |

## 6. Regras de Negócio

### Re-sortear:
1. Apenas **monitor** pode re-sortear;
2. Apenas chaveamentos em **DRAFT** ou **ACTIVE** podem ser re-sorteados;
3. **Nenhuma partida** deve ter sido iniciada (todas devem estar em SCHEDULED);
4. Ao re-sortear, sistema **deleta todas as partidas atuais**;
5. Sistema realiza **novo sorteio aleatório** dos times;
6. Sistema **recria todas as partidas** com nova distribuição;
7. Datas agendadas são perdidas no re-sorteio;
8. A operação deve ser registrada para auditoria.

### Editar Partida:
9. Apenas **monitor** pode editar partidas;
10. Partida deve estar em status **SCHEDULED**;
11. Monitor pode alterar **data/horário** da partida;
12. Monitor pode trocar **times** da partida (team1 e/ou team2);
13. Times trocados devem ser da **mesma modalidade**;
14. Times trocados devem estar **APPROVED**;
15. Partidas IN_PROGRESS ou FINISHED **não podem ser editadas**;
16. A operação deve ser registrada para auditoria.

### Deletar Partida:
17. Apenas **monitor** pode deletar partidas;
18. Partida deve estar em status **SCHEDULED**;
19. Sistema realiza **soft delete** (active = false);
20. Partidas deletadas não aparecem mais nas listagens;
21. A operação deve ser registrada para auditoria.

### Geral:
22. Monitor tem **total controle** sobre partidas antes de iniciá-las;
23. Sistema deve validar consistência do chaveamento após alterações;
24. Todas as operações devem ter confirmação antes de executar.

## 7. Critérios de Aceitação
- O sistema deve bloquear re-sorteio se houver partidas iniciadas;
- O sistema deve deletar e recriar todas as partidas ao re-sortear;
- O sistema deve permitir edição de data/horário de partidas SCHEDULED;
- O sistema deve permitir troca de times em partidas SCHEDULED;
- O sistema deve validar que times trocados são da mesma modalidade;
- O sistema deve bloquear edição/deleção de partidas não SCHEDULED;
- O sistema deve realizar soft delete ao deletar partidas;
- O sistema deve exibir confirmação antes de operações destrutivas;
- O sistema deve exibir mensagens claras de sucesso ou erro;
- O sistema deve registrar todas as operações para auditoria.

## 8. Pós-condições

### Re-sorteio:
- Todas as partidas antigas deletadas;
- Novas partidas criadas com novo sorteio;
- Times redistribuídos aleatoriamente;
- Datas agendadas resetadas (null);
- Operação registrada para auditoria.

### Edição:
- Partida atualizada com novos dados (data/times);
- Chaveamento mantém consistência;
- Operação registrada para auditoria.

### Deleção:
- Partida marcada como inativa (soft delete);
- Partida não aparece mais em listagens;
- Operação registrada para auditoria.

## 9. Cenários de Teste

| Cenário                                    | Dado                                           | Quando                              | Então                                                    |
|--------------------------------------------|------------------------------------------------|-------------------------------------|----------------------------------------------------------|
| Re-sorteio bem-sucedido                    | Chaveamento com partidas SCHEDULED             | Clica em "Re-sortear"               | Sistema deleta e recria partidas com novo sorteio       |
| Re-sorteio com partidas iniciadas          | Chaveamento com 2 partidas IN_PROGRESS         | Tenta re-sortear                    | Sistema bloqueia e lista partidas iniciadas             |
| Edição de data bem-sucedida                | Partida SCHEDULED sem data                     | Define data e confirma              | Sistema atualiza data da partida                        |
| Troca de times bem-sucedida                | Partida SCHEDULED entre Time A e B             | Troca Time B por Time C             | Sistema atualiza partida com Time C                     |
| Troca de times de outra modalidade         | Partida de Futsal                              | Tenta colocar time de Vôlei         | Sistema bloqueia e exibe erro                           |
| Edição de partida IN_PROGRESS             | Partida já iniciada                            | Tenta editar                        | Sistema bloqueia e exibe erro                           |
| Deleção bem-sucedida                       | Partida SCHEDULED                              | Clica em "Deletar"                  | Sistema soft delete e remove da listagem                |
| Deleção de partida finalizada              | Partida FINISHED                               | Tenta deletar                       | Sistema bloqueia e exibe erro                           |
| Cancelamento de re-sorteio                 | Modal de confirmação aberto                    | Clica em "Cancelar"                 | Sistema fecha sem realizar alterações                   |
| Cancelamento de edição                     | Modal de edição aberto                         | Clica em "Cancelar"                 | Sistema fecha sem salvar                                |
| Validação de times aprovados               | Partida sendo editada                          | Tenta colocar time PENDING_APPROVAL | Sistema bloqueia e exibe erro                           |
| Datas agendadas perdidas no re-sorteio     | Chaveamento com partidas com datas definidas   | Re-sorteia                          | Sistema recria partidas sem datas                       |
| Auditoria de re-sorteio                    | Re-sorteio realizado                           | Verifica logs                       | Sistema registra monitor, data/hora e ação              |
| Auditoria de edição                        | Partida editada                                | Verifica logs                       | Sistema registra monitor, alterações e data/hora        |
| Auditoria de deleção                       | Partida deletada                               | Verifica logs                       | Sistema registra monitor, partida e data/hora           |

## 10. Artefatos Relacionados
- [UC011 - Criar Chaveamento](UC011_CriarChaveamento.md)
- [UC013 - Iniciar Partida](UC013_IniciarPartida.md)
- [UC015 - Finalizar Partida](UC015_FinalizarPartida.md)