# Especificação de Caso de Uso: Reportar Jogador

## 1. Descrição
Este caso de uso permite que alunos reportem comportamentos inadequados de outros jogadores após partidas finalizadas ou através do perfil dos jogadores. Os reportes são analisados posteriormente pelos monitores como ferramenta de avaliação da conduta geral dos participantes do Intercurso.

## 2. Pré-condições
- O ator deve estar autenticado como **Aluno**;
- O aluno denunciante deve estar inscrito na temporada ativa (ter time ou ser atleta).

## 3. Fluxo Principal: Reportar Jogador
1. O aluno visualiza card de jogador (em listagem de times, perfil, estatísticas, etc);
2. O sistema exibe ícone de menu (⋮) no card do jogador;
3. O aluno clica no menu (⋮);
4. O sistema exibe opções do menu incluindo "⚠️ Reportar";
5. O aluno clica em "Reportar";
6. O sistema exibe modal de reporte conforme Bloco de Dados 1;
7. O aluno seleciona categoria da denúncia;
8. O aluno preenche descrição do problema;
9. O aluno pode opcionalmente marcar "Denúncia Anônima";
10. O aluno confirma o envio;
11. O sistema valida os dados conforme Regras de Negócio;
12. O sistema cria registro de Report com status PENDING;
13. O sistema define `reported_at = now()`;
14. Se denúncia não for anônima: sistema registra `reporter_id`;
15. Se denúncia for anônima: sistema mantém `reporter_id = NULL`;
16. O sistema vincula reporte à temporada ativa;
17. O sistema exibe mensagem de confirmação ao aluno;
18. O sistema fecha o modal.

## 4. Fluxos Alternativos

### Fluxo Alternativo 1: Reportar Via Estatísticas da Partida
1. O aluno acessa detalhes de partida finalizada (FINISHED);
2. O sistema exibe estatísticas e lista de jogadores que participaram;
3. Cada jogador tem ícone de menu (⋮) ao lado do nome;
4. O aluno clica no menu de um jogador específico;
5. O sistema exibe opção "⚠️ Reportar";
6. O aluno segue fluxo principal a partir do passo 5;
7. Sistema vincula reporte à partida específica automaticamente.

### Fluxo Alternativo 2: Reportar Via Perfil do Time
1. O aluno acessa perfil de um time;
2. O sistema exibe lista de membros do time;
3. Cada membro tem ícone de menu (⋮) ao lado do nome;
4. O aluno clica no menu de um jogador;
5. O aluno segue fluxo principal a partir do passo 5;
6. Sistema cria reporte sem vínculo com partida específica.

### Fluxo Alternativo 3: Tentar Reportar a Si Mesmo
1. Aluno clica em menu (⋮) do próprio card;
2. Sistema exibe menu **sem** a opção "Reportar";
3. Apenas outras opções aparecem (visualizar perfil, etc).

### Fluxo Alternativo 4: Denúncia Anônima
1. Aluno marca checkbox "Denúncia Anônima" no formulário;
2. Sistema exibe aviso: "ℹ️ Sua identidade será mantida em sigilo";
3. Aluno confirma envio;
4. Sistema cria reporte com `reporter_id = NULL` e `is_anonymous = true`;
5. Monitor verá apenas "Denúncia Anônima" sem identificação.

### Fluxo Alternativo 5: Cancelar Reporte
1. Aluno está preenchendo formulário de reporte;
2. Aluno clica em "Cancelar";
3. Sistema fecha modal sem salvar dados.

### Fluxo Alternativo 6: Descrição Muito Curta
1. Aluno preenche descrição com menos de 20 caracteres;
2. Aluno tenta enviar;
3. Sistema bloqueia e exibe erro: "Descreva o problema com mais detalhes (mínimo 20 caracteres)";
4. Aluno retorna ao formulário para completar.

## 5. Bloco de Dados

### Bloco de Dados 1 – Formulário de Reporte

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| Jogador Reportado        | S             | Nome e foto do jogador (já selecionado)               |
| Categoria da Denúncia    | E             | Dropdown com categorias (ver Bloco de Dados 2)        |
| Descrição                | E             | Campo de texto livre (mínimo 20 caracteres)           |
| Denúncia Anônima         | E             | Checkbox opcional (padrão: false)                     |
| Partida Relacionada      | S             | Partida automática (se veio de estatísticas)          |

### Bloco de Dados 2 – Categorias de Denúncia

| Categoria                        | Descrição                                           |
|----------------------------------|-----------------------------------------------------|
| CONDUTA_ANTIDESPORTIVA           | Comportamento antidesportivo, falta de fair play    |
| AGRESSAO_VERBAL                  | Xingamentos, ofensas, linguagem inadequada          |
| AGRESSAO_FISICA                  | Violência física, empurrões intencionais            |
| DESRESPEITO_MONITOR              | Desrespeito ao monitor/árbitro                      |
| JOGO_VIOLENTO                    | Faltas violentas, jogadas perigosas                 |
| DISCRIMINACAO                    | Racismo, homofobia, sexismo, qualquer discriminação |
| TRAPACA                          | Tentativa de enganar, corrupção                     |
| OUTROS                           | Outros problemas não listados                       |

### Bloco de Dados 3 – Reporte Criado

| Campo                    | Entrada/Saída | Observações                                           |
|--------------------------|---------------|-------------------------------------------------------|
| ID do Reporte            | S             | Identificador único                                   |
| Denunciante              | S             | ID do aluno ou NULL (anônimo)                         |
| Jogador Reportado        | S             | ID do jogador denunciado                              |
| Categoria                | S             | Categoria selecionada                                 |
| Descrição                | S             | Texto descritivo do problema                          |
| Partida                  | S             | ID da partida ou NULL                                 |
| É Anônimo                | S             | true ou false                                         |
| Status                   | S             | PENDING (sempre inicial)                              |
| Data do Reporte          | S             | Timestamp automático                                  |
| Temporada                | S             | Temporada ativa vinculada automaticamente             |

## 6. Regras de Negócio

### Criar Reporte:
1. Apenas **alunos** podem criar reportes de jogadores;
2. Aluno deve estar inscrito na temporada ativa (ter time ou `is_athlete = true`);
3. Aluno **não pode reportar a si mesmo** (opção não aparece no próprio menu);
4. Reportes são feitos **após eventos**, não durante partidas ao vivo;
5. Categoria da denúncia é **obrigatória**;
6. Descrição deve ter **mínimo de 20 caracteres**;
7. Denúncia pode ser **anônima** (opcional);
8. Sistema vincula reporte à **temporada ativa** automaticamente;
9. Se reporte vem de estatísticas de partida, vincula **match_id** automaticamente;
10. Se reporte vem de perfil/listagem, **match_id = NULL**;
11. Reporte criado tem status inicial **PENDING**;
12. `reported_at` é preenchido com timestamp atual;
13. **Se anônimo:** `reporter_id = NULL` e `is_anonymous = true`;
14. **Se não anônimo:** `reporter_id` registra o denunciante.

### Anonimato:
15. Denúncias anônimas **não exibem** identidade do denunciante para monitores;
16. Identidade anônima **não pode ser revelada** por monitores;
17. Denúncias anônimas têm mesmo peso que denúncias identificadas.

### Proteção ao Denunciante:
18. Sistema **não notifica** o jogador reportado sobre a denúncia;
19. Jogador reportado **não tem acesso** aos reportes contra ele;
20. Apenas **monitores** visualizam reportes;
21. Denunciante pode acompanhar status do seu reporte (em "Meus Reportes").

### Validações:
22. Sistema valida que categoria selecionada é válida;
23. Sistema valida comprimento mínimo da descrição (20 caracteres);
24. Sistema previne spam: máximo de **5 reportes por aluno por semana**;
25. Reportes são para **análise posterior**, não geram notificações imediatas.

### Análise Posterior:
26. Monitores analisam reportes em painel dedicado (UC019);
27. Reportes servem como **ferramenta de avaliação** da conduta geral;
28. Sistema permite identificar **padrões de comportamento** problemático;
29. Múltiplos reportes do mesmo jogador indicam problema recorrente;
30. A operação deve ser registrada para auditoria.

## 7. Critérios de Aceitação
- O sistema deve exibir opção "Reportar" no menu (⋮) de todos os cards de jogadores;
- O sistema deve ocultar opção "Reportar" no menu do próprio jogador;
- O sistema deve validar categoria obrigatória;
- O sistema deve validar descrição mínima de 20 caracteres;
- O sistema deve permitir denúncia anônima;
- O sistema deve ocultar identidade em denúncias anônimas;
- O sistema deve vincular reporte à partida quando vem de estatísticas;
- O sistema deve vincular reporte à temporada ativa;
- O sistema deve criar reporte com status PENDING;
- O sistema deve prevenir spam (máximo 5 reportes/semana);
- O sistema deve proteger identidade do denunciante;
- O sistema deve permitir cancelar reporte antes de enviar;
- O sistema NÃO deve notificar o jogador reportado;
- O sistema NÃO deve enviar notificações imediatas aos monitores;
- O sistema deve exibir mensagem clara de confirmação;
- O sistema deve registrar a operação para auditoria.

## 8. Pós-condições
- Reporte criado com status PENDING;
- Denunciante registrado ou NULL (anônimo);
- Jogador reportado vinculado ao reporte;
- Partida vinculada (se aplicável);
- Temporada ativa vinculada;
- Categoria e descrição registradas;
- Reporte disponível para monitores em painel dedicado;
- Operação registrada para auditoria;
- Aluno pode acompanhar status em "Meus Reportes".

## 9. Cenários de Teste

| Cenário                                    | Dado                                           | Quando                              | Então                                                    |
|--------------------------------------------|------------------------------------------------|-------------------------------------|----------------------------------------------------------|
| Reportar via card de jogador               | Card de jogador em listagem                    | Clica menu (⋮) e "Reportar"         | Sistema exibe modal de reporte                           |
| Reportar via estatísticas de partida       | Partida FINISHED, lista de jogadores           | Clica menu (⋮) de jogador           | Sistema exibe modal com partida vinculada                |
| Reportar via perfil do time                | Perfil do time, lista de membros               | Clica menu (⋮) de membro            | Sistema exibe modal sem partida vinculada                |
| Próprio menu não tem "Reportar"            | Card do próprio jogador                        | Clica menu (⋮)                      | Opção "Reportar" não aparece                             |
| Selecionar categoria                       | Formulário aberto                              | Seleciona AGRESSAO_VERBAL           | Sistema aceita categoria                                 |
| Descrição muito curta                      | Descrição com 10 caracteres                    | Tenta enviar                        | Sistema bloqueia e exige mínimo 20 caracteres            |
| Denúncia anônima                           | Marca "Denúncia Anônima"                       | Envia reporte                       | Sistema cria com reporter_id=NULL e is_anonymous=true    |
| Denúncia identificada                      | Não marca anônima                              | Envia reporte                       | Sistema registra reporter_id do aluno                    |
| Cancelar reporte                           | Formulário preenchido                          | Clica "Cancelar"                    | Sistema fecha sem salvar                                 |
| Validação de categoria obrigatória         | Tenta enviar sem selecionar categoria          | Clica "Enviar"                      | Sistema bloqueia e exige categoria                       |
| Vinculação à partida (estatísticas)        | Reporte vindo de estatísticas                  | Verifica reporte criado             | Sistema vincula match_id automaticamente                 |
| Sem vinculação à partida (perfil)          | Reporte vindo de perfil                        | Verifica reporte criado             | match_id é NULL                                          |
| Vinculação à temporada                     | Reporte criado                                 | Verifica temporada                  | Sistema vincula à temporada ativa                        |
| Status inicial PENDING                     | Reporte enviado com sucesso                    | Verifica status                     | Status é PENDING                                         |
| Sem notificação ao reportado               | Reporte criado contra jogador Y                | Verifica notificações de Y          | Jogador Y não recebe nenhuma notificação                 |
| Sem notificação imediata ao monitor        | Reporte criado                                 | Verifica notificações               | Monitor não recebe notificação imediata                  |
| Spam prevention                            | Aluno cria 6º reporte na mesma semana          | Tenta enviar                        | Sistema bloqueia e exibe limite semanal                  |
| Timestamp automático                       | Reporte criado                                 | Verifica reported_at                | Sistema registra data/hora exata                         |
| Denunciante acompanha status               | Reporte criado pelo aluno A                    | Aluno A acessa "Meus Reportes"      | Sistema exibe status do reporte                          |
| Jogador reportado não acessa               | Reporte criado contra jogador Y                | Jogador Y tenta ver reportes        | Sistema não exibe reportes contra ele                    |
| Mensagem de confirmação                    | Reporte enviado com sucesso                    | Verifica mensagem                   | "Reporte enviado. Será analisado pelos monitores"        |
| Auditoria de reporte                       | Reporte criado                                 | Verifica logs de auditoria          | Sistema registra denunciante, reportado e data/hora      |

## 10. Fluxo Complementar: Monitor Gerencia Reportes (UC019)

**Nota:** O gerenciamento de reportes pelos monitores será detalhado no UC019 - Gerenciar Reportes, que incluirá:
- Visualizar painel de reportes pendentes
- Filtrar por categoria, status, jogador, temporada
- Analisar detalhes do reporte
- Visualizar histórico de reportes por jogador
- Atualizar status (PENDING → UNDER_REVIEW → RESOLVED/DISMISSED)
- Adicionar notas internas sobre análise
- Aplicar ações disciplinares se necessário (V2)
- Gerar relatórios de conduta geral do Intercurso

## 11. Artefatos Relacionados
- [UC015 - Finalizar Partida](UC015_FinalizarPartida.md)
- [UC016 - Visualizar Partida em Tempo Real](UC016_VisualizarPartida.md)
- [UC005 - Criar Equipe](UC005_GestaoDeEquipes_CriarEquipe.md)
- [UC019 - Gerenciar Reportes](UC019_GerenciarReportes.md) (a ser criado)

### Princípios:
- **Discrição:** Opção de reportar deve ser discreta mas acessível
- **Simplicidade:** Formulário limpo e objetivo
- **Privacidade:** Identidade protegida, especialmente em denúncias anônimas
- **Análise posterior:** Foco em avaliação de conduta geral, não ações imediatas