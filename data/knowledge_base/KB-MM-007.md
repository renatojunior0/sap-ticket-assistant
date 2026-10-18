---
id: KB-MM-007
titulo: Erro de autorização ao criar/alterar pedido de compra
processo: pedido_compra
transacoes: [ME21N, ME22N, SU53, SUIM, SU01, PFCG]
mensagens: [EU 000, ME 000, "Sem autorização"]
---
# Erro de autorização ao criar/alterar pedido de compra

## Sintomas
- Mensagem "Sem autorização para ..." na ME21N/ME22N, ou a transação não abre.
- Usuário consegue criar para uma organização de compras/centro e não para outra.

## Causas prováveis
- Falta do objeto M_BEST_EKO (organização de compras), M_BEST_EKG (grupo de compradores), M_BEST_WRK (centro) ou M_BEST_BSA (tipo de documento) no perfil do usuário.
- Autorização de transação S_TCODE ausente para ME21N.
- Função atribuída com validade expirada ou usuário recém-transferido de área.
- Tipo de documento novo (ex.: ZNB) não incluído nas funções existentes.

## Verificações (somente leitura)
- SU53 imediatamente após o erro: objeto e valores que faltaram.
- SUIM → Usuário → por valores de autorização: comparar com um usuário que consegue.
- SU01 (exibir): funções atribuídas e validade.

## Ação recomendada
Pedir ao usuário o print da SU53 e o contexto (transação, organização de compras, centro, tipo de pedido). Com isso abrir solicitação de acesso formal para a equipe de segurança com o objeto/valor identificado.

## Requer autorização humana
- Atribuir função ou alterar perfil (SU01/PFCG): governança de SoD — responsável: equipe de segurança SAP, com aprovação do gestor do usuário.
- Criar/alterar função: responsável: Basis/Security.