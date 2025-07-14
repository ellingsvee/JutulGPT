import pytest

from jutulgpt.nodes.check_code import (
    _replace_case,
    _shorten_first_argument,
    shorter_simulations,
)


def test_replace_case_basic():
    code_str = """
        sim_func_1(case; other_args)
    """
    result = _replace_case(
        code=code_str,
        case_name="case",
        simulation_functions=["sim_func_1"],
    )
    assert "case[1:1]" in result
    assert result.count("case[1:1]") == 1


def test_replace_case_multiple_functions():
    code_str = """
    sim_func_1(case; other_args)
    sim_func_2(other_args, case)
    """
    result = _replace_case(
        code=code_str,
        case_name="case",
        simulation_functions=["sim_func_1", "sim_func_2"],
    )
    assert result.count("case[1:1]") == 2


def test_replace_case_other_word():
    code_str = """
        sim_func_1(dt, other_args)
    """
    result = _replace_case(
        code=code_str,
        case_name="dt",
        simulation_functions=["sim_func_1"],
    )
    assert "dt[1:1]" in result
    assert result.count("dt[1:1]") == 1


def test_shorten_first_argument():
    code_str = """
    results_proxy = sim_func_1(proxy, info_level=0)
    """
    result = _shorten_first_argument(
        code=code_str,
        simulation_functions=["sim_func_1"],
    )
    assert result.count("proxy[1:1]") == 1
    assert "sim_func_1(proxy[1:1], info_level=0)" in result


def test_shorter_simulations():
    code_str = """
    simulate_reservoir(case; other_args)
    simulate_reservoir(args, dt, more_args)
    """
    result = shorter_simulations(
        code=code_str,
    )
    assert result.count("case[1:1]") == 1
    assert result.count("dt[1:1]") == 1
    assert "simulate_reservoir(case[1:1]; other_args)" in result
    assert "simulate_reservoir(args, dt[1:1], more_args)" in result


def test_shorter_simulations_shorten_first_argument():
    code_str = """
    results_proxy = simulate_reservoir(proxy, info_level=0)
    """
    result = shorter_simulations(
        code=code_str,
    )
    assert "simulate_reservoir(proxy[1:1], info_level=0)" in result
