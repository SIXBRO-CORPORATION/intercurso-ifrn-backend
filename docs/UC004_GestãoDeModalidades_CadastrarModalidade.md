# Especificação de Caso de Uso: Cadastrar Modalidade

## 1. Descrição
Este caso de uso permite que o monitor cadastre novas modalidades esportivas no sistema, definindo nome, limites de membros por time e informações adicionais. Modalidades são utilizadas como base para criação de times em temporadas.

## 2. Pré-condições
- O ator deve estar autenticado com permissão de **Monitor**.

## 3. Fluxo Principal: Cadastrar Nova Modalidade
1. O ator acessa o módulo "Gestão de Modalidades";
2. O sistema exibe a listagem de modalidades cadastradas;
3. O ator clica em "Adicionar Modalidade";
4. O sistema exibe o formulário com os campos definidos no Bloco de Dados 1;
5. O ator preenche os campos obrigatórios;
6. O ator confirma o cadastro;
7. O sistema valida os dados conforme Regras de Negócio;
8. O sistema cria a modalidade com status ativo;
9. O sistema exibe mensagem de sucesso e retorna à listagem.

## 4. Fluxos Alternativos

### Fluxo Alternativo 1: Nome Duplicado
1. O ator tenta cadastrar modalidade com nome já existente;
2. O sistema bloqueia a operação e exibe mensagem de erro;
3. O ator retorna ao formulário para corrigir.

### Fluxo Alternativo 2: Limites Inválidos
1. O ator preenche `max_members` menor que `min_members`;
2. O sistema bloqueia a operação e exibe mensagem de erro;
3. O ator retorna ao formulário para corrigir.

### Fluxo Alternativo 3: Mínimo de Membros Inválido
1. O ator tenta definir `min_members` menor que 1;
2. O sistema bloqueia a operação e exibe mensagem de erro;
3. O ator retorna ao formulário para corrigir.

### Fluxo Alternativo 4: Editar Modalidade
1. O ator acessa a listagem de modalidades;
2. Seleciona uma modalidade e clica em "Editar";
3. O sistema exibe os campos permitidos para edição;
4. O ator altera os campos e confirma;
5. O sistema valida e salva as alterações;
6. O sistema exibe mensagem de sucesso.

## 5. Bloco de Dados

### Bloco de Dados 1 – Modalidade

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Nome                     | E             | Nome da modalidade (ex: "Futsal", "Vôlei")            |
| Mínimo de Membros        | E             | Quantidade mínima de jogadores por time (>= 1)        |
| Máximo de Membros        | E             | Quantidade máxima de jogadores por time               |
| Descrição                | E             | Descrição opcional da modalidade                      |
| Ícone                    | E             | URL ou código do ícone (opcional)                     |
| Status                   | S             | Ativo/Inativo                                         |
| Data de Criação          | S             | Data/hora de criação automática                       |
| Última Modificação       | S             | Data/hora e autor da última alteração                 |

## 6. Regras de Negócio
1. O campo **Nome** não pode estar vazio;
2. O campo **Nome** deve ser único no sistema;
3. **Mínimo de Membros** deve ser >= 1;
4. **Máximo de Membros** deve ser >= **Mínimo de Membros**;
5. Modalidade é criada com status **Ativo** por padrão;
6. Limites podem ser atualizados posteriormente (operação rara);
7. Modalidade pode ser inativada, mas não deletada;
8. Modalidades inativas não podem ser selecionadas em novas temporadas;
9. Times já criados com modalidade inativada continuam funcionando;
10. A operação deve ser registrada para auditoria com data/hora e monitor responsável.

## 7. Critérios de Aceitação
- O sistema deve bloquear cadastro com nome duplicado;
- O sistema deve validar que `min_members >= 1`;
- O sistema deve validar que `max_members >= min_members`;
- O sistema deve criar modalidade com status Ativo automaticamente;
- O sistema deve permitir edição de limites de membros;
- O sistema deve permitir inativação de modalidades;
- O sistema deve bloquear uso de modalidades inativas em novas temporadas;
- O sistema deve exibir mensagens claras de sucesso ou erro;
- O sistema deve registrar todas as operações para auditoria.

## 8. Pós-condições
- Nova modalidade é criada no sistema com status Ativo;
- Modalidade fica disponível para seleção em temporadas;
- Operação registrada para auditoria.

## 9. Cenários de Teste

| Cenário                                    | Dado                                           | Quando                              | Então                                                    |
|--------------------------------------------|------------------------------------------------|-------------------------------------|----------------------------------------------------------|
| Cadastro bem-sucedido                      | Nome único, limites válidos                    | Clica em "Salvar"                   | Sistema cria modalidade Ativa e exibe sucesso            |
| Nome duplicado                             | Nome já existe no sistema                      | Clica em "Salvar"                   | Sistema bloqueia e exibe erro                            |
| Mínimo menor que 1                         | `min_members = 0`                              | Clica em "Salvar"                   | Sistema bloqueia e exibe erro                            |
| Máximo menor que mínimo                    | `max_members < min_members`                    | Clica em "Salvar"                   | Sistema bloqueia e exibe erro                            |
| Edição de limites                          | Modalidade existente                           | Altera `min_members` e confirma     | Sistema atualiza limites e exibe sucesso                 |
| Inativação de modalidade                   | Modalidade ativa no sistema                    | Clica em "Inativar"                 | Sistema inativa e bloqueia uso em novas temporadas       |
| Uso de modalidade inativa                  | Modalidade inativa, criando temporada          | Tenta selecionar modalidade         | Sistema não exibe modalidade nas opções                  |
| Times existentes após inativação           | Modalidade inativa com times já criados        | Acessa times da modalidade          | Times continuam funcionando normalmente                  |
| Auditoria de cadastro                      | Modalidade cadastrada com sucesso              | Verifica logs de auditoria          | Sistema registra monitor, data/hora e ação               |
| Auditoria de edição                        | Limites atualizados                            | Verifica logs de auditoria          | Sistema registra monitor, data/hora e alterações         |

## 10. Artefatos Relacionados
- [UC001 - Criar Temporada](UC001_GestaoDeTemporadas_CriarTemporada.md)
- [UC005 - Criar Equipe](UC005_GestaoDeEquipes_CriarEquipe.md)