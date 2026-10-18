---
id: KB-MM-009
titulo: IDoc ORDERS com status 51 (erro de aplicação) — pedido não criado
processo: integracao
transacoes: [WE02, WE05, WE19, BD87, WE20, WE21, XK03, ME23N]
mensagens: [Status 51, Status 56, Status 64]
---
# IDoc ORDERS com status 51 (erro de aplicação) — pedido não criado

## Sintomas
- IDoc de entrada tipo ORDERS/ORDERS05 fica com status 51 na WE02 e nenhum pedido é gerado.
- Pedidos do portal do fornecedor/EDI deixam de chegar no SAP.

## Causas prováveis
- Fornecedor não cadastrado para a organização de compras (LFM1) ou bloqueado (XK03).
- Parceiro de entrada (WE20) sem o tipo de mensagem ORDERS ou código de função incorreto (ex.: IDOC_INPUT_ORDERS).
- Dado obrigatório ausente/inválido no segmento (material inexistente, unidade de medida, centro, tipo de pedido) — mensagem de erro no status record.
- Código do material do parceiro não mapeado (registro info ME13 ou tabela de conversão).
- Período/ano ou grupo de compradores inválido no segmento E1EDK01/E1EDP01.

## Verificações (somente leitura)
- WE02/WE05: abrir o IDoc → registro de status 51 → texto da mensagem e segmento com erro.
- WE20: perfil do parceiro e parâmetro de entrada para ORDERS.
- XK03 / MM03: existência e bloqueio do fornecedor e do material para a org. de compras/centro.
- BD87 (exibir): IDocs agrupados por erro.

## Ação recomendada
Ler a mensagem de erro do status 51 (ela aponta o campo exato), corrigir a causa (cadastro ou mapeamento) e reprocessar. Testar em WE19 copiando o IDoc para QA antes de reprocessar em produção.

## Requer autorização humana
- Criar/estender fornecedor ou material (XK01/XK02, MM01/MM02): dado mestre — responsável: MDM.
- Alterar perfil de parceiro (WE20): configuração de integração — responsável: Basis/integração.
- Reprocessar IDoc (BD87) ou editar segmento (WE19/WE02): gera documento real — responsável: analista de integração com aprovação de compras.