# Especificação de Caso de Uso: Aprovar Equipes

## 1. Descrição
Este caso de uso permite que o monitor aprove ou rejeite times que foram submetidos pelos alunos. A aprovação só pode ocorrer após todos os membros terem suas doações confirmadas. Times rejeitados podem receber um motivo de rejeição (sugestão futura).

## 2. Pré-condições
- O ator deve estar autenticado com permissão de **Monitor**;
- Deve existir ao menos um time com status **PENDING_APPROVAL**.

## 3. Fluxo Principal: Listar Times Pendentes
1. O monitor acessa o módulo "Gerenciamento de Equipes";
2. O sistema exibe opção de filtrar por status;
3. O monitor seleciona filtro "Pendentes de Aprovação";
4. O sistema exibe lista de times com status PENDING_APPROVAL;
5. Para cada time, o sistema exibe informações conforme Bloco de Dados 1.

## 4. Fluxos Alternativos

### Fluxo Alternativo 1: Aprovar Time
1. O monitor acessa detalhes de um time pendente;
2. O sistema exibe informações detalhadas do time e status de doações;
3. O sistema verifica se todos os membros têm doações confirmadas;
4. Se todas doações confirmadas, o sistema habilita botão "Aprovar Time";
5. O monitor clica em "Aprovar Time";
6. O sistema exibe confirmação da aprovação;
7. O monitor confirma;
8. O sistema valida conforme Regras de Negócio;
9. O sistema atualiza status para APPROVED;
10. O sistema define `approved_at = now()`;
11. O sistema exibe mensagem de sucesso;
12. Sistema envia notificação ao owner (escopo futuro).

### Fluxo Alternativo 2: Rejeitar Time
1. O monitor acessa detalhes de um time pendente;
2. O monitor clica em "Rejeitar Time";
3. O sistema exibe modal solicitando confirmação;
4. **Sugestão Futura:** Sistema solicita motivo da rejeição;
5. O monitor confirma a rejeição;
6. O sistema valida conforme Regras de Negócio;
7. O sistema atualiza status para REJECTED;
8. O sistema define `rejected_at = now()`;
9. **Sugestão Futura:** Sistema registra `rejection_reason`;
10. O sistema exibe mensagem de sucesso;
11. Sistema envia notificação ao owner (escopo futuro).

### Fluxo Alternativo 3: Tentativa de Aprovar Sem Todas Doações Confirmadas
1. O monitor tenta aprovar time com doações pendentes;
2. O sistema bloqueia a operação;
3. O sistema exibe mensagem listando membros com doações pendentes;
4. O monitor deve confirmar doações antes de aprovar.

### Fluxo Alternativo 4: Time Não Está em PENDING_APPROVAL
1. O monitor tenta aprovar/rejeitar time em outro status;
2. O sistema bloqueia a operação e exibe mensagem de erro;
3. Sistema informa status atual do time.

### Fluxo Alternativo 5: Cancelar Aprovação/Rejeição
1. Monitor inicia processo de aprovação ou rejeição;
2. Sistema exibe modal de confirmação;
3. Monitor clica em "Cancelar";
4. Sistema fecha modal sem realizar alterações.

### Fluxo Alternativo 6: Reverter Rejeição (Sugestão Futura)
1. Monitor acessa time com status REJECTED;
2. Monitor clica em "Retornar para Draft";
3. Sistema retorna time para DRAFT permitindo correções;
4. Sistema reativa convite do time;
5. Sistema notifica owner da oportunidade de correção.

## 5. Bloco de Dados

### Bloco de Dados 1 – Time Pendente (Listagem)

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Nome do Time             | S             | Nome do time                                          |
| Modalidade               | S             | Modalidade do time                                    |
| Quantidade de Membros    | S             | Total de membros                                      |
| Dono                     | S             | Nome do owner                                         |
| Data de Submissão        | S             | Quando foi submetido                                  |
| Status das Doações       | S             | "X/Y confirmadas" ou indicador visual                 |
| Ações Disponíveis        | S             | Botões de aprovar/rejeitar/detalhes                   |

### Bloco de Dados 2 – Time Aprovado

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Status                   | S             | Atualizado de PENDING_APPROVAL para APPROVED          |
| Data de Aprovação        | S             | Timestamp automático da aprovação                     |
| Monitor Aprovador        | S             | ID do monitor que aprovou                             |

### Bloco de Dados 3 – Time Rejeitado

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Status                   | S             | Atualizado de PENDING_APPROVAL para REJECTED          |
| Data de Rejeição         | S             | Timestamp automático da rejeição                      |
| Monitor Rejeitador       | S             | ID do monitor que rejeitou                            |
| Motivo de Rejeição       | E/S           | Texto explicativo (sugestão futura)                   |

## 6. Regras de Negócio

### Listagem:
1. Apenas **monitor** pode acessar listagem de times pendentes;
2. Sistema exibe apenas times com status **PENDING_APPROVAL**;
3. Listagem deve mostrar indicador de status das doações;
4. Listagem deve permitir ordenação por data de submissão.

### Aprovação:
5. Time deve estar em status **PENDING_APPROVAL**;
6. **Todos** os membros devem ter `donation_status = DONATION_CONFIRMED`;
7. Ao aprovar, status muda para **APPROVED**;
8. `approved_at` é preenchido com timestamp da aprovação;
9. Monitor aprovador é registrado;
10. Operação deve ser registrada para auditoria;
11. Owner deve ser notificado (escopo futuro).

### Rejeição:
12. Time deve estar em status **PENDING_APPROVAL**;
13. Pode rejeitar independente do status das doações;
14. Ao rejeitar, status muda para **REJECTED**;
15. `rejected_at` é preenchido com timestamp da rejeição;
16. Monitor rejeitador é registrado;
17. **Sugestão Futura:** Motivo de rejeição deve ser obrigatório;
18. **Sugestão Futura:** Time rejeitado pode voltar para DRAFT para correções;
19. Operação deve ser registrada para auditoria;
20. Owner deve ser notificado (escopo futuro).

## 7. Critérios de Aceitação
- O sistema deve exibir apenas times PENDING_APPROVAL na listagem;
- O sistema deve bloquear aprovação se doações não estiverem confirmadas;
- O sistema deve permitir rejeição independente das doações;
- O sistema deve atualizar status corretamente (APPROVED ou REJECTED);
- O sistema deve registrar timestamps de aprovação/rejeição;
- O sistema deve registrar monitor responsável pela ação;
- O sistema deve exibir mensagens claras de sucesso ou erro;
- O sistema deve registrar todas as operações para auditoria;
- O sistema deve exibir indicador de status das doações na listagem;
- O sistema deve bloquear ações em times que não estão em PENDING_APPROVAL.

## 8. Pós-condições

### Aprovação:
- Time tem status atualizado para APPROVED;
- Data de aprovação registrada;
- Monitor aprovador registrado;
- Time pode participar da competição;
- Operação registrada para auditoria.

### Rejeição:
- Time tem status atualizado para REJECTED;
- Data de rejeição registrada;
- Monitor rejeitador registrado;
- Motivo de rejeição registrado (futuro);
- Time não pode participar (a menos que seja revertido - futuro);
- Operação registrada para auditoria.

## 9. Cenários de Teste

| Cenário                                    | Dado                                           | Quando                              | Então                                                    |
|--------------------------------------------|------------------------------------------------|-------------------------------------|----------------------------------------------------------|
| Listagem de times pendentes                | Existem times PENDING_APPROVAL                 | Acessa filtro "Pendentes"           | Sistema exibe lista com informações dos times            |
| Aprovação bem-sucedida                     | Time PENDING_APPROVAL, todas doações OK        | Clica em "Aprovar"                  | Sistema atualiza para APPROVED e exibe sucesso           |
| Tentativa de aprovar sem doações           | Time com membros sem doação confirmada         | Clica em "Aprovar"                  | Sistema bloqueia e lista membros pendentes               |
| Rejeição com sucesso                       | Time PENDING_APPROVAL                          | Clica em "Rejeitar"                 | Sistema atualiza para REJECTED e exibe sucesso           |
| Rejeição com motivo (futuro)               | Time PENDING_APPROVAL                          | Preenche motivo e confirma          | Sistema registra motivo junto com rejeição               |
| Time não em PENDING_APPROVAL               | Time com status DRAFT                          | Tenta aprovar/rejeitar              | Sistema bloqueia e exibe erro                            |
| Cancelamento de aprovação                  | Modal de confirmação aberto                    | Clica em "Cancelar"                 | Sistema fecha modal sem alterações                       |
| Cancelamento de rejeição                   | Modal de confirmação aberto                    | Clica em "Cancelar"                 | Sistema fecha modal sem alterações                       |
| Registro de monitor aprovador              | Aprovação bem-sucedida                         | Verifica dados do time              | Sistema registra ID do monitor                           |
| Registro de monitor rejeitador             | Rejeição bem-sucedida                          | Verifica dados do time              | Sistema registra ID do monitor                           |
| Timestamp de aprovação                     | Aprovação bem-sucedida                         | Verifica `approved_at`              | Sistema registra data/hora da aprovação                  |
| Timestamp de rejeição                      | Rejeição bem-sucedida                          | Verifica `rejected_at`              | Sistema registra data/hora da rejeição                   |
| Indicador de doações na listagem           | Times com doações variadas                     | Visualiza listagem                  | Sistema exibe status das doações para cada time          |
| Ordenação por data de submissão            | Múltiplos times pendentes                      | Aplica ordenação                    | Sistema ordena por `submitted_at`                        |
| Reversão de rejeição (futuro)              | Time REJECTED                                  | Monitor clica em "Retornar Draft"   | Sistema retorna para DRAFT e reativa convite             |
| Auditoria de aprovação                     | Time aprovado                                  | Verifica logs de auditoria          | Sistema registra monitor, data/hora e ação               |
| Auditoria de rejeição                      | Time rejeitado                                 | Verifica logs de auditoria          | Sistema registra monitor, data/hora e ação               |

## 10. Artefatos Relacionados
- [UC008 - Submeter Equipe](UC008_GestaoDeEquipes_SubmeterEquipe.md)
- [UC010 - Confirmar Doações](UC010_GestaoDeEquipes_ConfirmarDoacoes.md)
- [UC007 - Gerenciar Membros](UC007_GestaoDeEquipes_GerenciarMembros.md)