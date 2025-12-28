# Especificação de Caso de Uso: Criar Chaveamento

## 1. Descrição
Este caso de uso permite que o monitor crie o chaveamento de uma modalidade após o encerramento do período de inscrições, definindo o formato da competição, realizando o sorteio dos times e gerando automaticamente todas as partidas do campeonato.

## 2. Pré-condições
- O ator deve estar autenticado com permissão de **Monitor**;
- Deve existir uma temporada com status **IN_PROGRESS**;
- Período de inscrição deve ter encerrado;
- Deve existir ao menos uma modalidade com times aprovados;
- Não deve existir chaveamento ativo para a modalidade selecionada.

## 3. Fluxo Principal: Criar Chaveamento
1. O monitor acessa o módulo "Gestão de Chaveamentos";
2. O sistema exibe lista de modalidades da temporada ativa;
3. O monitor seleciona uma modalidade;
4. O sistema exibe quantidade de times aprovados na modalidade;
5. O sistema exibe opções de formato conforme Bloco de Dados 1;
6. O monitor seleciona o formato desejado;
7. O sistema gera configuração sugerida baseada no número de times;
8. O monitor revisa a configuração e clica em "Sortear";
9. O sistema valida os dados conforme Regras de Negócio;
10. O sistema cria o Bracket com status ACTIVE;
11. O sistema cria BracketGroups conforme formato escolhido;
12. O sistema sorteia times aleatoriamente e distribui nos grupos/chaves;
13. O sistema cria todas as partidas com status SCHEDULED e times TBD nas fases avançadas;
14. O sistema exibe mensagem de sucesso e apresenta o chaveamento gerado.

## 4. Fluxos Alternativos

### Fluxo Alternativo 1: Menos de 2 Times Aprovados
1. O monitor seleciona modalidade com menos de 2 times aprovados;
2. O sistema bloqueia a criação e exibe mensagem de erro;
3. O sistema informa quantidade mínima necessária.

### Fluxo Alternativo 2: Chaveamento Já Existe
1. O monitor tenta criar chaveamento para modalidade que já possui bracket ativo;
2. O sistema bloqueia a operação e exibe mensagem de erro;
3. O sistema informa que já existe chaveamento criado.

### Fluxo Alternativo 3: Ajustar Configuração Antes de Sortear
1. O monitor visualiza configuração sugerida pelo sistema;
2. O monitor ajusta parâmetros (número de grupos, times por grupo, etc);
3. O sistema valida nova configuração;
4. O monitor confirma e prossegue com sorteio.

### Fluxo Alternativo 4: Cancelar Criação
1. Monitor está na tela de configuração do chaveamento;
2. Monitor clica em "Cancelar";
3. Sistema descarta configurações e retorna à listagem de modalidades.

## 5. Bloco de Dados

### Bloco de Dados 1 – Formatos de Competição

| Formato                  | Descrição                                      | Configurações                                    |
|--------------------------|------------------------------------------------|--------------------------------------------------|
| KNOCKOUT                 | Mata-mata (eliminação direta)                  | Número de rodadas, disputa de 3º lugar          |
| GROUP_STAGE_KNOCKOUT     | Fase de grupos + mata-mata                     | Grupos, times por grupo, classificados por grupo |
| ROUND_ROBIN              | Todos contra todos (pontos corridos)           | Número de turnos                                 |
| TRIANGULAR               | 3 times jogam entre si                         | Turno único ou ida e volta                       |

### Bloco de Dados 2 – Chaveamento Criado

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Modalidade               | E             | Modalidade selecionada                                |
| Formato                  | E             | Formato escolhido (KNOCKOUT, GROUP_STAGE_KNOCKOUT...) |
| Configuração             | E/S           | JSON com parâmetros do formato                        |
| Quantidade de Times      | S             | Total de times participantes                          |
| Status                   | S             | Sempre criado como ACTIVE                             |
| Grupos/Chaves            | S             | Lista de grupos criados (se aplicável)                |
| Partidas Criadas         | S             | Total de partidas geradas                             |
| Data de Criação          | S             | Timestamp automático                                  |

### Bloco de Dados 3 – Partidas Geradas

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Time 1                   | S             | Time sorteado ou TBD                                  |
| Time 2                   | S             | Time sorteado ou TBD                                  |
| Grupo/Fase               | S             | A qual grupo ou fase pertence                         |
| Categoria                | S             | GROUP ou KNOCKOUT                                     |
| Status                   | S             | Sempre criado como SCHEDULED                          |
| Data Agendada            | S             | Null inicialmente (monitor define depois)             |

## 6. Regras de Negócio
1. Apenas **monitor** pode criar chaveamento;
2. Temporada deve estar em **IN_PROGRESS**;
3. Período de inscrição deve ter encerrado;
4. Modalidade deve ter ao menos **2 times aprovados**;
5. Apenas um chaveamento ativo por modalidade/temporada;
6. Formato escolhido aplica-se a **todas as fases** da modalidade;
7. Sorteio é **totalmente aleatório** (sem cabeças de chave na V1);
8. Sistema cria **todas as partidas de todas as fases** de uma vez:
   - Primeira fase: com times definidos pelo sorteio
   - Fases seguintes: com times TBD (a serem determinados)
9. Partidas de mata-mata têm `match_category = KNOCKOUT`;
10. Partidas de grupos têm `match_category = GROUP`;
11. Sistema distribui times nos grupos de forma equilibrada;
12. **Observação:** Sistema não trata automaticamente times ímpares. Monitor deve ajustar manualmente se necessário (V2);
13. Chaveamento criado tem status **ACTIVE**;
14. A operação deve ser registrada para auditoria.

## 7. Critérios de Aceitação
- O sistema deve bloquear criação se período de inscrição não encerrou;
- O sistema deve bloquear criação se modalidade tem menos de 2 times;
- O sistema deve bloquear criação se já existe chaveamento ativo;
- O sistema deve exibir opções de formato baseadas no número de times;
- O sistema deve permitir ajuste de configuração antes do sorteio;
- O sistema deve sortear times aleatoriamente;
- O sistema deve criar todas as partidas (primeira fase + fases seguintes TBD);
- O sistema deve definir `match_category` corretamente (GROUP/KNOCKOUT);
- O sistema deve criar chaveamento com status ACTIVE;
- O sistema deve exibir mensagens claras de sucesso ou erro;
- O sistema deve registrar a operação para auditoria.

## 8. Pós-condições
- Bracket criado com status ACTIVE;
- BracketGroups criados conforme formato;
- Times distribuídos nos grupos/chaves;
- Todas as partidas criadas com status SCHEDULED;
- Fases avançadas com times TBD;
- `match_category` definido para cada partida;
- Chaveamento pronto para monitor agendar datas e iniciar partidas;
- Operação registrada para auditoria.

## 9. Cenários de Teste

| Cenário                                    | Dado                                           | Quando                              | Então                                                    |
|--------------------------------------------|------------------------------------------------|-------------------------------------|----------------------------------------------------------|
| Criação bem-sucedida (Mata-mata)           | 8 times aprovados, formato KNOCKOUT            | Clica em "Sortear"                  | Sistema cria bracket e 7 partidas (oitavas, quartas...) |
| Criação bem-sucedida (Grupos)              | 12 times, formato GROUP_STAGE_KNOCKOUT         | Clica em "Sortear"                  | Sistema cria grupos e partidas de grupo + mata-mata     |
| Menos de 2 times                           | Modalidade com 1 time aprovado                 | Tenta criar chaveamento             | Sistema bloqueia e exibe erro                            |
| Chaveamento já existe                      | Modalidade já possui bracket ativo             | Tenta criar novo                    | Sistema bloqueia e exibe erro                            |
| Ajuste de configuração                     | Sistema sugere 4 grupos de 3 times             | Monitor ajusta para 3 de 4          | Sistema aceita e sorteia com nova config                |
| Sorteio aleatório                          | 8 times aprovados                              | Clica em "Sortear"                  | Times distribuídos aleatoriamente                        |
| Partidas TBD criadas                       | Formato mata-mata escolhido                    | Após sorteio                        | Sistema cria partidas das fases seguintes com TBD       |
| Match_category definido                    | Chaveamento misto (grupos + mata-mata)         | Após criação                        | Partidas de grupo têm GROUP, eliminatórias têm KNOCKOUT |
| Cancelamento de criação                    | Na tela de configuração                        | Clica em "Cancelar"                 | Sistema descarta e retorna sem criar                    |
| Times ímpares (observação)                 | 13 times aprovados                             | Cria chaveamento                    | Sistema cria normalmente, monitor ajusta manualmente    |
| Status do bracket                          | Chaveamento criado com sucesso                 | Verifica status                     | Status é ACTIVE                                         |
| Auditoria de criação                       | Chaveamento criado                             | Verifica logs                       | Sistema registra monitor, data/hora e configuração      |

## 10. Artefatos Relacionados
- [UC002 - Abrir Período de Inscrições](UC002_GestaoDeTemporadas_AbrirInscricoes.md)
- [UC009 - Aprovar Equipes](UC009_GestaoDeEquipes_AprovarEquipes.md)
- [UC012 - Gerenciar Chaveamento](UC012_GerenciarChaveamento.md)
- [UC013 - Iniciar Partida](UC013_IniciarPartida.md)