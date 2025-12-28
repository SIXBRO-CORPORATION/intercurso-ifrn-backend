# Especificação de Caso de Uso: Criar Equipe

## 1. Descrição
Este caso de uso permite que um aluno crie um novo time para participar de uma modalidade durante o período de inscrições. O criador se torna automaticamente o dono (owner) do time e recebe um link de convite para compartilhar com outros alunos.

## 2. Pré-condições
- O ator deve estar autenticado como **Aluno**;
- Deve existir uma temporada com status **REGISTRATION_OPEN**;
- O período de inscrição deve estar aberto (data atual entre `registration_start_date` e `registration_end_date`);
- O aluno não deve estar em outro time da mesma modalidade na temporada ativa.

## 3. Fluxo Principal: Criar Novo Time
1. O ator acessa o módulo "Minhas Equipes";
2. O sistema exibe a listagem dos times do aluno;
3. O ator clica em "Criar Time";
4. O sistema exibe lista de modalidades disponíveis na temporada ativa;
5. O ator seleciona uma modalidade;
6. O sistema exibe o formulário com os campos definidos no Bloco de Dados 1;
7. O ator preenche o nome do time e, opcionalmente, adiciona uma foto;
8. O ator confirma a criação;
9. O sistema valida os dados conforme Regras de Negócio;
10. O sistema cria o time com status DRAFT;
11. O sistema gera um `invite_token` único;
12. O sistema define o aluno como owner e adiciona como primeiro membro;
13. O sistema atualiza `user.is_athlete = true`;
14. O sistema exibe mensagem de sucesso e apresenta o link de convite.

## 4. Fluxos Alternativos

### Fluxo Alternativo 1: Aluno Já Está em Time da Mesma Modalidade
1. O ator tenta criar time de modalidade em que já participa;
2. O sistema bloqueia a operação e exibe mensagem de erro;
3. O ator é redirecionado para listagem de times.

### Fluxo Alternativo 2: Período de Inscrição Fechado
1. O ator tenta criar time fora do período de inscrição;
2. O sistema bloqueia a operação e exibe mensagem informando período;
3. O ator é redirecionado para listagem de times.

### Fluxo Alternativo 3: Nenhuma Temporada Ativa
1. O ator tenta criar time sem temporada ativa;
2. O sistema bloqueia a operação e exibe mensagem de erro;
3. O ator é informado que não há período de inscrições aberto.

### Fluxo Alternativo 4: Modalidade Inativa
1. O ator tenta criar time de modalidade inativa;
2. O sistema não exibe a modalidade na lista de opções disponíveis.

## 5. Bloco de Dados

### Bloco de Dados 1 – Time

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Nome do Time             | E             | Nome único para o time                                |
| Foto/Logo                | E             | URL da imagem (opcional)                              |
| Modalidade               | E             | Modalidade selecionada da temporada ativa             |
| Status                   | S             | Sempre criado como DRAFT                              |
| Link de Convite          | S             | URL gerada automaticamente com o token                |
| Token de Convite         | S             | Token único gerado (UUID ou alfanumérico)             |
| Convite Ativo            | S             | Sempre `true` na criação                              |
| Dono (Owner)             | S             | Usuário criador automaticamente                       |
| Contagem de Membros      | S             | Inicia com 1 (o owner)                                |
| Mínimo de Membros        | S             | Obtido da modalidade                                  |
| Máximo de Membros        | S             | Obtido da modalidade                                  |
| Data de Criação          | S             | Data/hora de criação automática                       |

## 6. Regras de Negócio
1. O campo **Nome do Time** não pode estar vazio;
2. Temporada deve estar em status **REGISTRATION_OPEN**;
3. Data atual deve estar dentro do período de inscrição;
4. Aluno não pode estar em outro time da mesma modalidade na mesma temporada;
5. Modalidade deve existir e estar ativa na temporada;
6. Time é criado com status **DRAFT**;
7. Sistema gera `invite_token` único automaticamente;
8. `invite_active` é definido como `true` na criação;
9. Criador é automaticamente definido como **owner** do time;
10. Owner é automaticamente adicionado como primeiro membro com `role = OWNER` e `donation_status = PENDING_DONATION`;
11. `user.is_athlete` do criador é atualizado para `true`;
12. Link de convite deve ser compartilhável (formato: `https://app.intercurso.com/join/{token}`);
13. A operação deve ser registrada para auditoria.

## 7. Critérios de Aceitação
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
- O sistema deve registrar a operação para auditoria.

## 8. Pós-condições
- Novo time é criado no sistema com status DRAFT;
- Token de convite único é gerado e ativo;
- Aluno é definido como owner e primeiro membro do time;
- `user.is_athlete` do criador atualizado para `true`;
- Link de convite disponível para compartilhamento;
- Operação registrada para auditoria.

## 9. Cenários de Teste

| Cenário                                    | Dado                                           | Quando                              | Então                                                    |
|--------------------------------------------|------------------------------------------------|-------------------------------------|----------------------------------------------------------|
| Criação bem-sucedida                       | Período aberto, aluno sem time na modalidade   | Clica em "Criar"                    | Sistema cria time DRAFT e exibe link de convite          |
| Nome vazio                                 | Campo nome não preenchido                      | Clica em "Criar"                    | Sistema bloqueia e exibe erro                            |
| Aluno já em time da modalidade             | Aluno já participa de time na mesma modalidade | Tenta criar time                    | Sistema bloqueia e exibe erro                            |
| Período de inscrição fechado               | Data atual fora do período de inscrição        | Tenta criar time                    | Sistema bloqueia e exibe mensagem sobre período          |
| Nenhuma temporada ativa                    | Não existe temporada REGISTRATION_OPEN         | Tenta criar time                    | Sistema bloqueia e informa ausência de período           |
| Modalidade inativa                         | Modalidade está inativa                        | Acessa seleção de modalidade        | Sistema não exibe modalidade nas opções                  |
| Token único gerado                         | Time criado com sucesso                        | Verifica `invite_token`             | Sistema gera token único e diferente de outros times     |
| Owner definido automaticamente             | Time criado com sucesso                        | Verifica owner do time              | Sistema define criador como owner                        |
| Owner como primeiro membro                 | Time criado com sucesso                        | Verifica membros do time            | Sistema adiciona owner com role=OWNER                    |
| Atualização de is_athlete                  | Time criado com sucesso                        | Verifica `user.is_athlete`          | Sistema atualiza para `true`                             |
| Link de convite exibido                    | Time criado com sucesso                        | Verifica resposta/interface         | Sistema exibe link compartilhável                        |
| Auditoria de criação                       | Time criado com sucesso                        | Verifica logs de auditoria          | Sistema registra aluno, data/hora e ação                 |

## 10. Artefatos Relacionados
- [UC002 - Abrir Período de Inscrições](UC002_GestaoDeTemporadas_AbrirInscricoes.md)
- [UC004 - Cadastrar Modalidade](UC004_GestaoDeModalidades_CadastrarModalidade.md)
- [UC006 - Entrar em Time via Convite](UC006_GestaoDeEquipes_EntrarViaConvite.md)
- [UC007 - Gerenciar Membros](UC007_GestaoDeEquipes_GerenciarMembros.md)
- [UC008 - Submeter Equipe](UC008_GestaoDeEquipes_SubmeterEquipe.md)