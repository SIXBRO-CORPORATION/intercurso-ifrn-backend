# Especificação de Caso de Uso: Criar Temporada

## 1. Descrição
Este caso de uso permite que o monitor crie uma nova temporada (edição anual do Intercurso), definindo nome, ano de referência e modalidades que estarão disponíveis para inscrição de times.

## 2. Pré-condições
- O ator deve estar autenticado com permissão de **Monitor**;
- Devem existir modalidades previamente cadastradas e ativas no sistema.

## 3. Fluxo Principal: Criar Nova Temporada
1. O ator acessa o módulo "Gestão de Temporadas";
2. O sistema exibe a listagem de temporadas cadastradas;
3. O ator clica em "Criar Temporada";
4. O sistema exibe o formulário com os campos definidos no Bloco de Dados 1;
5. O ator preenche os campos obrigatórios e seleciona as modalidades;
6. O ator confirma a criação;
7. O sistema valida os dados conforme Regras de Negócio;
8. O sistema cria a temporada com status DRAFT e `is_active = false` se já existir outra temporada ativa;
9. O sistema exibe mensagem de sucesso e retorna à listagem.

## 4. Fluxos Alternativos

### Fluxo Alternativo 1: Validação de Modalidades
1. O ator tenta criar temporada sem selecionar modalidades;
2. O sistema bloqueia a criação e exibe mensagem de erro;
3. O ator retorna ao formulário para corrigir.

### Fluxo Alternativo 2: Temporada Ativa Existente
1. O ator cria nova temporada quando já existe uma temporada ativa;
2. O sistema cria a temporada com `is_active = false`;
3. O sistema exibe aviso informando que existe outra temporada ativa;
4. O sistema exibe mensagem de sucesso.

### Fluxo Alternativo 3: Ano Anterior ao Atual
1. O ator tenta criar temporada com ano menor que o ano atual;
2. O sistema bloqueia a criação e exibe mensagem de erro;
3. O ator retorna ao formulário para corrigir.

## 5. Bloco de Dados

### Bloco de Dados 1 – Temporada

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Nome                     | E             | Ex: "Intercurso 2025/26"                              |
| Ano                      | E             | Ano de referência (numérico, >= ano atual)            |
| Modalidades              | E             | Lista de modalidades selecionadas                     |
| Status                   | S             | DRAFT, REGISTRATION_OPEN, IN_PROGRESS, FINISHED       |
| Ativa                    | S             | Indica se é a temporada ativa (booleano)              |
| Data de Criação          | S             | Data/hora de criação automática                       |
| Última Modificação       | S             | Data/hora e autor da última alteração 

## 6. Regras de Negócio
1. O campo **Nome** não pode estar vazio;
2. O campo **Ano** deve ser maior ou igual ao ano atual;
3. Ao menos uma **Modalidade** deve ser selecionada;
4. Todas as modalidades selecionadas devem estar ativas no sistema;
5. Apenas uma temporada pode ter `is_active = true` por vez;
6. Se já existe temporada ativa, a nova temporada é criada com `is_active = false`;
7. Status inicial é sempre **DRAFT**;
8. A criação deve ser registrada para auditoria com data/hora e monitor responsável;
9. Nome da temporada não precisa ser único.

## 7. Critérios de Aceitação
- O sistema deve bloquear criação sem nome ou ano inválido;
- O sistema deve bloquear criação sem modalidades selecionadas;
- O sistema deve validar que modalidades existem e estão ativas;
- O sistema deve criar temporada com status DRAFT automaticamente;
- O sistema deve gerenciar corretamente a flag `is_active`;
- O sistema deve exibir mensagens claras de sucesso ou erro;
- O sistema deve registrar a operação para auditoria.

## 8. Pós-condições
- Nova temporada é criada no sistema com status DRAFT;
- Temporada fica vinculada às modalidades selecionadas;
- Sistema mantém apenas uma temporada ativa por vez;
- Operação registrada para auditoria.

## 9. Cenários de Teste

| Cenário                                    | Dado                                           | Quando                              | Então                                                    |
|--------------------------------------------|------------------------------------------------|-------------------------------------|----------------------------------------------------------|
| Criação bem-sucedida                       | Nome, ano válido e modalidades selecionadas    | Clica em "Criar"                    | Sistema cria temporada DRAFT e exibe sucesso             |
| Criação sem nome                           | Campo nome vazio                               | Clica em "Criar"                    | Sistema bloqueia e exibe erro                            |
| Criação com ano inválido                   | Ano menor que o atual                          | Clica em "Criar"                    | Sistema bloqueia e exibe erro                            |
| Criação sem modalidades                    | Nenhuma modalidade selecionada                 | Clica em "Criar"                    | Sistema bloqueia e exibe erro                            |
| Criação com modalidade inativa             | Modalidade inativa selecionada                 | Clica em "Criar"                    | Sistema bloqueia e exibe erro                            |
| Criação com temporada ativa existente      | Já existe temporada com `is_active = true`     | Clica em "Criar"                    | Sistema cria com `is_active = false` e exibe aviso       |
| Criação sendo primeira temporada           | Nenhuma temporada ativa no sistema             | Clica em "Criar"                    | Sistema cria e pode definir como ativa se necessário     |
| Auditoria de criação                       | Temporada criada com sucesso                   | Verifica logs de auditoria          | Sistema registra monitor, data/hora e ação               |

## 10. Artefatos Relacionados
- [UC002 - Abrir Período de Inscrições](UC002_GestaoDeTemporadas_AbrirInscricoes.md)
- [UC003 - Finalizar Temporada](UC003_GestaoDeTemporadas_FinalizarTemporada.md)
- [UC004 - Cadastrar Modalidade](UC004_GestaoDeModalidades_CadastrarModalidade.md)