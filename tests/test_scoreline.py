import math
from engine.scoreline import poisson_pmf


def test_poisson_pmf_zero():
    # P(X=0; λ=1) = e^-1
    assert poisson_pmf(0, 1.0) == math.exp(-1.0)


def test_poisson_pmf_known_value():
    # P(X=2; λ=2) = e^-2 * 2^2 / 2! = 2 e^-2
    assert math.isclose(poisson_pmf(2, 2.0), 2 * math.exp(-2.0), rel_tol=1e-12)


def test_poisson_pmf_negative_k_is_zero():
    assert poisson_pmf(-1, 1.5) == 0.0


from engine.scoreline import score_matrix


def _matrix_sum(m):
    return sum(cell for row in m for cell in row)


def test_score_matrix_normalized():
    m = score_matrix(1.4, 1.1)
    assert math.isclose(_matrix_sum(m), 1.0, rel_tol=1e-9)


def test_score_matrix_dimensions():
    m = score_matrix(1.4, 1.1, max_goals=10)
    assert len(m) == 11 and all(len(row) == 11 for row in m)


def test_score_matrix_rho_zero_is_plain_poisson():
    # rho=0 时 (1,1) 单元应等于归一化前的 pmf 乘积比例
    m = score_matrix(1.5, 1.2, rho=0.0)
    # 平局对角线之和应为正且 <1
    diag = sum(m[i][i] for i in range(len(m)))
    assert 0.0 < diag < 1.0


def test_dixon_coles_lowers_draw_inflation():
    # rho<0 提高 0:0/1:1，降低 0:1/1:0（DC 对低分修正）
    plain = score_matrix(1.3, 1.3, rho=0.0)
    dc = score_matrix(1.3, 1.3, rho=-0.05)
    assert dc[0][0] > plain[0][0]
