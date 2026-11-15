"""Testes de ordenação de by_month e top_hotels, via CLI real (run_cli)."""

from decimal import Decimal

# AJUSTE o import para onde o seu helper está (ex.: tests/helpers.py ou conftest)
from helpers import run_cli


def row(rid, hotel_id, amount="100.00", **extra):
    return {
        "reservation_id": rid,
        "hotel_id": hotel_id,
        "hotel_name": f"Hotel {hotel_id}",
        "amount": amount,
        **extra,
    }


def ids(report):
    return [h["hotel_id"] for h in report["top_hotels"]]


def test_by_month_ascendente(tmp_path):
    # Meses inseridos fora de ordem de propósito
    rows = [
        row("R1", "H01", checkin_date="2025-03-10", checkout_date="2025-03-11"),
        row("R2", "H01", checkin_date="2025-01-10", checkout_date="2025-01-11"),
        row("R3", "H01", checkin_date="2025-02-10", checkout_date="2025-02-11"),
        row("R4", "H01", checkin_date="2024-12-10", checkout_date="2024-12-11"),
    ]
    report = run_cli(tmp_path, rows)

    assert [m["month"] for m in report["by_month"]] == [
        "2024-12", "2025-01", "2025-02", "2025-03",
    ]


def test_top_hotels_total_decrescente(tmp_path):
    rows = [
        row("R1", "H01", "100.00"),
        row("R2", "H02", "300.00"),
        row("R3", "H03", "200.00"),
    ]

    assert ids(run_cli(tmp_path, rows)) == ["H02", "H03", "H01"]


def test_top_hotels_desempate_hotel_id_ascendente(tmp_path):
    rows = [
        row("R1", "H05", "100.00"),
        row("R2", "H02", "100.00"),
        row("R3", "H09", "300.00"),
    ]

    # Falha com reverse=True na tupla (H05 viria antes de H02)
    assert ids(run_cli(tmp_path, rows)) == ["H09", "H02", "H05"]


def test_top_hotels_desempate_apos_conversao(tmp_path):
    # USD 100.00 * 5.42 = BRL 542.00, empatando com o hotel pago em BRL
    rows = [
        row("R1", "H03", "100.00", currency="USD"),
        row("R2", "H01", "542.00", currency="BRL"),
    ]

    assert ids(run_cli(tmp_path, rows)) == ["H01", "H03"]


def test_top_hotels_regra_completa(tmp_path):
    rows = [
        row("R1", "H04", "250.00"),
        row("R2", "H01", "250.00"),
        row("R3", "H07", "900.00"),
        row("R4", "H02", "250.00"),
        row("R5", "H06", "50.00"),
    ]
    top = run_cli(tmp_path, rows)["top_hotels"]

    for a, b in zip(top, top[1:]):
        va, vb = Decimal(a["total_brl"]), Decimal(b["total_brl"])
        assert va > vb or (va == vb and a["hotel_id"] < b["hotel_id"]), (a, b)


def test_top_respeita_limite(tmp_path):
    rows = [row(f"R{i}", f"H0{i}", f"{i * 100}.00") for i in range(1, 5)]

    assert ids(run_cli(tmp_path, rows, top=2)) == ["H04", "H03"]


def test_nao_faturavel_fora_do_ranking(tmp_path):
    rows = [
        row("R1", "H01", "100.00"),
        row("R2", "H02", "999.00", status="CANCELLED"),
    ]

    assert ids(run_cli(tmp_path, rows)) == ["H01"]