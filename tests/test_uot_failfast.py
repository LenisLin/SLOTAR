from __future__ import annotations

import numpy as np
import pytest

from slotar.exceptions import UOTInputError
from slotar.uot import UOTSolveConfig, solve_uot


def test_solve_uot_raises_on_empty_mass_source() -> None:
    a = np.array([0.0, 0.0])
    b = np.array([1.0, 1.0])
    C = np.zeros((2, 2))
    cfg = UOTSolveConfig(eps_schedule=[1.0])
    with pytest.raises(UOTInputError) as e:
        solve_uot(a=a, b=b, C=C, lam=1.0, cfg=cfg)
    assert "ERR_UOT_EMPTY_MASS_PRE" in str(e.value)


def test_solve_uot_raises_on_empty_support_after_prune() -> None:
    a = np.array([1.0, 1.0])
    b = np.array([1.0, 1.0])
    C = np.zeros((2, 2))
    cfg = UOTSolveConfig(eps_schedule=[1.0], n_min_proto=10.0)  # prunes everything
    with pytest.raises(UOTInputError) as e:
        solve_uot(a=a, b=b, C=C, lam=1.0, cfg=cfg)
    assert "ERR_UOT_EMPTY_SUPPORT" in str(e.value)
