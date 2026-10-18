---
id: KB-MM-004
titulo: Erro M7053 - Período de lançamento não aberto na entrada de mercadoria
modulo: MM
processo: entrada_mercadoria
transacoes: [MIGO, MMPV, MMRV, OB52, MB5L]
mensagens: [M7053, M7021]
tabelas: [MARV, T001B]
risco_acao: alto
referencias:
  - SAP Help Portal - Period Closing Program (MMPV)
  - SAP Help Portal - Posting Periods in Materials Management
---
## Sintoma
Ao lançar um movimento de mercadoria (MIGO, entrada por pedido, transferência ou estorno) o sistema emite a mensagem M7053 "Período de lançamento XXX YYYY não está aberto para a variante Z". O documento de material não é gerado.

## Causas prováveis
1. A data de lançamento informada pertence a um período já fechado em MM: o programa de encerramento de período (MMPV) já avançou o período da empresa e o período anterior não está habilitado.
2. O usuário está lançando com data retroativa em um período que foi fechado por política contábil.
3. O período de MM (MMRV) está aberto, mas o período contábil em FI (OB52) está fechado para a variante da empresa ou para o tipo de conta de material; neste caso a mensagem pode variar.
4. O período corrente nunca foi aberto porque a rotina mensal MMPV não foi executada (comum em ambientes de teste).

## Verificações somente leitura
- MMRV: exibir o período corrente e o período anterior da empresa e verificar se o indicador "Permitir lançamento no período anterior" está ativo.
- OB52 em modo exibição (ou consulta ao FI): confirmar os períodos abertos na variante de período contábil da empresa.
- Confirmar com o usuário a data de lançamento pretendida e se há real necessidade de lançar no período anterior.
- MB5L ou relatório de estoque: verificar impactos de lançar retroativamente no saldo de estoque do período.

## Ações que exigem autorização humana
- Abrir o período anterior em MM (MMRV) ou alterar períodos em FI (OB52): decisão do controller / gestor financeiro, pois afeta fechamento contábil e relatórios.
- Executar MMPV para avançar período: rotina controlada de fechamento, executada por time autorizado e com data planejada.
- Alterar a data de lançamento do documento para o período aberto: deve ser validada com o negócio quando houver impacto em inventário, custos ou fiscal.