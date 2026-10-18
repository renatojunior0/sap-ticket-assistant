---
id: KB-MM-002
titulo: Divergência entre pedido de compra e recebimento (quantidade ou valor)
processo: entrada_mercadoria
transacoes: [ME23N, MIGO, MB51, MB5S, MR11, MBST]
mensagens: [M7021, M7022]
---
# Divergência entre pedido de compra e recebimento (quantidade ou valor)

## Sintomas
- Quantidade recebida na MIGO diferente da quantidade do pedido.
- Saldo na conta GR/IR (MB5S) não zera após fatura.
- Usuário recebeu material errado ou em unidade de medida diferente.

## Causas prováveis
- Entrega parcial ou excesso de fornecimento (ver KB-MM-006 para tolerância).
- Entrada lançada contra item errado do pedido ou pedido errado.
- Unidade de medida do pedido ≠ unidade de entrada (conversão em MM03 → dados básicos).
- Entrada lançada e fatura ainda não registrada (saldo GR/IR é normal até a MIRO).
- Estorno parcial (mov. 102) não realizado após erro de lançamento.

## Verificações (somente leitura)
- ME23N → aba Histórico do pedido: documentos de material (101/102) e faturas por item.
- MB51 filtrando pedido e material: datas, quantidades, usuário.
- MB5S: saldo GR/IR por pedido/item.
- MM03 → Dados básicos 1: unidade de medida base e conversões.

## Ação recomendada
Identificar qual documento gerou a divergência pelo histórico e orientar o usuário a confirmar fisicamente a quantidade. Se a entrada foi lançada errada, a correção é estorno (MBST / MIGO 102) pelo responsável do almoxarifado.

## Requer autorização humana
- Estorno de documento de material (MBST / MIGO 102): impacto em estoque e FI — responsável: supervisor de almoxarifado.
- Compensação manual de GR/IR (MR11): impacto contábil — responsável: Controladoria.
- Alteração de quantidade do pedido (ME22N): responsável: comprador.