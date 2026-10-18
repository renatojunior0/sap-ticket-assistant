---
id: KB-MM-008
titulo: ICMS calculado na MIRO divergente da NF-e (Localização Brasil / TAXBRA)
processo: localizacao_brasil
transacoes: [MIRO, J1B3N, J1BTAX, FTXP, ME23N, MM03, XK03]
mensagens: []
tabelas: [J_1BTXIC1, J_1BTXIC2, J_1BTXIC3, J_1BNFDOC, J_1BNFLIN, J_1BTAXCODEV]
---
## Sintomas
Ao lançar fatura com NF-e, o ICMS calculado pelo SAP (código de imposto ex.: I1) difere do destacado no documento do fornecedor; a MIRO não permite lançar ou gera saldo.

## Causas prováveis
1. **Alíquota de ICMS por UF origem/destino** (J_1BTXIC1) desatualizada ou sem entrada para a combinação emissor → receptor.
2. **Exceção por material/NCM ou fornecedor** (J_1BTXIC2/J_1BTXIC3) ausente ou incorreta — ex.: redução de base, isenção.
3. **Código de imposto errado na fatura**: I1 (tributado) usado quando a operação é isenta/ST ou vice-versa.
4. **Dados mestres fiscais**: fornecedor como não contribuinte/simples nacional (XK03) ou utilização do material / NCM (MM03) divergentes do que o fornecedor aplicou.

## Verificações (somente leitura)
- ME23N → item → aba Fatura: código de imposto do pedido; comparar com a NF-e.
- J1BTAX (exibir): alíquota e exceções para a combinação UF emissor/receptor, NCM e material.
- XK03 fornecedor: regime (contribuinte, simples) e UF; MM03: NCM/utilização do material.
- J1B3N: se a NF já foi criada, comparar campos de imposto por linha.

## Ação recomendada
Se o fornecedor errou, solicitar carta de correção/nota complementar. Se a tabela SAP está defasada, abrir chamado fiscal para atualização em J1BTAX (transporte).

## Requer autorização humana
Alteração de alíquotas/exceções fiscais e de dados mestres fiscais tem impacto tributário — exclusivo da equipe fiscal com change request.