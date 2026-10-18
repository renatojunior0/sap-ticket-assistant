---
id: KB-MM-005
titulo: Fatura bloqueada para pagamento após MIRO
processo: verificacao_fatura
transacoes: [MIRO, MIR4, MRBR, ME23N, OMR6, ME22N]
mensagens: [M8, RBKP-ZLSPR]
---
# Fatura bloqueada para pagamento após MIRO

## Sintomas
- Fatura registrada na MIRO mas o financeiro informa bloqueio para pagamento (campo RBKP-ZLSPR preenchido).
- Fornecedor cobra pagamento vencido; F110 não seleciona o documento.

## Causas prováveis
- **Bloqueio R (divergência de preço)**: valor da fatura excede o valor do pedido além da tolerância PP (OMR6).
- **Bloqueio por quantidade (DQ)**: quantidade faturada maior que quantidade recebida.
- **Bloqueio por data (ST)**: fatura antes da data de entrega prevista.
- **Bloqueio manual (A)**: usuário marcou "bloquear pagamento" na MIRO.
- **Bloqueio estocástico (S)**: amostragem configurada em OMRG.

## Verificações (somente leitura)
- MIR4 → aba Pagamento: campo "Bloqueio de pagamento" e motivo por item (bloqueio R, Q, D).
- MRBR em modo exibição: lista de faturas bloqueadas e motivo.
- ME23N → aba Condições: preço do pedido vs. preço faturado; aba Histórico: quantidade recebida.
- OMR6 (exibir): limites de tolerância PP/DQ para a empresa.

## Ação recomendada
Identificar o motivo do bloqueio na MIR4 e confrontar com o pedido. Se a diferença for legítima (reajuste acordado), o comprador ajusta o pedido; se for erro do fornecedor, solicitar nota de crédito.

## Requer autorização humana
- Liberar fatura na MRBR: impacto direto em pagamento — responsável: Contas a Pagar / aprovador conforme alçada.
- Alterar preço do pedido (ME22N): compromisso financeiro — responsável: comprador.
- Alterar tolerâncias (OMR6): customizing com efeito em todas as faturas — responsável: consultor MM + Controladoria.