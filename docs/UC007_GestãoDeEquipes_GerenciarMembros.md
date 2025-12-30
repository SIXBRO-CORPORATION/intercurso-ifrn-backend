# Especificação de Caso de Uso: Gerenciar Membros

## 1. Descrição
Este caso de uso permite que o dono (owner) de um time gerencie seus membros durante o status DRAFT, incluindo selecionar capitão, remover membros e que membros possam sair do time voluntariamente. O owner pode acumular o papel de capitão.

## 2. Pré-condições
- O ator deve estar autenticado como **Aluno**;
- Para operações de owner: deve ser o dono do time;
- Para sair do time: deve ser membro mas não owner;
- Time deve estar em status **DRAFT** (exceto para monitor que pode gerenciar em qualquer status).

## 3. Fluxo Principal: Selecionar Capitão
1. O owner acessa a página de detalhes do seu time;
2. O sistema exibe a listagem de membros do time;
3. O owner clica em "Selecionar Capitão" em um dos membros (incluindo ele mesmo);
4. O sistema exibe confirmação da seleção;
5. O owner confirma a operação;
6. O sistema valida os dados conforme Regras de Negócio;
7. O sistema remove role CAPTAIN do membro anterior (se existir);
8. O sistema adiciona role CAPTAIN ao membro selecionado;
9. O sistema atualiza `team.captain_id` para o membro selecionado;
10. O sistema exibe mensagem de sucesso.

## 4. Fluxos Alternativos

### Fluxo Alternativo 1: Remover Membro (Owner)
1. O owner acessa a listagem de membros do time;
2. O owner clica em "Remover" em um dos membros;
3. O sistema exibe confirmação da remoção;
4. O owner confirma a operação;
5. O sistema valida conforme Regras de Negócio;
6. O sistema remove o registro de TeamMember;
7. Se o membro era capitão, sistema limpa `team.captain_id`;
8. O sistema atualiza `user.is_athlete = false` se o usuário não estiver em outros times;
9. O sistema exibe mensagem de sucesso.

### Fluxo Alternativo 2: Sair do Time (Membro)
1. O membro acessa a página de detalhes do time;
2. O membro clica em "Sair do Time";
3. O sistema exibe confirmação da saída;
4. O membro confirma a operação;
5. O sistema valida conforme Regras de Negócio;
6. O sistema remove o registro de TeamMember;
7. Se o membro era capitão, sistema limpa `team.captain_id`;
8. O sistema atualiza `user.is_athlete = false` se o usuário não estiver em outros times;
9. O sistema exibe mensagem de sucesso e redireciona.

### Fluxo Alternativo 3: Owner Tenta Sair do Time
1. O owner clica em "Sair do Time";
2. O sistema bloqueia a operação e exibe mensagem de erro;
3. Sistema informa que owner deve deletar o time ao invés de sair.

### Fluxo Alternativo 4: Owner Se Seleciona Como Capitão
1. Owner seleciona a si mesmo como capitão;
2. Sistema permite normalmente a operação;
3. Owner acumula roles: OWNER e CAPTAIN;
4. Sistema atualiza interface exibindo ambos os papéis;
5. Sistema exibe mensagem de sucesso.

### Fluxo Alternativo 5: Operação Fora do Status DRAFT
1. Usuário tenta realizar operação com time não em DRAFT;
2. O sistema bloqueia a operação e exibe mensagem de erro;
3. Sistema informa que time não aceita mais alterações.

### Fluxo Alternativo 6: Remover Membro (Monitor)
1. Monitor acessa a página de gerenciamento de times;
2. Monitor seleciona um time e acessa seus membros;
3. Monitor clica em "Remover Membro";
4. O sistema valida permissão de monitor;
5. O sistema remove o membro independente do status do time;
6. O sistema registra a operação como administrativa;
7. O sistema exibe mensagem de sucesso.

## 5. Bloco de Dados

### Bloco de Dados 1 – Membro do Time

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Nome do Membro           | S             | Nome completo do usuário                              |
| Papel (Role)             | S             | OWNER, CAPTAIN, MEMBER (owner pode ter ambos)         |
| Status de Doação         | S             | PENDING_DONATION, DONATION_CONFIRMED                  |
| Data de Entrada          | S             | Quando entrou no time                                 |
| É Owner                  | S             | Indicador visual                                      |
| É Capitão                | S             | Indicador visual                                      |

### Bloco de Dados 2 – Operação de Gerenciamento

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Tipo de Operação         | E             | SELECIONAR_CAPITAO, REMOVER_MEMBRO, SAIR_TIME         |
| Membro Alvo              | E             | ID do usuário afetado pela operação                   |
| Autor da Operação        | S             | Usuário que executou (owner, membro ou monitor)       |
| Data da Operação         | S             | Timestamp automático                                  |

## 6. Regras de Negócio

### Selecionar Capitão:
1. Apenas **owner** pode selecionar capitão;
2. Time deve estar em status **DRAFT**;
3. Membro selecionado deve pertencer ao time;
4. **Owner PODE ser selecionado como capitão** (acumula papéis);
5. Apenas um capitão por time;
6. Ao selecionar novo capitão, role CAPTAIN do anterior é removido;
7. `team.captain_id` é atualizado para o novo capitão;
8. Owner pode acumular roles OWNER e CAPTAIN simultaneamente.

### Diferença entre OWNER e CAPTAIN:
9. **OWNER:** Gerencia o time no sistema (membros, convites, submissão, doações);
10. **CAPTAIN:** Referência em quadra durante partidas (súmula, comunicação com monitor);
11. Um usuário pode ser OWNER e CAPTAIN ao mesmo tempo.

### Remover Membro:
12. Apenas **owner** pode remover membros durante DRAFT;
13. **Monitor** pode remover membros em qualquer status;
14. Owner não pode ser removido (deve deletar o time);
15. Membro deve pertencer ao time;
16. Se membro removido era capitão, `team.captain_id` é limpo;
17. `user.is_athlete` é atualizado para `false` se usuário não estiver em outros times;
18. Remoção por monitor deve ser registrada como operação administrativa.

### Sair do Time:
19. Qualquer membro (exceto owner) pode sair do time;
20. Owner não pode sair do time;
21. Time deve estar em status **DRAFT**;
22. Se membro que sai era capitão, `team.captain_id` é limpo;
23. `user.is_athlete` é atualizado para `false` se usuário não estiver em outros times.

### Geral:
24. Todas as operações devem ser registradas para auditoria;
25. Operações de monitor são permitidas em qualquer status do time.

## 7. Critérios de Aceitação
- O sistema deve permitir apenas owner selecionar capitão;
- O sistema deve permitir owner ser selecionado como capitão;
- O sistema deve exibir visualmente quando owner acumula papel de capitão;
- O sistema deve atualizar role de capitão anterior ao selecionar novo;
- O sistema deve permitir owner remover membros durante DRAFT;
- O sistema deve permitir monitor remover membros em qualquer status;
- O sistema deve bloquear remoção do owner;
- O sistema deve permitir membros saírem do time durante DRAFT;
- O sistema deve bloquear owner de sair do time;
- O sistema deve limpar captain_id ao remover/sair do capitão;
- O sistema deve atualizar `is_athlete` corretamente;
- O sistema deve bloquear operações fora do status DRAFT (exceto monitor);
- O sistema deve exibir mensagens claras de sucesso ou erro;
- O sistema deve registrar todas as operações para auditoria.

## 8. Pós-condições

### Selecionar Capitão:
- Membro selecionado tem role=CAPTAIN adicionado;
- Capitão anterior (se existia) perde role CAPTAIN;
- `team.captain_id` atualizado;
- Se owner foi selecionado, acumula OWNER e CAPTAIN;
- Operação registrada para auditoria.

### Remover Membro:
- Registro de TeamMember deletado;
- `team.captain_id` limpo se era capitão;
- `user.is_athlete` atualizado se necessário;
- Operação registrada para auditoria.

### Sair do Time:
- Registro de TeamMember deletado;
- `team.captain_id` limpo se era capitão;
- `user.is_athlete` atualizado se necessário;
- Operação registrada para auditoria.

## 9. Cenários de Teste

| Cenário                                    | Dado                                           | Quando                              | Então                                                    |
|--------------------------------------------|------------------------------------------------|-------------------------------------|----------------------------------------------------------|
| Selecionar capitão com sucesso             | Owner, time DRAFT, membro válido               | Clica em "Selecionar Capitão"       | Sistema adiciona role CAPTAIN e atualiza captain_id      |
| Selecionar novo capitão                    | Time já tem capitão definido                   | Seleciona outro membro              | Sistema remove CAPTAIN do anterior e define novo         |
| Owner se seleciona como capitão            | Owner seleciona a si mesmo                     | Clica em "Selecionar Capitão"       | Sistema permite e owner acumula OWNER + CAPTAIN          |
| Interface com owner-capitão                | Owner é também capitão                         | Visualiza lista de membros          | Sistema exibe badges "Dono" e "Capitão" no mesmo usuário |
| Selecionar capitão fora de DRAFT           | Time em PENDING_APPROVAL                       | Tenta selecionar capitão            | Sistema bloqueia e exibe erro                            |
| Remover membro com sucesso                 | Owner, time DRAFT, membro válido               | Clica em "Remover"                  | Sistema remove membro                                    |
| Remover capitão                            | Membro a ser removido é o capitão              | Clica em "Remover"                  | Sistema remove e limpa captain_id                        |
| Owner tenta se remover                     | Owner clica em remover a si mesmo              | Clica em "Remover"                  | Sistema bloqueia e exibe erro                            |
| Monitor remove membro                      | Monitor, time APPROVED                         | Clica em "Remover"                  | Sistema remove e registra como operação administrativa   |
| Membro sai do time                         | Membro comum, time DRAFT                       | Clica em "Sair do Time"             | Sistema remove membro                                    |
| Capitão sai do time                        | Capitão, time DRAFT                            | Clica em "Sair do Time"             | Sistema remove e limpa captain_id                        |
| Owner tenta sair                           | Owner clica em "Sair do Time"                  | Clica em "Sair"                     | Sistema bloqueia e exibe erro                            |
| Sair fora de DRAFT                         | Membro, time APPROVED                          | Clica em "Sair do Time"             | Sistema bloqueia e exibe erro                            |
| Atualização de is_athlete                  | Membro único time removido                     | Remove membro                       | Sistema atualiza `is_athlete = false`                    |
| Manutenção de is_athlete                   | Membro em múltiplos times removido             | Remove de um time                   | Sistema mantém `is_athlete = true`                       |
| Auditoria de operações                     | Qualquer operação realizada                    | Verifica logs                       | Sistema registra autor, data/hora e ação                 |

## 10. Nota sobre Papéis Acumulados

Owner e Capitão são papéis complementares:
- **OWNER (Dono):** "Administrador" do time no sistema
- **CAPTAIN (Capitão):** Líder em quadra durante os jogos
- **Comum em times escolares/universitários:** O organizador do time (owner) geralmente é também a liderança em campo (captain)
- **Sistema permite acúmulo:** Um mesmo usuário pode ter ambos os papéis simultaneamente
- **Interface visual:** Sistema deve exibir ambas as badges quando usuário acumula papéis

## 11. Artefatos Relacionados
- [UC005 - Criar Equipe](UC005_GestaoDeEquipes_CriarEquipe.md)
- [UC006 - Entrar em Time via Convite](UC006_GestaoDeEquipes_EntrarViaConvite.md)
- [UC008 - Submeter Equipe](UC008_GestaoDeEquipes_SubmeterEquipe.md)