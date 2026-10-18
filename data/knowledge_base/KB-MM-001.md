---
id: KB-MM-001
titulo: Visão geral do processo Procure-to-Pay (P2P) em SAP MM
processo: visao_geral_p2p
transacoes: [ME51N, ME54N, ME21N, ME28, ME29N, MIGO, MIRO, MRBR, F110]
mensagens: []
---
# Visão geral do processo Procure-to-Pay (P2P) em SAP MM

## Sintomas / solicitação típica
Usuário não sabe em qual etapa o documento está travado: "o pedido não anda", "não consigo receber", "a fatura não foi paga".

## Fluxo padrão e documentos
1. Requisição de compra (ME51N) → liberação ME54N/ME55 (EBAN).
2. Pedido de compra (ME21N) → estratégia de liberação ME28/ME29N (EKKO/EKPO, EKKO-FRGKE).
3. Entrada de mercadoria MIGO mov. 101 → documento de material (MKPF/MSEG) e contábil (BKPF/BSEG), conta GR/IR.
4. Verificação de fatura MIRO → documento RBKP/RSEG; bloqueios em MRBR.
5. Pagamento F110 (FI-AP).

## Verificações (somente leitura)
- ME23N aba Status: quantidades pedidas, recebidas e faturadas por item; histórico do pedido (EKBE).
- ME2N / ME2M: pedidos por fornecedor ou material com status de liberação.
- MB51: movimentos de material; MIR4/MIR5: faturas.

## Ação recomendada
Localizar a etapa onde o documento parou pelo histórico do pedido (ME23N → Histórico) antes de abrir chamado para cada módulo. Redirecionar: bloqueio de liberação → KB-MM-003; período → KB-MM-004; fatura bloqueada → KB-MM-005.

## Requer autorização humana
Nenhuma ação direta. Qualquer alteração em documentos segue os artigos específicos.