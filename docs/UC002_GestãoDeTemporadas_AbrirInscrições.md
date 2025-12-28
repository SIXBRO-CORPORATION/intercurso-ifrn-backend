# Especificação de Caso de Uso: Abrir Período de Inscrições

## 1. Descrição
Este caso de uso permite que o monitor abra o período de inscrições de uma temporada, definindo data de início e término para que alunos possam criar e submeter times para aprovação.

## 2. Pré-condições
- O ator deve estar autenticado com permissão de **Monitor**;
- Deve existir uma temporada cadastrada com status **DRAFT**.

## 3. Fluxo Principal: Abrir Período de Inscrições
1. O ator acessa o módulo "Gestão de Temporadas";
2. O sistema exibe a listagem de temporadas cadastradas;
3. O ator seleciona uma temporada com status DRAFT;
4. O ator clica em "Abrir Inscrições";
5. O sistema exibe o formulário com os campos definidos no Bloco de Dados 1;
6. O ator preenche as datas de início e término do período de inscrição;
7. O ator confirma a operação;
8. O sistema valida os dados conforme Regras de Negócio;
9. O sistema atualiza a temporada com as datas e altera status para REGISTRATION_OPEN;
10. O sistema exibe mensagem de sucesso.

## 4. Fluxos Alternativos

### Fluxo Alternativo 1: Data de Término Anterior à Data de Início
1. O ator preenche data de término anterior à data de início;
2. O sistema bloqueia a operação e exibe mensagem de erro;
3. O ator retorna ao formulário para corrigir.

### Fluxo Alternativo 2: Período no Passado
1. O ator tenta definir período com datas no passado;
2. O sistema bloqueia a operação e exibe mensagem de erro;
3. O ator retorna ao formulário para corrigir.

### Fluxo Alternativo 3: Temporada Não Está em DRAFT
1. O ator tenta abrir inscrições de temporada que não está em DRAFT;
2. O sistema bloqueia a operação e exibe mensagem de erro;
3. O sistema mantém o status atual da temporada.

## 5. Bloco de Dados

### Bloco de Dados 1 – Período de Inscrição

| Campo                           | Entrada/Saída | Observações                                    |
|---------------------------------|---------------|------------------------------------------------|
| Data de Início das Inscrições   | E             | Data/hora de início (deve ser futura)          |
| Data de Término das Inscrições  | E             | Data/hora de término (deve ser > início)       |
| Status                          | S             | Atualizado de DRAFT para REGISTRATION_OPEN     |
| Última Modificação              | S             | Data/hora e autor da alteração                 |

## 6. Regras de Negócio
1. Temporada deve estar em status **DRAFT**;
2. **Data de Término** deve ser posterior à **Data de Início**;
3. Período deve ser no futuro (data de início >= data/hora atual);
4. Ao abrir inscrições, status muda automaticamente para **REGISTRATION_OPEN**;
5. Durante período de inscrição, alunos podem criar e submeter times;
6. A operação deve ser registrada para auditoria com data/hora e monitor responsável;
7. Apenas monitor pode abrir período de inscrições.

## 7. Critérios de Aceitação
- O sistema deve bloquear abertura se temporada não estiver em DRAFT;
- O sistema deve validar que data de término é posterior à data de início;
- O sistema deve validar que período é no futuro;
- O sistema deve atualizar status para REGISTRATION_OPEN automaticamente;
- O sistema deve armazenar as datas de início e término corretamente;
- O sistema deve exibir mensagens claras de sucesso ou erro;
- O sistema deve registrar a operação para auditoria.

## 8. Pós-condições
- Temporada tem status atualizado para REGISTRATION_OPEN;
- Datas de início e término de inscrição definidas;
- Alunos podem criar e submeter times durante o período;
- Operação registrada para auditoria.

## 9. Cenários de Teste

| Cenário                                    | Dado                                           | Quando                              | Então                                                    |
|--------------------------------------------|------------------------------------------------|-------------------------------------|----------------------------------------------------------|
| Abertura bem-sucedida                      | Temporada DRAFT, datas válidas futuras         | Clica em "Abrir Inscrições"         | Sistema atualiza para REGISTRATION_OPEN e exibe sucesso  |
| Data término antes do início               | Data término < data início                     | Clica em "Abrir Inscrições"         | Sistema bloqueia e exibe erro                            |
| Período no passado                         | Datas no passado                               | Clica em "Abrir Inscrições"         | Sistema bloqueia e exibe erro                            |
| Temporada não está em DRAFT                | Temporada com status IN_PROGRESS               | Clica em "Abrir Inscrições"         | Sistema bloqueia e exibe erro                            |
| Temporada já com período aberto            | Temporada com status REGISTRATION_OPEN         | Clica em "Abrir Inscrições"         | Sistema bloqueia e exibe erro                            |
| Auditoria de abertura                      | Período aberto com sucesso                     | Verifica logs de auditoria          | Sistema registra monitor, data/hora e ação               |

## 10. Artefatos Relacionados
- [UC001 - Criar Temporada](UC001_GestaoDeTemporadas_CriarTemporada.md)
- [UC003 - Finalizar Temporada](UC003_GestaoDeTemporadas_FinalizarTemporada.md)
- [UC005 - Criar Equipe](UC005_GestaoDeEquipes_CriarEquipe.md)
- [UC008 - Submeter Equipe](UC008_GestaoDeEquipes_SubmeterEquipe.md)