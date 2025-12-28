# Especificação de Caso de Uso: Submeter Equipe

## 1. Descrição
Este caso de uso permite que o dono (owner) de um time submeta sua equipe para aprovação do monitor quando tiver o número mínimo de membros necessário. Após a submissão, o time não aceita mais novos membros e aguarda a confirmação das doações e aprovação do monitor.

## 2. Pré-condições
- O ator deve estar autenticado como **Aluno**;
- O ator deve ser o dono (owner) do time;
- Time deve estar em status **DRAFT**;
- A temporada deve estar em **REGISTRATION_OPEN**;
- Data atual deve estar dentro do período de inscrição;
- Time deve ter ao menos o número mínimo de membros definido pela modalidade.

## 3. Fluxo Principal: Submeter Time para Aprovação
1. O owner acessa a página de detalhes do seu time;
2. O sistema exibe informações do time e seus membros;
3. O sistema verifica se time atende requisitos mínimos;
4. O owner clica em "Submeter para Aprovação";
5. O sistema exibe confirmação com resumo dos membros;
6. O owner confirma a submissão;
7. O sistema valida os dados conforme Regras de Negócio;
8. O sistema atualiza status do time para PENDING_APPROVAL;
9. O sistema define `invite_active = false`;
10. O sistema define `submitted_at = now()`;
11. O sistema atualiza `donation_status` de todos os membros para PENDING_DONATION (se ainda não estiver);
12. O sistema exibe mensagem de sucesso informando próximos passos.

## 4. Fluxos Alternativos

### Fluxo Alternativo 1: Time Sem Número Mínimo de Membros
1. O owner acessa time com menos membros que o mínimo;
2. O sistema exibe botão "Submeter" desabilitado;
3. O sistema exibe mensagem informando quantos membros faltam;
4. Owner não consegue submeter até atingir mínimo.

### Fluxo Alternativo 2: Fora do Período de Inscrição
1. O owner tenta submeter fora do período de inscrição;
2. O sistema bloqueia a operação e exibe mensagem de erro;
3. Sistema informa que período de inscrição está fechado.

### Fluxo Alternativo 3: Time Já Submetido
1. O owner tenta submeter time que já está em PENDING_APPROVAL ou outro status;
2. O sistema bloqueia a operação e exibe mensagem de erro;
3. Sistema informa status atual do time.

### Fluxo Alternativo 4: Temporada Não em REGISTRATION_OPEN
1. O owner tenta submeter quando temporada não está aberta para inscrições;
2. O sistema bloqueia a operação e exibe mensagem de erro;
3. Sistema informa que inscrições não estão abertas.

### Fluxo Alternativo 5: Cancelar Submissão
1. Owner clica em "Submeter para Aprovação";
2. Sistema exibe modal de confirmação;
3. Owner clica em "Cancelar";
4. Sistema fecha modal sem realizar alterações.

## 5. Bloco de Dados

### Bloco de Dados 1 – Time para Submissão

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Nome do Time             | S             | Nome do time                                          |
| Modalidade               | S             | Modalidade do time                                    |
| Membros Atuais           | S             | Quantidade de membros                                 |
| Mínimo Necessário        | S             | Mínimo de membros da modalidade                       |
| Capitão                  | S             | Nome do capitão (se definido)                         |
| Lista de Membros         | S             | Nomes de todos os membros para confirmação            |

### Bloco de Dados 2 – Time Submetido

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Status                   | S             | Atualizado de DRAFT para PENDING_APPROVAL             |
| Convite Ativo            | S             | Atualizado para `false`                               |
| Data de Submissão        | S             | Timestamp automático da submissão                     |
| Status Doação Membros    | S             | Todos membros com PENDING_DONATION                    |

## 6. Regras de Negócio
1. Apenas **owner** pode submeter o time;
2. Time deve estar em status **DRAFT**;
3. Temporada deve estar em **REGISTRATION_OPEN**;
4. Data atual deve estar dentro do período de inscrição (`registration_start_date` a `registration_end_date`);
5. Quantidade de membros deve ser >= `min_members` da modalidade;
6. Ao submeter, status muda automaticamente para **PENDING_APPROVAL**;
7. `invite_active` é definido como `false` (convite desativado);
8. `submitted_at` é preenchido com timestamp da submissão;
9. Todos os membros recebem `donation_status = PENDING_DONATION` (se ainda não estiver);
10. Após submissão, apenas monitor pode modificar membros;
11. Time submetido aguarda confirmação de doações e aprovação do monitor;
12. A operação deve ser registrada para auditoria;
13. Notificação ao monitor deve ser enviada (escopo futuro).

## 7. Critérios de Aceitação
- O sistema deve bloquear submissão se time não tiver mínimo de membros;
- O sistema deve bloquear submissão fora do período de inscrição;
- O sistema deve bloquear submissão se temporada não estiver em REGISTRATION_OPEN;
- O sistema deve bloquear submissão se time não estiver em DRAFT;
- O sistema deve atualizar status para PENDING_APPROVAL automaticamente;
- O sistema deve desativar convite (`invite_active = false`);
- O sistema deve registrar data/hora da submissão;
- O sistema deve atualizar donation_status de todos os membros;
- O sistema deve exibir mensagens claras de sucesso ou erro;
- O sistema deve registrar a operação para auditoria;
- O sistema deve exibir próximos passos ao owner após submissão.

## 8. Pós-condições
- Time tem status atualizado para PENDING_APPROVAL;
- Convite desativado (`invite_active = false`);
- Data de submissão registrada;
- Todos os membros com `donation_status = PENDING_DONATION`;
- Novos membros não podem entrar no time;
- Owner não pode mais remover membros;
- Time aguarda aprovação do monitor;
- Operação registrada para auditoria.

## 9. Cenários de Teste

| Cenário                                    | Dado                                           | Quando                              | Então                                                    |
|--------------------------------------------|------------------------------------------------|-------------------------------------|----------------------------------------------------------|
| Submissão bem-sucedida                     | Time DRAFT, >= min_members, período aberto     | Clica em "Submeter"                 | Sistema atualiza para PENDING_APPROVAL e exibe sucesso   |
| Time com menos que mínimo                  | Time com 3 membros, mínimo = 5                 | Acessa página do time               | Sistema exibe botão desabilitado e quantidade faltante   |
| Fora do período de inscrição               | Data atual fora do período                     | Clica em "Submeter"                 | Sistema bloqueia e exibe erro                            |
| Time já submetido                          | Time com status PENDING_APPROVAL               | Tenta submeter novamente            | Sistema bloqueia e exibe erro                            |
| Temporada não aberta                       | Temporada em DRAFT ou FINISHED                 | Clica em "Submeter"                 | Sistema bloqueia e exibe erro                            |
| Convite desativado após submissão          | Time submetido com sucesso                     | Verifica `invite_active`            | Sistema define como `false`                              |
| Data de submissão registrada               | Time submetido com sucesso                     | Verifica `submitted_at`             | Sistema registra timestamp da submissão                  |
| Status de doação atualizado                | Time submetido com sucesso                     | Verifica membros                    | Todos com `donation_status = PENDING_DONATION`           |
| Cancelamento de submissão                  | Modal de confirmação aberto                    | Clica em "Cancelar"                 | Sistema fecha modal sem alterações                       |
| Bloqueio de novos membros                  | Time submetido, link de convite acessado       | Tenta entrar via convite            | Sistema bloqueia entrada                                 |
| Bloqueio de remoção de membros             | Time submetido, owner tenta remover membro     | Clica em "Remover"                  | Sistema bloqueia operação                                |
| Não-owner tenta submeter                   | Membro comum tenta submeter                    | Acessa opção de submeter            | Sistema não exibe opção ou bloqueia                      |
| Auditoria de submissão                     | Time submetido com sucesso                     | Verifica logs de auditoria          | Sistema registra owner, data/hora e ação                 |

## 10. Artefatos Relacionados
- [UC002 - Abrir Período de Inscrições](UC002_GestaoDeTemporadas_AbrirInscricoes.md)
- [UC005 - Criar Equipe](UC005_GestaoDeEquipes_CriarEquipe.md)
- [UC006 - Entrar em Time via Convite](UC006_GestaoDeEquipes_EntrarViaConvite.md)
- [UC007 - Gerenciar Membros](UC007_GestaoDeEquipes_GerenciarMembros.md)
- [UC009 - Aprovar Equipes](UC009_GestaoDeEquipes_AprovarEquipes.md)
- [UC010 - Confirmar Doações](UC010_GestaoDeEquipes_ConfirmarDoacoes.md)