# Especificação de Caso de Uso: Confirmar Doações

## 1. Descrição
Este caso de uso permite que o monitor confirme individualmente as doações de alimentos de cada membro de um time após a submissão. A confirmação de todas as doações é pré-requisito para aprovação do time.

## 2. Pré-condições
- O ator deve estar autenticado com permissão de **Monitor**;
- Deve existir time com status **PENDING_APPROVAL** ou **APPROVED**;
- Membros do time devem ter `donation_status = PENDING_DONATION`.

## 3. Fluxo Principal: Confirmar Doação Individual
1. O monitor acessa a página de detalhes de um time;
2. O sistema exibe lista de membros com seus status de doação;
3. O monitor identifica membro com doação pendente;
4. O monitor clica em "Confirmar Doação" para o membro;
5. O sistema exibe confirmação da ação;
6. O monitor confirma a operação;
7. O sistema valida conforme Regras de Negócio;
8. O sistema atualiza `donation_status` para DONATION_CONFIRMED;
9. O sistema define `donation_confirmed_at = now()`;
10. O sistema registra `donation_confirmed_by = monitor_id`;
11. O sistema exibe mensagem de sucesso;
12. O sistema atualiza indicador visual de progresso das doações do time.

## 4. Fluxos Alternativos

### Fluxo Alternativo 1: Confirmar Múltiplas Doações em Sequência
1. O monitor acessa lista de membros do time;
2. Para cada membro com doação pendente, o monitor clica em "Confirmar";
3. Sistema processa cada confirmação individualmente;
4. Sistema atualiza indicador de progresso após cada confirmação;
5. Ao confirmar última doação, sistema habilita botão de aprovação do time.

### Fluxo Alternativo 2: Doação Já Confirmada
1. O monitor tenta confirmar doação já confirmada;
2. O sistema exibe mensagem informando que doação já foi confirmada;
3. O sistema mostra data e monitor que confirmou anteriormente.

### Fluxo Alternativo 3: Membro Não Pertence ao Time
1. O monitor tenta confirmar doação de usuário que não é membro;
2. O sistema bloqueia a operação e exibe mensagem de erro.

### Fluxo Alternativo 4: Time em Status DRAFT
1. O monitor tenta confirmar doação de time em DRAFT;
2. O sistema bloqueia a operação;
3. O sistema exibe erro: "Doações só podem ser confirmadas após submissão do time.";
4. Sistema sugere: "Aguarde o owner submeter o time para aprovação.";

### Fluxo Alternativo 5: Time em Status REJECTED
1. Monitor tenta confirmar doação de time REJECTED;
2. Sistema bloqueia operação;
3. Sistema exibe erro: "Time foi rejeitado. Doações não podem ser confirmadas.";

### Fluxo Alternativo 6: Cancelar Confirmação
1. Monitor clica em "Confirmar Doação";
2. Sistema exibe modal de confirmação;
3. Monitor clica em "Cancelar";
4. Sistema fecha modal sem realizar alterações.

### Fluxo Alternativo 7: Visualizar Histórico de Doações
1. Monitor acessa detalhes do time;
2. Monitor clica em "Histórico de Doações";
3. Sistema exibe lista com todas as confirmações realizadas;
4. Para cada confirmação, sistema exibe: membro, data/hora, monitor responsável.

### Fluxo Alternativo 8: Filtrar Times por Status de Doações
1. Monitor acessa listagem de times;
2. Monitor aplica filtro "Com Doações Pendentes";
3. Sistema exibe apenas times com ao menos um membro com doação pendente;
4. Para cada time, sistema exibe contagem de doações (ex: "7/10 confirmadas").

## 5. Bloco de Dados

### Bloco de Dados 1 – Membro com Doação Pendente

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Nome do Membro           | S             | Nome completo do usuário                              |
| Status de Doação         | S             | PENDING_DONATION, DONATION_CONFIRMED                  |
| Data de Entrada          | S             | Quando entrou no time                                 |
| Data de Confirmação      | S             | Quando doação foi confirmada (se confirmada)          |
| Monitor Confirmador      | S             | Nome do monitor que confirmou (se confirmada)         |
| Ações Disponíveis        | S             | Botão "Confirmar Doação" se pendente                  |

### Bloco de Dados 2 – Confirmação de Doação

| Campo                            | Entrada/Saída | Observações                                    |
|----------------------------------|---------------|------------------------------------------------|
| Status de Doação                 | S             | Atualizado para DONATION_CONFIRMED             |
| Data de Confirmação da Doação    | S             | Timestamp automático                           |
| Monitor Confirmador              | S             | ID do monitor que realizou a confirmação       |

### Bloco de Dados 3 – Progresso das Doações do Time

| Campo                            | Entrada/Saída | Observações                                    |
|----------------------------------|---------------|------------------------------------------------|
| Total de Membros                 | S             | Quantidade total de membros do time            |
| Doações Confirmadas              | S             | Quantidade de membros com doação confirmada    |
| Doações Pendentes                | S             | Quantidade de membros com doação pendente      |
| Percentual de Conclusão          | S             | Cálculo visual (ex: "70% completo")            |
| Todas Confirmadas                | S             | Booleano indicando se todas estão confirmadas  |

## 6. Regras de Negócio
1. Apenas **monitor** pode confirmar doações;
2. Time deve estar em status **PENDING_APPROVAL** ou **APPROVED** (não DRAFT ou REJECTED);
3. Membro deve ter `donation_status = PENDING_DONATION`;
4. Membro deve pertencer ao time;
5. Ao confirmar, `donation_status` muda para **DONATION_CONFIRMED**;
6. `donation_confirmed_at` é preenchido com timestamp da confirmação;
7. `donation_confirmed_by` é preenchido com ID do monitor;
8. Confirmação é irreversível (não pode desfazer);
9. Cada membro tem confirmação individual (não há confirmação em massa);
10. Time só pode ser aprovado se **todas** as doações estiverem confirmadas;
11. **Doações só podem ser confirmadas APÓS submissão do time** (status != DRAFT);
12. Monitor pode confirmar doações mesmo após time ser aprovado;
13. A operação deve ser registrada para auditoria;
14. Sistema deve atualizar indicador de progresso após cada confirmação.

## 7. Critérios de Aceitação
- O sistema deve permitir apenas monitor confirmar doações;
- O sistema deve bloquear confirmação em times DRAFT ou REJECTED;
- O sistema deve bloquear confirmação de doação já confirmada;
- O sistema deve validar que membro pertence ao time;
- O sistema deve atualizar status para DONATION_CONFIRMED;
- O sistema deve registrar data/hora da confirmação;
- O sistema deve registrar monitor responsável;
- O sistema deve atualizar indicador de progresso do time;
- O sistema deve habilitar aprovação quando todas doações confirmadas;
- O sistema deve exibir mensagens claras de sucesso ou erro;
- O sistema deve registrar todas as operações para auditoria;
- O sistema deve permitir filtrar times por status de doações.

## 8. Pós-condições
- `donation_status` do membro atualizado para DONATION_CONFIRMED;
- Data de confirmação registrada (`donation_confirmed_at`);
- Monitor confirmador registrado (`donation_confirmed_by`);
- Indicador de progresso do time atualizado;
- Se todas doações confirmadas, botão de aprovação habilitado;
- Operação registrada para auditoria.

## 9. Cenários de Teste

| Cenário                                    | Dado                                           | Quando                              | Então                                                    |
|--------------------------------------------|------------------------------------------------|-------------------------------------|----------------------------------------------------------|
| Confirmação bem-sucedida                   | Membro com PENDING_DONATION, time submetido    | Clica em "Confirmar Doação"         | Sistema atualiza para DONATION_CONFIRMED                 |
| Confirmação de doação já confirmada        | Membro com DONATION_CONFIRMED                  | Tenta confirmar novamente           | Sistema exibe mensagem informando já confirmada          |
| Confirmação em time DRAFT                  | Membro de time em DRAFT                        | Tenta confirmar doação              | Sistema bloqueia e exibe erro                            |
| Confirmação em time REJECTED               | Membro de time REJECTED                        | Tenta confirmar doação              | Sistema bloqueia e exibe erro                            |
| Confirmação múltiplas em sequência         | Time com 5 membros pendentes                   | Confirma uma por uma                | Sistema processa todas e atualiza progresso              |
| Última doação confirmada                   | Time com apenas 1 doação pendente              | Confirma última doação              | Sistema habilita botão de aprovação do time              |
| Timestamp de confirmação                   | Confirmação bem-sucedida                       | Verifica `donation_confirmed_at`    | Sistema registra data/hora da confirmação                |
| Monitor confirmador registrado             | Confirmação bem-sucedida                       | Verifica `donation_confirmed_by`    | Sistema registra ID do monitor                           |
| Membro não pertence ao time                | Membro de outro time                           | Tenta confirmar doação              | Sistema bloqueia e exibe erro                            |
| Cancelamento de confirmação                | Modal de confirmação aberto                    | Clica em "Cancelar"                 | Sistema fecha modal sem alterações                       |
| Indicador de progresso atualizado          | Confirmação bem-sucedida                       | Verifica indicador visual           | Sistema atualiza contador (ex: "8/10")                   |
| Histórico de doações                       | Time com várias doações confirmadas            | Acessa "Histórico"                  | Sistema exibe lista completa de confirmações             |
| Filtro por doações pendentes               | Listagem com times variados                    | Aplica filtro                       | Sistema exibe apenas times com doações pendentes         |
| Percentual de conclusão                    | Time com 7/10 doações confirmadas              | Visualiza progresso                 | Sistema exibe "70% completo"                             |
| Confirmação após aprovação                 | Time APPROVED com nova doação pendente         | Confirma doação                     | Sistema permite confirmação normalmente                  |
| Bloqueia confirmação antes de submissão    | Time DRAFT, monitor tenta confirmar            | Clica em "Confirmar Doação"         | Sistema exibe erro e sugere aguardar submissão           |
| Auditoria de confirmação                   | Confirmação bem-sucedida                       | Verifica logs de auditoria          | Sistema registra monitor, membro, data/hora e ação       |

## 10. Artefatos Relacionados
- [UC008 - Submeter Equipe](UC008_GestaoDeEquipes_SubmeterEquipe.md)
- [UC009 - Aprovar Equipes](UC009_GestaoDeEquipes_AprovarEquipes.md)
- [UC007 - Gerenciar Membros](UC007_GestaoDeEquipes_GerenciarMembros.md)