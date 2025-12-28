# Especificação de Caso de Uso: Finalizar Temporada

## 1. Descrição
Este caso de uso permite que o monitor finalize uma temporada em andamento, encerrando todas as atividades relacionadas. A operação requer confirmação digitando o nome completo da temporada para evitar finalizações acidentais.

## 2. Pré-condições
- O ator deve estar autenticado com permissão de **Monitor**;
- Deve existir uma temporada com status **IN_PROGRESS**;
- Todos os jogos da temporada devem estar finalizados (validação futura).

## 3. Fluxo Principal: Finalizar Temporada
1. O ator acessa o módulo "Gestão de Temporadas";
2. O sistema exibe a listagem de temporadas cadastradas;
3. O ator seleciona uma temporada com status IN_PROGRESS;
4. O ator clica em "Finalizar Temporada";
5. O sistema exibe modal de confirmação solicitando que o ator digite o nome completo da temporada;
6. O ator digita o nome da temporada e confirma;
7. O sistema valida os dados conforme Regras de Negócio;
8. O sistema atualiza a temporada para status FINISHED;
9. O sistema desativa todos os convites de times relacionados à temporada;
10. O sistema exibe mensagem de sucesso.

## 4. Fluxos Alternativos

### Fluxo Alternativo 1: Nome de Confirmação Incorreto
1. O ator digita nome diferente do nome da temporada;
2. O sistema bloqueia a operação e exibe mensagem de erro;
3. O ator retorna ao modal para corrigir ou cancelar.

### Fluxo Alternativo 2: Temporada Não Está em IN_PROGRESS
1. O ator tenta finalizar temporada que não está em IN_PROGRESS;
2. O sistema bloqueia a operação e exibe mensagem de erro;
3. O sistema mantém o status atual da temporada.

### Fluxo Alternativo 3: Jogos Não Finalizados (Validação Futura)
1. O ator tenta finalizar temporada com jogos pendentes;
2. O sistema bloqueia a operação e exibe lista de jogos não finalizados;
3. O ator deve finalizar os jogos antes de prosseguir.

### Fluxo Alternativo 4: Cancelar Finalização
1. O ator clica em "Finalizar Temporada";
2. O sistema exibe modal de confirmação;
3. O ator clica em "Cancelar";
4. O sistema fecha o modal sem realizar alterações.

## 5. Bloco de Dados

### Bloco de Dados 1 – Finalização de Temporada

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Nome de Confirmação      | E             | Deve corresponder exatamente ao nome da temporada     |
| Status                   | S             | Atualizado de IN_PROGRESS para FINISHED               |
| Data de Finalização      | S             | Data/hora automática da finalização                   |
| Última Modificação       | S             | Data/hora e autor da alteração                        |

## 6. Regras de Negócio
1. Temporada deve estar em status **IN_PROGRESS**;
2. Nome de confirmação deve corresponder **exatamente** ao nome da temporada (case-sensitive);
3. Todos os jogos da temporada devem estar finalizados (regra futura);
4. Ao finalizar, status muda automaticamente para **FINISHED**;
5. Todos os convites de times relacionados à temporada são desativados (`invite_active = false`);
6. Temporada finalizada não pode ter seu status alterado novamente;
7. A operação deve ser registrada para auditoria com data/hora e monitor responsável;
8. Apenas monitor pode finalizar temporada.

## 7. Critérios de Aceitação
- O sistema deve bloquear finalização se temporada não estiver em IN_PROGRESS;
- O sistema deve validar correspondência exata do nome de confirmação;
- O sistema deve bloquear finalização se existirem jogos não finalizados (futuro);
- O sistema deve desativar todos os convites de times ao finalizar;
- O sistema deve atualizar status para FINISHED automaticamente;
- O sistema deve exibir mensagens claras de sucesso ou erro;
- O sistema deve registrar a operação para auditoria;
- O sistema não deve permitir reversão após finalização.

## 8. Pós-condições
- Temporada tem status atualizado para FINISHED;
- Todos os convites de times desativados;
- Nenhuma alteração adicional é permitida na temporada;
- Operação registrada para auditoria.

## 9. Cenários de Teste

| Cenário                                    | Dado                                           | Quando                              | Então                                                    |
|--------------------------------------------|------------------------------------------------|-------------------------------------|----------------------------------------------------------|
| Finalização bem-sucedida                   | Temporada IN_PROGRESS, nome correto digitado   | Clica em "Confirmar"                | Sistema finaliza temporada e exibe sucesso               |
| Nome de confirmação incorreto              | Nome digitado diferente do nome da temporada   | Clica em "Confirmar"                | Sistema bloqueia e exibe erro                            |
| Temporada não está em IN_PROGRESS          | Temporada com status DRAFT                     | Clica em "Finalizar"                | Sistema bloqueia e exibe erro                            |
| Jogos não finalizados (futuro)             | Temporada IN_PROGRESS com jogos pendentes      | Clica em "Finalizar"                | Sistema bloqueia e lista jogos pendentes                 |
| Cancelamento de finalização                | Modal de confirmação aberto                    | Clica em "Cancelar"                 | Sistema fecha modal sem alterações                       |
| Desativação de convites                    | Temporada finalizada com sucesso               | Verifica convites dos times         | Todos os convites ficam com `invite_active = false`      |
| Tentativa de edição após finalização       | Temporada com status FINISHED                  | Tenta alterar qualquer campo        | Sistema bloqueia alteração                               |
| Auditoria de finalização                   | Temporada finalizada com sucesso               | Verifica logs de auditoria          | Sistema registra monitor, data/hora e ação               |

## 10. Artefatos Relacionados
- [UC001 - Criar Temporada](UC001_GestaoDeTemporadas_CriarTemporada.md)
- [UC002 - Abrir Período de Inscrições](UC002_GestaoDeTemporadas_AbrirInscricoes.md)