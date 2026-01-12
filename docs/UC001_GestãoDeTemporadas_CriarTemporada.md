# Especificação de Caso de Uso: Criar Temporada

## 1. Descrição
Este caso de uso permite que o monitor crie uma nova temporada (edição anual do Intercurso), definindo nome, ano de referência, modalidades e datas de abertura/encerramento das inscrições. O sistema gerencia automaticamente as transições de status baseado nas datas definidas.

## 2. Pré-condições
- O ator deve estar autenticado com permissão de **Monitor**;
- Devem existir modalidades previamente cadastradas e ativas no sistema.

## 3. Fluxo Principal: Criar Nova Temporada
1. O ator acessa o módulo "Gestão de Temporadas";
2. O sistema exibe a listagem de temporadas cadastradas;
3. O ator clica em "Criar Temporada";
4. O sistema exibe o formulário com os campos definidos no Bloco de Dados 1;
5. O ator preenche os campos obrigatórios, seleciona modalidades e define datas;
6. O ator confirma a criação;
7. O sistema valida os dados conforme Regras de Negócio;
8. O sistema cria a temporada com status DRAFT e `is_active = false`;
9. O sistema agenda jobs automáticos para abertura e encerramento;
10. O sistema exibe mensagem de sucesso com resumo das datas agendadas;
11. O sistema retorna à listagem.

## 4. Fluxos Alternativos

### Fluxo Alternativo 1: Validação de Modalidades
1. O ator tenta criar temporada sem selecionar modalidades;
2. O sistema bloqueia a criação e exibe mensagem de erro;
3. O ator retorna ao formulário para corrigir.

### Fluxo Alternativo 2: Abertura Imediata
1. O ator seleciona "Abrir inscrições imediatamente" (checkbox);
2. O sistema desabilita campo de data de abertura;
3. O sistema define data de abertura = agora;
4. Ao criar, sistema muda status para REGISTRATION_OPEN automaticamente;
5. O sistema define `is_active = true` e desativa outras temporadas;
6. O sistema envia notificação aos alunos: "🎉 Inscrições abertas!";
7. O sistema exibe mensagem de sucesso.

### Fluxo Alternativo 3: Ano Anterior ao Atual
1. O ator tenta criar temporada com ano menor que o ano atual;
2. O sistema bloqueia a criação e exibe mensagem de erro;
3. O ator retorna ao formulário para corrigir.

### Fluxo Alternativo 4: Data de Encerramento Inválida
1. O ator define data de encerramento <= data de abertura;
2. O sistema bloqueia a criação e exibe mensagem de erro;
3. O ator retorna ao formulário para corrigir.

### Fluxo Alternativo 5: Editar Datas Antes da Abertura
1. Monitor acessa temporada em status DRAFT;
2. Monitor clica em "Editar Datas";
3. Sistema exibe formulário com datas atuais;
4. Monitor altera datas e confirma;
5. Sistema valida e atualiza agendamentos;
6. Sistema exibe mensagem de sucesso.

## 5. Bloco de Dados

### Bloco de Dados 1 – Temporada

| Campo                           | Entrada/Saída | Observações                                           |
|---------------------------------|---------------|-------------------------------------------------------|
| Nome                            | E             | Ex: "Intercurso 2025/26"                              |
| Ano                             | E             | Ano de referência (numérico, >= ano atual)            |
| Modalidades                     | E             | Lista de modalidades selecionadas                     |
| Data/Hora Abertura Inscrições   | E             | Quando sistema abrirá automaticamente (>= agora)      |
| Data/Hora Encerramento Inscrições | E           | Quando sistema encerrará automaticamente (> abertura) |
| Abrir Imediatamente             | E             | Checkbox opcional para abertura instantânea           |
| Regulamento (PDF)               | E             | Arquivo PDF opcional com regras gerais do Intercurso  |
| Status                          | S             | DRAFT, REGISTRATION_OPEN, REGISTRATION_CLOSED, IN_PROGRESS, FINISHED |
| Ativa                           | S             | Indica se é a temporada ativa (booleano)              |
| Data de Criação                 | S             | Data/hora de criação automática                       |
| Última Modificação              | S             | Data/hora e autor da última alteração                 |

## 6. Regras de Negócio
1. O campo **Nome** não pode estar vazio;
2. O campo **Ano** deve ser maior ou igual ao ano atual;
3. Ao menos uma **Modalidade** deve ser selecionada;
4. Todas as modalidades selecionadas devem estar ativas no sistema;
5. **Data de Abertura** deve ser maior ou igual à data/hora atual;
6. **Data de Encerramento** deve ser maior que data de abertura;
7. Sistema agenda job para mudar status automaticamente nas datas definidas;
8. Monitor pode editar datas enquanto status = DRAFT (antes da abertura);
9. Status inicial é sempre **DRAFT** (exceto se "Abrir Imediatamente" for marcado);
10. Apenas uma temporada pode ter `is_active = true` por vez;
11. **Abertura Automática (Job Agendado):**
    - Sistema verifica temporadas DRAFT periodicamente (ex: a cada minuto);
    - Quando `registration_start_date` <= agora:
      - Status: DRAFT → REGISTRATION_OPEN;
      - `is_active` = true (e desativa todas outras temporadas);
      - Notificação push enviada aos alunos;
      - Operação registrada em auditoria como "Sistema Automático";
12. **Encerramento Automático (Job Agendado):**
    - Sistema verifica temporadas REGISTRATION_OPEN periodicamente;
    - Quando `registration_end_date` <= agora:
      - Status: REGISTRATION_OPEN → REGISTRATION_CLOSED;
      - `registration_closed_at` = agora;
      - Notificação enviada aos monitores;
      - Operação registrada em auditoria como "Sistema Automático";
13. A criação deve ser registrada para auditoria com data/hora e monitor responsável;
14. Nome da temporada não precisa ser único.

## 7. Critérios de Aceitação
- O sistema deve bloquear criação sem nome ou ano inválido;
- O sistema deve bloquear criação sem modalidades selecionadas;
- O sistema deve validar que modalidades existem e estão ativas;
- O sistema deve validar que data de abertura >= agora;
- O sistema deve validar que data de encerramento > data de abertura;
- O sistema deve criar temporada com status DRAFT automaticamente;
- O sistema deve agendar abertura e encerramento automáticos;
- O sistema deve permitir "Abrir Imediatamente" (status REGISTRATION_OPEN);
- O sistema deve gerenciar corretamente a flag `is_active`;
- O sistema deve permitir edição de datas antes da abertura;
- O sistema deve exibir mensagens claras de sucesso ou erro;
- O sistema deve registrar a operação para auditoria;
- O sistema deve enviar notificações aos alunos na abertura;
- O sistema deve enviar notificações aos monitores no encerramento.

## 8. Pós-condições
- Nova temporada é criada no sistema com status DRAFT ou REGISTRATION_OPEN;
- Temporada fica vinculada às modalidades selecionadas;
- Jobs agendados para abertura e encerramento automáticos;
- Sistema mantém apenas uma temporada ativa por vez;
- Operação registrada para auditoria;
- Se abertura imediata: notificações enviadas aos alunos.

## 9. Cenários de Teste

| Cenário                                    | Dado                                           | Quando                              | Então                                                    |
|--------------------------------------------|------------------------------------------------|-------------------------------------|----------------------------------------------------------|
| Criação bem-sucedida                       | Nome, ano válido, modalidades e datas válidas  | Clica em "Criar"                    | Sistema cria temporada DRAFT e agenda abertura           |
| Criação com abertura imediata              | Checkbox "Abrir Imediatamente" marcado         | Clica em "Criar"                    | Sistema cria com status REGISTRATION_OPEN e is_active=true |
| Criação sem nome                           | Campo nome vazio                               | Clica em "Criar"                    | Sistema bloqueia e exibe erro                            |
| Criação com ano inválido                   | Ano menor que o atual                          | Clica em "Criar"                    | Sistema bloqueia e exibe erro                            |
| Criação sem modalidades                    | Nenhuma modalidade selecionada                 | Clica em "Criar"                    | Sistema bloqueia e exibe erro                            |
| Data de abertura no passado                | Data de abertura < agora                       | Clica em "Criar"                    | Sistema bloqueia e exibe erro                            |
| Data de encerramento antes da abertura     | Data encerramento <= data abertura             | Clica em "Criar"                    | Sistema bloqueia e exibe erro                            |
| Abertura automática (Job)                  | Temporada DRAFT com data de abertura chegando  | Job executa                         | Sistema muda para REGISTRATION_OPEN e ativa temporada    |
| Encerramento automático (Job)              | Temporada OPEN com data de encerramento        | Job executa                         | Sistema muda para REGISTRATION_CLOSED                    |
| Editar datas antes da abertura             | Temporada DRAFT, clica "Editar Datas"          | Altera e confirma                   | Sistema atualiza datas e reagenda jobs                   |
| Tentar editar após abertura                | Temporada REGISTRATION_OPEN                    | Tenta editar datas                  | Sistema bloqueia edição de data de abertura              |
| Notificação de abertura                    | Job abre inscrições automaticamente            | Abertura ocorre                     | Alunos recebem push notification                         |
| Notificação de encerramento                | Job encerra inscrições automaticamente         | Encerramento ocorre                 | Monitores recebem notificação                            |
| Auditoria de criação                       | Temporada criada com sucesso                   | Verifica logs de auditoria          | Sistema registra monitor, data/hora e ação               |
| Auditoria de abertura automática           | Job abre inscrições                            | Verifica logs                       | Sistema registra "Sistema Automático" e timestamp        |

## 10. Artefatos Relacionados
- [UC002 - Gerenciar Temporada](UC002_GestaoDeTemporadas_GerenciarTemporada.md) (renomeado)
- [UC003 - Finalizar Temporada](UC003_GestaoDeTemporadas_FinalizarTemporada.md)
- [UC004 - Cadastrar Modalidade](UC004_GestaoDeModalidades_CadastrarModalidade.md)
- [UC011 - Criar Chaveamento](UC011_GestaoDeChaveamento_CriarChaveamento.md)