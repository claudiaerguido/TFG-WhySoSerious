# Tipo: Validación
# Requisitos cubiertos: RF13, RF14
# Objetivo: Verificar el cálculo y aplicación correcta del rango temporal correspondiente al año fiscal configurado.

import pytest
from datetime import date
from unittest.mock import patch, MagicMock

from backend.main import _get_fiscal_year_range


@patch("backend.main.date")
def test_fy_range_calculation_january(mock_date):
    """
    REQ: RF13 (Filtro por fechas) y RF14 (Selección de periodo personalizado).
    DEFINICIÓN: El cálculo del año fiscal debe ser preciso incluso si coincide con el año natural.
    VALIDACIÓN: Se inyecta una fecha simulada en abril de 2026 y se comprueba que, para un inicio en enero, el rango resultante es el año completo 2026.
    """
    mock_date.today.return_value = date(2026, 4, 11)
    mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

    start, end, year = _get_fiscal_year_range(1)

    assert start == "2026-01-01"
    assert end == "2026-12-31"
    assert year == 2026


@patch("backend.main.date")
def test_fy_range_calculation_april_current_cycle(mock_date):
    """
    REQ: RF13 (Filtro por fechas) y RF14 (Selección de periodo personalizado).
    DEFINICIÓN: Gestión de ciclos fiscales que comienzan el mes actual.
    VALIDACIÓN: Verifica que si hoy es abril de 2026 y el FY empieza en abril, el sistema identifica correctamente que estamos al inicio del ciclo 2026 y proyecta el final en marzo de 2027.
    """
    mock_date.today.return_value = date(2026, 4, 11)
    mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

    start, end, year = _get_fiscal_year_range(4)

    assert start == "2026-04-01"
    assert end == "2027-03-31"
    assert year == 2026


@patch("backend.main.date")
def test_fy_range_calculation_september_past_cycle(mock_date):
    """
    REQ: RF13 (Filtro por fechas) y RF14 (Selección de periodo personalizado).
    DEFINICIÓN: Gestión de ciclos fiscales que empezaron el año anterior (ej. curso académico).
    VALIDACIÓN: Comprueba que si hoy es abril de 2026 y el FY empieza en septiembre, el sistema retrocede correctamente a septiembre de 2025 para el inicio del rango.
    """
    mock_date.today.return_value = date(2026, 4, 11)
    mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

    start, end, year = _get_fiscal_year_range(9)

    assert start == "2025-09-01"
    assert end == "2026-08-31"
    assert year == 2025


@patch("backend.main.date")
def test_fy_range_calculation_september_current_cycle(mock_date):
    """
    REQ: RF13 (Filtro por fechas) y RF14 (Selección de periodo personalizado).
    DEFINICIÓN: Cambio de ciclo anual dentro del inicio del año fiscal.
    VALIDACIÓN: Verifica que si ya estamos en octubre de 2026, el ciclo fiscal de septiembre se asocia al año actual (2026) y no al anterior.
    """
    mock_date.today.return_value = date(2026, 10, 15)
    mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

    start, end, year = _get_fiscal_year_range(9)

    assert start == "2026-09-01"
    assert end == "2027-08-31"
    assert year == 2026