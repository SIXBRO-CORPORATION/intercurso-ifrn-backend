# Especificação de Caso de Uso: Gerenciar Temporada

## 1. Descrição
Este caso de uso permite que o monitor gerencie uma temporada existente, incluindo editar datas de inscrição (antes da abertura), encerrar período de inscrições antecipadamente e visualizar estatísticas da temporada.

## 2. Pré-condições
- O ator deve estar autenticado com permissão de **Monitor**;
- Deve existir uma temporada cadastrada.

## 3. Fluxo Principal: Visualizar Temporada
1. O ator acessa o módulo "Gestão de Temporadas";
2. O sistema exibe a listagem de temporadas cadastradas;
3. O ator seleciona uma temporada;
4. O sistema exibe detalhes conforme Bloco de Dados 1;
5. O sistema exibe ações disponíveis baseadas no status atual.

## 4. Fluxos Alternativos

### Fluxo Alternativo 1: Editar Datas de Inscrição (Antes da Abertura)
1. O ator acessa temporada com status DRAFT;
2. O ator clica em "Editar Datas de Inscrição";
3. O sistema exibe formulário com datas atuais;
4. O ator altera data de abertura e/ou encerramento;
5. O ator confirma a alteração;
6. O sistema valida os dados conforme Regras de Negócio;
7. O sistema atualiza as datas;
8. O sistema atualiza agendamentos dos jobs automáticos;
9. O sistema exibe mensagem de sucesso.

### Fluxo Alternativo 2: Editar Apenas Data de Encerramento (Após Abertura)
1. O ator acessa temporada com status REGISTRATION_OPEN;
2. O ator clica em "Editar Data de Encerramento";
3. O sistema exibe formulário com data de encerramento atual;
4. O ator altera apenas data de encerramento;
5. O ator confirma;
6. O sistema valida conforme Regras de Negócio;
7. O sistema atualiza data de encerramento;
8. O sistema atualiza agendamento do job de encerramento;
9. O sistema exibe mensagem de sucesso.

### Fluxo Alternativo 3: Encerrar Inscrições Antecipadamente
1. O ator acessa temporada com status REGISTRATION_OPEN;
2. O ator clica em "Encerrar Inscrições Agora";
3. O sistema exibe confirmação: "Encerrar período de inscrições antecipadamente? Nenhum novo time poderá ser criado ou submetido.";
4. O ator confirma;
5. O sistema valida conforme Regras de Negócio;
6. O sistema atualiza status para REGISTRATION_CLOSED;
7. O sistema define `registration_closed_at = now()`;
8. O sistema cancela job agendado de encerramento automático;
9. O sistema envia notificação aos alunos e monitores;
10. O sistema exibe mensagem de sucesso.

### Fluxo Alternativo 4: Reabrir Inscrições (Emergência)
1. O ator acessa temporada com status REGISTRATION_CLOSED;
2. O ator clica em "Reabrir Inscrições";
3. O sistema exibe confirmação: "Reabrir período de inscrições? Defina nova data de encerramento.";
4. O ator define nova data de encerramento;
5. O ator confirma;
6. O sistema valida conforme Regras de Negócio;
7. O sistema atualiza status para REGISTRATION_OPEN;
8. O sistema agenda novo job de encerramento;
9. O sistema envia notificação aos alunos;
10. O sistema exibe mensagem de sucesso.

### Fluxo Alternativo 5: Adiar Abertura
1. O ator acessa temporada com status DRAFT;
2. O ator clica em "Adiar Abertura";
3. O sistema exibe formulário com data atual;
4. O ator define nova data de abertura;
5. O ator confirma;
6. O sistema valida que nova data > agora;
7. O sistema atualiza data de abertura;
8. O sistema atualiza agendamento do job;
9. O sistema exibe mensagem de sucesso.

### Fluxo Alternativo 6: Tentar Editar Após IN_PROGRESS
1. O ator tenta editar temporada em status IN_PROGRESS ou FINISHED;
2. O sistema bloqueia a operação;
3. O sistema exibe mensagem: "Não é possível editar temporada em andamento ou finalizada.";

### Fluxo Alternativo 7: Cancelar Operação
1. Monitor inicia qualquer operação de edição;
2. Sistema exibe modal de confirmação;
3. Monitor clica em "Cancelar";
4. Sistema fecha modal sem realizar alterações.

## 5. Bloco de Dados

### Bloco de Dados 1 – Detalhes da Temporada

| Campo                           | Entrada/Saída | Observações                                           |
|---------------------------------|---------------|-------------------------------------------------------|
| Nome                            | S             | Nome da temporada                                     |
| Ano                             | S             | Ano de referência                                     |
| Status                          | S             | Status atual da temporada                             |
| Ativa                           | S             | Se `is_active = true`                                 |
| Modalidades                     | S             | Lista de modalidades vinculadas                       |
| Data de Abertura                | E/S           | Quando abrirá ou abriu                                |
| Data de Encerramento            | E/S           | Quando encerrará ou encerrou                          |
| Data Real de Abertura           | S             | Quando realmente abriu (se já abriu)                  |
| Data Real de Encerramento       | S             | Quando realmente encerrou (se já encerrou)            |
| Total de Times Criados          | S             | Estatística                                           |
| Total de Times Submetidos       | S             | Estatística                                           |
| Total de Times Aprovados        | S             | Estatística                                           |
| Ações Disponíveis               | S             | Botões baseados no status                             |

### Bloco de Dados 2 – Edição de Datas

| Campo                           | Entrada/Saída | Observações                                           |
|---------------------------------|---------------|-------------------------------------------------------|
| Nova Data de Abertura           | E             | >= agora (apenas se DRAFT)                            |
| Nova Data de Encerramento       | E             | > data de abertura                                    |
| Motivo da Alteração             | E             | Opcional, para auditoria                              |

## 6. Regras de Negócio

### Edição de Datas:
1. Monitor pode editar datas apenas em status **DRAFT** ou **REGISTRATION_OPEN**;
2. Em DRAFT: pode editar abertura e encerramento;
3. Em REGISTRATION_OPEN: pode editar apenas encerramento;
4. Nova data de abertura deve ser >= agora;
5. Nova data de encerramento deve ser > data de abertura;
6. Sistema atualiza agendamentos dos jobs automaticamente;
7. Alterações são registradas para auditoria.

### Encerramento Antecipado:
8. Apenas temporadas em **REGISTRATION_OPEN** podem ser encerradas antecipadamente;
9. Status muda para REGISTRATION_CLOSED imediatamente;
10. Job agendado de encerramento automático é cancelado;
11. Notificações enviadas aos alunos e monitores;
12. Times DRAFT não podem mais ser submetidos.

### Reabertura:
13. Apenas temporadas em **REGISTRATION_CLOSED** podem ser reabertas;
14. Monitor deve definir nova data de encerramento;
15. Status volta para REGISTRATION_OPEN;
16. Novo job de encerramento é agendado;
17. Notificação enviada aos alunos;
18. Times DRAFT podem voltar a ser submetidos.

### Bloqueios:
19. Temporadas em **IN_PROGRESS** ou **FINISHED** não podem ter datas editadas;
20. Temporadas FINISHED não podem ser reabertas;
21. Apenas monitor pode realizar essas operações.

### Auditoria:
22. Todas as alterações devem ser registradas para auditoria;
23. Sistema registra: monitor, data/hora, alteração realizada, motivo (se informado).

## 7. Critérios de Aceitação
- O sistema deve permitir edição de datas em DRAFT e REGISTRATION_OPEN;
- O sistema deve bloquear edição de data de abertura após status mudar;
- O sistema deve validar que nova data de abertura >= agora;
- O sistema deve validar que nova data de encerramento > abertura;
- O sistema deve atualizar agendamentos dos jobs após alterações;
- O sistema deve permitir encerramento antecipado;
- O sistema deve permitir reabertura com nova data;
- O sistema deve bloquear edições em IN_PROGRESS ou FINISHED;
- O sistema deve enviar notificações apropriadas;
- O sistema deve exibir mensagens claras de sucesso ou erro;
- O sistema deve registrar todas as operações para auditoria.

## 8. Pós-condições

### Edição de Datas:
- Datas atualizadas no sistema;
- Jobs reagendados;
- Operação registrada para auditoria.

### Encerramento Antecipado:
- Status atualizado para REGISTRATION_CLOSED;
- Job de encerramento cancelado;
- Notificações enviadas;
- Operação registrada para auditoria.

### Reabertura:
- Status atualizado para REGISTRATION_OPEN;
- Novo job agendado;
- Notificações enviadas;
- Operação registrada para auditoria.

## 9. Cenários de Teste

| Cenário                                    | Dado                                           | Quando                              | Então                                                    |
|--------------------------------------------|------------------------------------------------|-------------------------------------|----------------------------------------------------------|
| Editar datas em DRAFT                      | Temporada DRAFT                                | Altera ambas as datas               | Sistema atualiza e reagenda jobs                        |
| Editar apenas encerramento em OPEN         | Temporada REGISTRATION_OPEN                    | Altera data de encerramento         | Sistema atualiza job de encerramento                    |
| Tentar editar abertura em OPEN             | Temporada REGISTRATION_OPEN                    | Tenta alterar abertura              | Sistema bloqueia e exibe erro                           |
| Encerrar antecipadamente                   | Temporada REGISTRATION_OPEN                    | Clica "Encerrar Agora"              | Sistema muda para CLOSED e notifica                     |
| Reabrir inscrições                         | Temporada REGISTRATION_CLOSED                  | Clica "Reabrir" e define data       | Sistema volta para OPEN e agenda novo job               |
| Adiar abertura                             | Temporada DRAFT                                | Clica "Adiar Abertura"              | Sistema atualiza data e reagenda                        |
| Tentar editar em IN_PROGRESS               | Temporada IN_PROGRESS                          | Tenta editar datas                  | Sistema bloqueia operação                               |
| Tentar editar em FINISHED                  | Temporada FINISHED                             | Tenta editar datas                  | Sistema bloqueia operação                               |
| Data de abertura no passado                | Edição de data, define data < agora            | Confirma                            | Sistema bloqueia e exibe erro                           |
| Data de encerramento antes da abertura     | Edição, encerramento <= abertura               | Confirma                            | Sistema bloqueia e exibe erro                           |
| Cancelar edição                            | Modal de edição aberto                         | Clica "Cancelar"                    | Sistema fecha sem salvar                                |
| Notificação de encerramento antecipado     | Encerramento antecipado realizado              | Operação concluída                  | Alunos e monitores recebem notificação                  |
| Notificação de reabertura                  | Reabertura realizada                           | Operação concluída                  | Alunos recebem notificação                              |
| Auditoria de edição                        | Datas alteradas                                | Verifica logs                       | Sistema registra monitor, alterações e data/hora        |
| Auditoria de encerramento antecipado       | Encerramento realizado                         | Verifica logs                       | Sistema registra monitor e motivo                       |

## 10. Artefatos Relacionados
- [UC001 - Criar Temporada](UC001_GestaoDeTemporadas_CriarTemporada.md)
- [UC003 - Finalizar Temporada](UC003_GestaoDeTemporadas_FinalizarTemporada.md)
- [UC005 - Criar Equipe](UC005_GestaoDeEquipes_CriarEquipe.md)
- [UC011 - Criar Chaveamento](UC011_GestaoDeChaveamento_CriarChaveamento.md)