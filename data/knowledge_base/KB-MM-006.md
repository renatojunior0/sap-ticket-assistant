---
id: KB-MM-006
titulo: Entrada de mercadoria excede tolerância do pedido (overdelivery)
processo: entrada_mercadoria
transacoes: [MIGO, ME23N, ME22N, OMCO, MM03]
mensagens: [M7022]
---
# Entrada de mercadoria excede tolerância do pedido (overdelivery)

## Sintomas
- MIGO mov. 101 recusa quantidade maior que a do pedido: mensagem M7022 "Quantidade de EM excede a tolerância de fornecimento excedente".
- Fornecedor entregou mais do que o pedido (ex.: 110 vs. 100).

## Causas prováveis
- Tolerância de fornecimento excedente do item (EKPO-UEBTO) menor que a diferença entregue (ex.: 5% não cobre 10%).
- Indicador "entrega ilimitada" (EKPO-UEBTK) desmarcado.
- Tolerância padrão vem do registro info (ME13) ou do dado mestre de material (MM03 → Compras) e não foi ajustada.
- Mensagem M7022 configurada como erro em OMCQ (poderia ser aviso conforme política).

## Verificações (somente leitura)
- ME23N → item → aba Entrega: tolerância excedente (%) e flag entrega ilimitada.
- ME23N → Histórico: quantidade já recebida.
- MM03 → Compras: tolerâncias padrão do material; ME13: registro info.
- OMCQ (exibir): tipo da mensagem M7 022.

## Ação recomendada
Receber apenas a quantidade do pedido (100) e tratar o excedente com o comprador: devolver ao fornecedor ou ampliar o pedido. Nunca forçar a entrada alterando o pedido sem acordo comercial.

## Requer autorização humana
- Alterar tolerância ou marcar entrega ilimitada no item (ME22N): compromisso financeiro adicional — responsável: comprador.
- Criar item/pedido adicional para o excedente: responsável: comprador.
- Alterar OMCQ (M7022 de erro para aviso): customizing — responsável: consultor MM com aprovação do gestor de compras.