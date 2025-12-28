# Especificação de Caso de Uso: Entrar em Time via Convite

## 1. Descrição
Este caso de uso permite que um aluno entre em um time existente através de um link de convite compartilhado pelo dono do time. O aluno se torna automaticamente um membro do time ao acessar o link válido.

## 2. Pré-condições
- O ator deve estar autenticado como **Aluno**;
- Deve existir um time com status **DRAFT** e convite ativo;
- A temporada do time deve estar em **REGISTRATION_OPEN**;
- O período de inscrição deve estar aberto;
- O aluno não deve estar em outro time da mesma modalidade na temporada ativa.

## 3. Fluxo Principal: Entrar em Time via Link
1. O ator recebe e acessa o link de convite (formato: `https://app.intercurso.com/join/{token}`);
2. O sistema valida o token e recupera informações do time;
3. O sistema exibe informações do time conforme Bloco de Dados 1;
4. O ator clica em "Entrar no Time";
5. O sistema valida os dados conforme Regras de Negócio;
6. O sistema adiciona o aluno como membro do time;
7. O sistema atualiza `user.is_athlete = true`;
8. O sistema exibe mensagem de sucesso com informações do time.

## 4. Fluxos Alternativos

### Fluxo Alternativo 1: Token Inválido ou Inexistente
1. O ator acessa link com token inválido;
2. O sistema exibe mensagem de erro informando que o convite não existe;
3. O ator é redirecionado para a página inicial.

### Fluxo Alternativo 2: Convite Inativo
1. O ator acessa link de time que já foi submetido ou finalizado;
2. O sistema exibe mensagem informando que o convite não está mais ativo;
3. O ator é redirecionado para a página inicial.

### Fluxo Alternativo 3: Time Cheio
1. O ator acessa link de time que atingiu o limite máximo de membros;
2. O sistema exibe mensagem informando que o time está completo;
3. O ator é redirecionado para a página inicial.

### Fluxo Alternativo 4: Aluno Já É Membro
1. O ator acessa link de time em que já é membro;
2. O sistema exibe mensagem informando que já faz parte do time;
3. O ator é redirecionado para a página do time.

### Fluxo Alternativo 5: Aluno em Outro Time da Mesma Modalidade
1. O ator acessa link de time de modalidade em que já participa em outro time;
2. O sistema exibe mensagem de erro informando a restrição;
3. O ator é redirecionado para a listagem de seus times.

### Fluxo Alternativo 6: Período de Inscrição Fechado
1. O ator acessa link fora do período de inscrição;
2. O sistema exibe mensagem informando que o período está fechado;
3. O ator é redirecionado para a página inicial.

## 5. Bloco de Dados

### Bloco de Dados 1 – Informações do Time (Visualização)

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Nome do Time             | S             | Nome do time                                          |
| Modalidade               | S             | Modalidade do time                                    |
| Foto/Logo                | S             | Logo do time (se disponível)                          |
| Membros Atuais           | S             | Quantidade atual de membros                           |
| Limite de Membros        | S             | Formato: "X/Y" (atual/máximo)                         |
| Capitão                  | S             | Nome do capitão (se já definido)                      |
| Dono                     | S             | Nome do dono do time                                  |

### Bloco de Dados 2 – Membro do Time (Registro)

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Papel (Role)             | S             | Sempre MEMBER na entrada via convite                  |
| Status de Doação         | S             | Sempre PENDING_DONATION na entrada                    |
| Data de Entrada          | S             | Timestamp automático                                  |

## 6. Regras de Negócio
1. Token de convite deve existir e estar ativo (`invite_active = true`);
2. Time deve estar em status **DRAFT**;
3. Temporada deve estar em **REGISTRATION_OPEN**;
4. Data atual deve estar dentro do período de inscrição;
5. Time não pode estar cheio (`members_count < max_members`);
6. Aluno não pode já ser membro do time;
7. Aluno não pode estar em outro time da mesma modalidade na mesma temporada;
8. Ao entrar, aluno recebe automaticamente `role = MEMBER` e `donation_status = PENDING_DONATION`;
9. `user.is_athlete` do aluno é atualizado para `true`;
10. `joined_at` é preenchido automaticamente com timestamp atual;
11. A operação deve ser registrada para auditoria.

## 7. Critérios de Aceitação
- O sistema deve validar token e exibir erro se inválido;
- O sistema deve bloquear entrada se convite estiver inativo;
- O sistema deve bloquear entrada se time estiver cheio;
- O sistema deve bloquear entrada se aluno já for membro;
- O sistema deve bloquear entrada se aluno estiver em outro time da modalidade;
- O sistema deve bloquear entrada fora do período de inscrição;
- O sistema deve adicionar membro com role=MEMBER automaticamente;
- O sistema deve definir donation_status=PENDING_DONATION automaticamente;
- O sistema deve atualizar `is_athlete` do aluno;
- O sistema deve exibir mensagens claras de sucesso ou erro;
- O sistema deve registrar a operação para auditoria.

## 8. Pós-condições
- Aluno é adicionado como membro do time;
- `user.is_athlete` do aluno atualizado para `true`;
- Registro de TeamMember criado com role=MEMBER e donation_status=PENDING_DONATION;
- Contador de membros do time atualizado;
- Operação registrada para auditoria.

## 9. Cenários de Teste

| Cenário                                    | Dado                                           | Quando                              | Então                                                    |
|--------------------------------------------|------------------------------------------------|-------------------------------------|----------------------------------------------------------|
| Entrada bem-sucedida                       | Token válido, time DRAFT, período aberto       | Clica em "Entrar no Time"           | Sistema adiciona membro e exibe sucesso                  |
| Token inválido                             | Token não existe no sistema                    | Acessa link                         | Sistema exibe erro e redireciona                         |
| Convite inativo                            | Time já foi submetido (invite_active=false)    | Acessa link                         | Sistema exibe erro de convite inativo                    |
| Time cheio                                 | Time atingiu limite máximo de membros          | Clica em "Entrar no Time"           | Sistema bloqueia e exibe mensagem                        |
| Aluno já é membro                          | Aluno já está no time                          | Acessa link                         | Sistema informa e redireciona para time                  |
| Aluno em outro time da modalidade          | Aluno já participa de time na mesma modalidade | Clica em "Entrar no Time"           | Sistema bloqueia e exibe erro                            |
| Período de inscrição fechado               | Data atual fora do período de inscrição        | Acessa link                         | Sistema bloqueia e informa período fechado               |
| Time não está em DRAFT                     | Time com status PENDING_APPROVAL ou APPROVED   | Acessa link                         | Sistema bloqueia e exibe erro                            |
| Role definido automaticamente              | Entrada bem-sucedida                           | Verifica role do membro             | Sistema define role=MEMBER                               |
| Status de doação definido                  | Entrada bem-sucedida                           | Verifica donation_status            | Sistema define PENDING_DONATION                          |
| Atualização de is_athlete                  | Entrada bem-sucedida                           | Verifica `user.is_athlete`          | Sistema atualiza para `true`                             |
| Contador de membros atualizado             | Entrada bem-sucedida                           | Verifica members_count              | Sistema incrementa contador                              |
| Auditoria de entrada                       | Entrada bem-sucedida                           | Verifica logs de auditoria          | Sistema registra aluno, data/hora e ação                 |

## 10. Artefatos Relacionados
- [UC005 - Criar Equipe](UC005_GestaoDeEquipes_CriarEquipe.md)
- [UC007 - Gerenciar Membros](UC007_GestaoDeEquipes_GerenciarMembros.md)
- [UC008 - Submeter Equipe](UC008_GestaoDeEquipes_SubmeterEquipe.md)