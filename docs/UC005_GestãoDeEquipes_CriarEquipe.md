# Especificação de Caso de Uso: Criar Equipe

## 1. Descrição
Este caso de uso permite que um aluno crie um novo time para participar de uma modalidade durante o período de inscrições. O criador se torna automaticamente o dono (owner) do time e recebe um link de convite para compartilhar com outros alunos.

## 2. Pré-condições
- O ator deve estar autenticado como **Aluno**;
- Deve existir uma temporada ativa (`is_active = true`) com status **REGISTRATION_OPEN**;
- O período de inscrição deve estar aberto (data atual entre `registration_start_date` e `registration_end_date`);
- O aluno não deve estar em outro time da mesma modalidade na temporada ativa.

## 3. Fluxo Principal: Criar Novo Time
1. O ator acessa o módulo "Minhas Equipes";
2. O sistema exibe a listagem dos times do aluno;
3. O ator clica em "Criar Time";
4. O sistema valida que existe temporada ativa em REGISTRATION_OPEN;
5. O sistema exibe lista de modalidades disponíveis na temporada ativa;
6. O ator seleciona uma modalidade;
7. O sistema exibe o formulário com os campos definidos no Bloco de Dados 1;
8. O ator preenche o nome do time e, opcionalmente, adiciona uma foto;
9. O ator confirma a criação;
10. O sistema valida os dados conforme Regras de Negócio;
11. O sistema cria o time com status DRAFT;
12. O sistema gera um `invite_token` único;
13. O sistema define o aluno como owner e adiciona como primeiro membro;
14. O sistema atualiza `user.is_athlete = true`;
15. O sistema exibe mensagem de sucesso e apresenta o link de convite.

## 4. Fluxos Alternativos

### Fluxo Alternativo 1: Aluno Já Está em Time da Mesma Modalidade
1. O ator tenta criar time de modalidade em que já participa;
2. O sistema bloqueia a operação e exibe mensagem de erro;
3. O ator é redirecionado para listagem de times.

### Fluxo Alternativo 2: Período de Inscrição Fechado
1. Sistema detecta que temporada ativa está em REGISTRATION_CLOSED ou IN_PROGRESS;
2. Sistema bloqueia botão "Criar Time";
3. Sistema exibe mensagem: "Período de inscrições encerrado. Aguarde a próxima temporada.";

### Fluxo Alternativo 3: Nenhuma Temporada Ativa ou em Período de Inscrição
1. O ator tenta criar time sem temporada ativa em REGISTRATION_OPEN;
2. Sistema bloqueia botão "Criar Time";
3. Sistema exibe mensagem: "Não há período de inscrições aberto no momento.";
4. Sistema pode exibir countdown para próxima abertura (se temporada DRAFT existe).

### Fluxo Alternativo 4: Modalidade Inativa
1. O ator tenta criar time de modalidade inativa;
2. O sistema não exibe a modalidade na lista de opções disponíveis.

### Fluxo Alternativo 5: Temporada Encerra Durante Criação
1. Aluno está preenchendo formulário;
2. Sistema detecta que temporada mudou para REGISTRATION_CLOSED;
3. Sistema exibe alerta: "⚠️ Período de inscrições encerrado enquanto você criava o time.";
4. Sistema bloqueia confirmação;
5. Aluno precisa aguardar próximo período.

## 5. Bloco de Dados

### Bloco de Dados 1 – Time

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Nome do Time             | E             | Nome único para o time                                |
| Foto/Logo                | E             | URL da imagem (opcional)                              |
| Modalidade               | E             | Modalidade selecionada da temporada ativa             |
| Temporada                | S             | Temporada ativa automaticamente vinculada             |
| Status                   | S             | Sempre criado como DRAFT                              |
| Link de Convite          | S             | URL gerada automaticamente com o token                |
| Token de Convite         | S             | Token único gerado (UUID)                             |
| Convite Ativo            | S             | Sempre `true` na criação                              |
| Dono (Owner)             | S             | Usuário criador automaticamente                       |
| Contagem de Membros      | S             | Inicia com 1 (o owner)                                |
| Mínimo de Membros        | S             | Obtido da modalidade                                  |
| Máximo de Membros        | S             | Obtido da modalidade                                  |
| Data de Criação          | S             | Data/hora de criação automática                       |

## 6. Regras de Negócio
1. O campo **Nome do Time** não pode estar vazio;
2. Deve existir temporada ativa (`is_active = true`) em status **REGISTRATION_OPEN**;
3. Data atual deve estar dentro do período de inscrição;
4. Aluno não pode estar em outro time da mesma modalidade na mesma temporada;
5. Modalidade deve existir e estar ativa na temporada;
6. Time é automaticamente vinculado à **temporada ativa**;
7. Time é criado com status **DRAFT**;
8. Sistema gera `invite_token` único automaticamente (UUID);
9. `invite_active` é definido como `true` na criação;
10. Criador é automaticamente definido como **owner** do time;
11. Owner é automaticamente adicionado como primeiro membro com `role = OWNER` e `donation_status = PENDING_DONATION`;
12. `user.is_athlete` do criador é atualizado para `true`;
13. Link de convite deve ser compartilhável (formato: `https://app.intercurso.com/join/{token}`);
14. A operação deve ser registrada para auditoria;
15. Sistema valida em tempo real se período de inscrição ainda está aberto.

## 7. Critérios de Aceitação
- O sistema deve bloquear criação se não houver temporada ativa em REGISTRATION_OPEN;
- O sistema deve bloquear criação fora do período de inscrição;
- O sistema deve bloquear criação se aluno já estiver em time da mesma modalidade;
- O sistema deve validar que modalidade está ativa e na temporada;
- O sistema deve criar time com status DRAFT automaticamente;
- O sistema deve gerar token único de convite;
- O sistema deve definir criador como owner automaticamente;
- O sistema deve adicionar owner como primeiro membro;
- O sistema deve atualizar `is_athlete` do criador;
- O sistema deve exibir link de convite após criação;
- O sistema deve exibir mensagens claras de sucesso ou erro;
- O sistema deve registrar a operação para auditoria;
- O sistema deve vincular time à temporada ativa automaticamente.

## 8. Pós-condições
- Novo time é criado no sistema com status DRAFT;
- Time vinculado à temporada ativa;
- Token de convite único é gerado e ativo;
- Aluno é definido como owner e primeiro membro do time;
- `user.is_athlete` do criador atualizado para `true`;
- Link de convite disponível para compartilhamento;
- Operação registrada para auditoria.

## 9. Cenários de Teste

| Cenário                                    | Dado                                           | Quando                              | Então                                                    |
|--------------------------------------------|------------------------------------------------|-------------------------------------|----------------------------------------------------------|
| Criação bem-sucedida                       | Temporada ativa OPEN, aluno sem time           | Clica em "Criar"                    | Sistema cria time DRAFT e exibe link de convite          |
| Nome vazio                                 | Campo nome não preenchido                      | Clica em "Criar"                    | Sistema bloqueia e exibe erro                            |
| Aluno já em time da modalidade             | Aluno já participa de time na mesma modalidade | Tenta criar time                    | Sistema bloqueia e exibe erro                            |
| Período de inscrição fechado               | Temporada ativa em REGISTRATION_CLOSED         | Acessa "Criar Time"                 | Botão desabilitado, mensagem informativa                 |
| Nenhuma temporada ativa                    | Não existe temporada com is_active=true        | Tenta criar time                    | Sistema bloqueia e informa ausência de período           |
| Temporada DRAFT (aguardando abertura)      | Temporada DRAFT com data futura                | Acessa "Criar Time"                 | Sistema exibe countdown para abertura                    |
| Modalidade inativa                         | Modalidade está inativa                        | Acessa seleção de modalidade        | Sistema não exibe modalidade nas opções                  |
| Token único gerado                         | Time criado com sucesso                        | Verifica `invite_token`             | Sistema gera UUID único e diferente de outros times      |
| Owner definido automaticamente             | Time criado com sucesso                        | Verifica owner do time              | Sistema define criador como owner                        |
| Owner como primeiro membro                 | Time criado com sucesso                        | Verifica membros do time            | Sistema adiciona owner com role=OWNER                    |
| Atualização de is_athlete                  | Time criado com sucesso                        | Verifica `user.is_athlete`          | Sistema atualiza para `true`                             |
| Link de convite exibido                    | Time criado com sucesso                        | Verifica resposta/interface         | Sistema exibe link compartilhável                        |
| Temporada encerra durante criação          | Aluno preenchendo formulário                   | Temporada muda para CLOSED          | Sistema bloqueia confirmação e exibe alerta              |
| Time vinculado à temporada ativa           | Time criado com sucesso                        | Verifica `team.season_id`           | Sistema vincula à temporada ativa automaticamente        |
| Auditoria de criação                       | Time criado com sucesso                        | Verifica logs de auditoria          | Sistema registra aluno, temporada, data/hora e ação      |

## 10. Artefatos Relacionados
- [UC001 - Criar Temporada](UC001_GestaoDeTemporadas_CriarTemporada.md)
- [UC002 - Gerenciar Temporada](UC002_GestaoDeTemporadas_GerenciarTemporada.md)
- [UC004 - Cadastrar Modalidade](UC004_GestaoDeModalidades_CadastrarModalidade.md)
- [UC006 - Entrar em Time via Convite](UC006_GestaoDeEquipes_EntrarViaConvite.md)
- [UC007 - Gerenciar Membros](UC007_GestaoDeEquipes_GerenciarMembros.md)
- [UC008 - Submeter Equipe](UC008_GestaoDeEquipes_SubmeterEquipe.md)