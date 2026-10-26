"""Small statistics helpers for the Cookie Cats analysis."""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

DATA = Path(__file__).resolve().parents[1] / "data" / "cookie_cats.csv"


def load(path=DATA):
    return pd.read_csv(path)


def sample_ratio_check(counts):
    """Chi-square test of arm sizes against an equal split."""
    return stats.chisquare(np.asarray(counts, float))


def diff_in_props(treat, ctrl):
    """Difference in proportions (treat - ctrl): pooled z-test p-value, Wald 95% CI."""
    t, c = np.asarray(treat, float), np.asarray(ctrl, float)
    pt, pc = t.mean(), c.mean()
    se = np.sqrt(pt * (1 - pt) / t.size + pc * (1 - pc) / c.size)
    pool = (t.sum() + c.sum()) / (t.size + c.size)
    se0 = np.sqrt(pool * (1 - pool) * (1 / t.size + 1 / c.size))
    z = (pt - pc) / se0
    return {"diff": pt - pc, "lo": pt - pc - 1.96 * se, "hi": pt - pc + 1.96 * se,
            "p": 2 * stats.norm.sf(abs(z))}


def bootstrap_diff(treat, ctrl, n_boot=10000, seed=0):
    """Bootstrap percentile 95% CI for a difference in means."""
    rng = np.random.default_rng(seed)
    t, c = np.asarray(treat, float), np.asarray(ctrl, float)
    boots = np.array([rng.choice(t, t.size).mean() - rng.choice(c, c.size).mean() for _ in range(n_boot)])
    return {"diff": t.mean() - c.mean(), "lo": np.percentile(boots, 2.5), "hi": np.percentile(boots, 97.5)}


def holm(pvals):
    return multipletests(pvals, method="holm")[1]


def n_per_arm(baseline, mde_abs, alpha=0.05, power=0.8):
    """Sample size per arm to detect an absolute change in a proportion."""
    es = proportion_effectsize(baseline + mde_abs, baseline)
    return int(np.ceil(NormalIndPower().solve_power(es, alpha=alpha, power=power, ratio=1)))
