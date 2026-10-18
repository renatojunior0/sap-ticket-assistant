import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from assistant import config  # noqa: E402
from assistant.pipeline import analyze  # noqa: E402


def load_tickets() -> dict[str, dict]:
    return {t["id"]: t for t in json.loads(config.TICKETS_PATH.read_text(encoding="utf-8"))}


def print_response(response) -> None:
    print("=" * 80)
    print(f"[{response.ticket_id}] STATUS: {response.status.value} | confiança: {response.confianca} ({response.nivel_confianca})"
          f" | humano: {response.requer_humano} | {response.latencia_ms} ms")
    print(f"Processo: {response.triage.processo} | transações: {response.triage.transacoes}")
    if response.analysis:
        print("\nCAUSAS PROVÁVEIS (IA recomenda):")
        for causa in response.analysis.causas:
            print(f"  - [{causa.probabilidade}] {causa.descricao}  {causa.fontes}")
        print("\nVERIFICAÇÕES SOMENTE LEITURA:")
        for check in response.analysis.verificacoes_somente_leitura:
            print(f"  - ({check.transacao or '-'}) {check.descricao}")
        print("\nAÇÕES QUE EXIGEM AUTORIZAÇÃO HUMANA:")
        for action in response.analysis.acoes_requerem_autorizacao:
            print(f"  - {action.descricao} | risco: {action.motivo_risco} | responsável: {action.responsavel_sugerido}")
    if response.motivos_humano:
        print(f"\nMOTIVOS DE ESCALONAMENTO: {response.motivos_humano}")
    print(f"\nFONTES: {[(s.id, s.score) for s in response.fontes]}")
    print(f"\nMENSAGEM AO USUÁRIO:\n{response.mensagem_ao_usuario}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Assistente de análise de chamados SAP MM")
    parser.add_argument("--ticket", help="ID do chamado em data/tickets/tickets.json")
    parser.add_argument("--texto", help="Texto livre de um chamado")
    parser.add_argument("--all", action="store_true", help="Executa todos os chamados")
    args = parser.parse_args()

    tickets = load_tickets()
    if args.texto:
        print_response(analyze(args.texto))
    elif args.all:
        for ticket in tickets.values():
            print_response(analyze(ticket["texto"], ticket["id"]))
    elif args.ticket:
        ticket = tickets[args.ticket]
        print_response(analyze(ticket["texto"], ticket["id"]))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()