import numpy as np
import pytest

from app import add_point, classical_mds, schoenberg_D, wake_matrix, wind_vector


def sq_dists(P):
    return ((P[:, None] - P[None]) ** 2).sum(-1)


def test_doc_example():
    q = np.array([[0, 0], [-500, -500 * np.sqrt(3)], [-1000, -1000 * np.sqrt(3)]])
    W = wake_matrix(q @ wind_vector(240), 1e-3)
    np.testing.assert_allclose(W, [[0, 1 / 6, 2 / 27], [0, 0, 1 / 6], [0, 0, 0]], atol=1e-12)


@pytest.mark.parametrize("n", [2, 3, 4, 7, 15, 30])
def test_mds_is_exact(n):
    s = np.random.default_rng(n).uniform(-2000, 2000, n)
    D = schoenberg_D(s, s, 1e-3)
    W = wake_matrix(s, 1e-3)
    np.testing.assert_allclose(2 / 3 - (W + W.T), D + 2 / 3 * np.eye(n), atol=1e-12)
    Z, lam = classical_mds(D)
    assert lam[-1] > -1e-12
    assert Z.shape[1] == n - 1
    np.testing.assert_allclose(sq_dists(Z), D, atol=1e-10)


@pytest.mark.parametrize("n_existing", [1, 3, 6])
def test_next_turbine_is_exact(n_existing):
    rng = np.random.default_rng(n_existing)
    s = rng.uniform(-2000, 2000, n_existing)
    s_new = np.append(rng.uniform(-2500, 2500, 50), s)
    Y, x_par, h = add_point(s, s_new, 1e-3)
    np.testing.assert_allclose(h[-n_existing:], 0, atol=1e-6)
    for x, hk, sk in zip(x_par, h, s_new):
        P = np.vstack([np.column_stack([Y, np.zeros(n_existing)]), np.append(x, hk)])
        all_s = np.append(s, sk)
        np.testing.assert_allclose(sq_dists(P), schoenberg_D(all_s, all_s, 1e-3), atol=1e-10)
