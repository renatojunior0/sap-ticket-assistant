"""Gera data/ontology/mm_ontology.yaml e transacoes_catalogo.yaml a partir da planilha corporativa.
Layout por aba: título 'XX - Nome do módulo', cabeçalho com 'Transação' e 'Descrição',
coluna 'Categoria' em células mescladas. Aba 'Extras' traz também Tabela/Descrição e Tipo/Descrição.
Uso: python scripts/build_ontology.py
"""
import re
from collections import defaultdict
from pathlib import Path

import openpyxl
import yaml

ROOT = Path(__file__).resolve().parents[1]
SHEET = next(ROOT.glob("data/raw_docs/Transa*.xlsx"), None)
OUT_DIR = ROOT / "data" / "ontology"

TCODE = re.compile(r"^/?[A-Z][A-Z0-9_]{1,3}[A-Z0-9_/]{0,16}$")
SHEET_MODULE_ALIAS = {"EXTRAS": "BC"}
BLOCKS = {"transação": "transacoes", "tabela": "tabelas", "tipo": "tipos_material"}  # cabeçalho -> coleção

# Ordem importa: regras mais específicas antes (MIR* antes de MI*).
PROCESS_RULES = [
    ("verificacao_fatura", r"^(MIR|MR)"),
    ("localizacao_brasil", r"^(J1B|J_1B|FTXP)"),
    ("requisicao_compra", r"^ME5"),
    ("pedido_compra", r"^(ME2|ME3|ME4|ME6|ME8|ME9)"),
    ("entrada_mercadoria", r"^(MIGO|MB|MMBE|MMPV|MMRV|MI\d)"),
    ("dados_mestres", r"^(MM0|MM5|MM6|ME0|ME1|MK0|MKV|XK0|FK0|MSC|BP$)"),
    ("relatorios", r"^(S_ALR|ME2|MB5|MC\.)"),
    ("integracao", r"^(WE|BD87|SM58|SXMB|SXI)"),
    ("autorizacao", r"^(SU|PFCG|ST01)"),
]

ADJACENT_SD = re.compile(r"^(VL|VF|VT|VA)")  # expedição/faturamento SD: fora do P2P, encaminhar à equipe SD

TEMPLATE = {
    "modulo": "MM",
    "descricao": "Ontologia P2P (MM) — processos curados manualmente, transações/tabelas enriquecidas pela planilha corporativa",
    "fora_escopo": {
        "modulos": ["HR", "HCM", "PA", "PY", "PT"],
        "modulos_adjacentes": ["FI", "CO", "SD", "PP", "PM", "WM", "BC"],  # não recusa: triagem encaminha à equipe dona
        "intencoes": ["executar acao", "rodar script", "liberar em massa", "alterar em massa"],
    },
    "processos": {
        "requisicao_compra": {"nome": "Requisição de compra", "etapa": 1, "tabelas": ["EBAN"],
                              "informacoes_minimas": ["numero_requisicao_ou_item", "transacao", "mensagem_de_erro"]},
        "pedido_compra": {"nome": "Pedido de compra / contratos / cotações", "etapa": 2,
                          "tabelas": ["EKKO", "EKPO", "EKET", "EKBE", "T16FS", "T16FV"],
                          "objetos_autorizacao": ["M_BEST_EKO", "M_BEST_WRK", "M_BEST_BSA", "M_EINK_FRG"],
                          "informacoes_minimas": ["numero_pedido", "sintoma_ou_mensagem"]},
        "entrada_mercadoria": {"nome": "Entrada de mercadoria / movimentos de estoque", "etapa": 3,
                               "tabelas": ["MKPF", "MSEG", "MARD", "MARC"],
                               "mensagens": ["M7053", "M7021", "M7022", "M7001", "M7024", "M7093"],
                               "informacoes_minimas": ["numero_pedido_ou_documento_material", "data_lancamento", "mensagem_de_erro"]},
        "verificacao_fatura": {"nome": "Verificação de fatura (MIRO)", "etapa": 4, "tabelas": ["RBKP", "RSEG", "EKBE"],
                               "mensagens": ["M8049", "M8050", "M8504"],
                               "informacoes_minimas": ["numero_fatura_ou_pedido", "mensagem_de_erro_ou_sintoma"]},
        "localizacao_brasil": {"nome": "Nota fiscal e impostos (Localização BR)", "etapa": 4,
                               "tabelas": ["J_1BNFDOC", "J_1BNFLIN", "J_1BTXIC1", "J_1BTXIP1"],
                               "informacoes_minimas": ["numero_nota_ou_pedido", "codigo_imposto_ou_mensagem"]},
        "integracao": {"nome": "Integração / IDoc / interfaces", "tabelas": ["EDIDC", "EDID4"],
                       "informacoes_minimas": ["numero_idoc_ou_mensagem", "tipo_mensagem", "status"]},
        "dados_mestres": {"nome": "Dados mestres (material, fornecedor, registro info)",
                          "tabelas": ["MARA", "MARC", "MBEW", "LFA1", "LFM1", "EINA", "EINE"],
                          "informacoes_minimas": ["codigo_material_ou_fornecedor", "centro_ou_org_compras", "mensagem_de_erro"]},
        "autorizacao": {"nome": "Autorização e acesso",
                        "objetos_autorizacao": ["M_BEST_EKO", "M_BEST_WRK", "M_BANF_EKO", "M_EINK_FRG", "M_MSEG_BWA", "M_RECH_WRK"],
                        "informacoes_minimas": ["transacao", "texto_exato_do_erro", "usuario"]},
        "relatorios": {"nome": "Relatórios e consultas de compras/estoque",
        "informacoes_minimas": ["nome_do_relatorio", "parametros_de_selecao", "resultado_esperado"]},
    },
    "acoes_criticas": ["liberar pedido", "liberar requisição", "liberar fatura", "liberar bloqueio", "estornar",
                       "abrir período", "fechar período", "alterar configuração", "spro", "atribuir autorização",
                       "atribuir role", "alterar dados mestres", "alteração em massa", "executar script", "transporte"],
}


def clean(cell) -> str:
    return re.sub(r"\s+", " ", str(cell)).strip() if cell is not None else ""


def parse_sheet(sheet) -> dict | None:
    rows = [list(r) for r in sheet.iter_rows(values_only=True)]
    header_index = next((i for i, r in enumerate(rows) if any(clean(c).lower() == "transação" for c in r)), None)
    if header_index is None:
        return None
    header = rows[header_index]
    title = next((clean(c) for r in rows[:header_index] for c in r if " - " in clean(c)), sheet.title)
    module = SHEET_MODULE_ALIAS.get(sheet.title.strip().upper(), title.split(" - ")[0].strip().upper())
    blocks = {j: BLOCKS[clean(c).lower()] for j, c in enumerate(header) if clean(c).lower() in BLOCKS}
    category_col = next((j for j, c in enumerate(header) if clean(c).lower() == "categoria"), None)

    parsed = {"modulo": module, "nome": title.split(" - ")[-1].strip(), "transacoes": {}, "tabelas": {}, "tipos_material": {}}
    category = None  # células mescladas: valor só na 1ª linha do grupo -> forward-fill
    for row in rows[header_index + 1:]:
        if category_col is not None and clean(row[category_col]):
            category = clean(row[category_col])
        for column, collection in blocks.items():
            code = clean(row[column]).upper()
            description = clean(row[column + 1]) if column + 1 < len(row) else ""
            if not code or (collection == "transacoes" and not TCODE.match(code)):
                continue
            parsed[collection][code] = {"descricao": description, "categoria": category} if collection == "transacoes" else description
    return parsed


def process_for(code: str) -> str | None:
    return next((name for name, pattern in PROCESS_RULES if re.match(pattern, code)), None)


def main() -> None:
    if not SHEET:
        raise SystemExit("Planilha não encontrada em data/raw_docs/Transa*.xlsx")
    workbook = openpyxl.load_workbook(SHEET, read_only=True, data_only=True)
    sheets = [s for s in (parse_sheet(ws) for ws in workbook) if s]
    sheets.sort(key=lambda s: s["modulo"] != "MM")  # MM primeiro: em código duplicado, prevalece MM

    catalog, module_names, tables, material_types = {}, {}, {}, {}
    for sheet in sheets:
        module_names[sheet["modulo"]] = sheet["nome"]
        for code, info in sheet["transacoes"].items():
            catalog.setdefault(code, {"modulo": sheet["modulo"], **info})
        tables.update(sheet["tabelas"])
        material_types.update(sheet["tipos_material"])

    mm = {code: info for code, info in catalog.items() if info["modulo"] == "MM"}
    by_process, by_category, unmapped = defaultdict(dict), defaultdict(list), []
    for code, info in sorted(mm.items()):
        by_category[info["categoria"] or "Sem categoria"].append(code)
        if ADJACENT_SD.match(code):
            continue
        if process := process_for(code):
            by_process[process][code] = info["descricao"]
        else:
            unmapped.append(code)

    ontology = TEMPLATE
    for name, process in ontology["processos"].items():
        process["transacoes"] = sorted(by_process.get(name, {}))
        process["descricoes_transacoes"] = by_process.get(name, {})
    ontology["categorias_planilha_mm"] = dict(by_category)
    ontology["tipos_material"] = material_types
    ontology["tabelas_referencia"] = tables
    ontology["modulos_catalogo"] = module_names
    ontology["catalogo_transacoes_path"] = "transacoes_catalogo.yaml"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "mm_ontology.yaml").write_text(yaml.safe_dump(ontology, allow_unicode=True, sort_keys=False), encoding="utf-8")
    (OUT_DIR / "transacoes_catalogo.yaml").write_text(yaml.safe_dump(catalog, allow_unicode=True, sort_keys=True), encoding="utf-8")

    per_module = defaultdict(int)
    for info in catalog.values():
        per_module[info["modulo"]] += 1
    print(f"transações: {len(catalog)} | por módulo: {dict(per_module)}")
    print(f"tabelas: {len(tables)} | tipos de material: {len(material_types)}")
    print(f"MM por processo: { {k: len(v) for k, v in by_process.items()} }")
    print(f"MM sem processo ({len(unmapped)}): {unmapped}")


if __name__ == "__main__":
    main()