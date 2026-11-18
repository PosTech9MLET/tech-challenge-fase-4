"""Geração de gráficos de fairness: ROC-AUC, FPR, FNR e recall por grupo."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # backend sem interface gráfica
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, roc_curve

from src.features.build import GENDER
from src.training.train import AGE_BINS, AGE_LABELS, error_rates


def _roc_curve_data(
    y_true: pd.Series, scores: np.ndarray
) -> tuple[np.ndarray, np.ndarray, float]:
    """Retorna FPR, TPR e AUC para uma curva ROC."""
    fpr, tpr, _ = roc_curve(y_true, scores)
    auc = float(roc_auc_score(y_true, scores))
    return fpr, tpr, auc


def plot_roc_by_group(
    x_val: pd.DataFrame,
    y_val: pd.Series,
    scores: np.ndarray,
    group_col: str,
    group_label: str,
    output: Path,
) -> Path:
    """Plota curvas ROC por subgrupo de um atributo.

    Args:
        x_val: features de validação (contém a coluna de grupo).
        y_val: rótulos reais.
        scores: probabilidades previstas.
        group_col: nome da coluna no ``x_val`` que define o grupo.
        group_label: rótulo humano do grupo (ex.: ``"Gênero"``).
        output: caminho do arquivo PNG de saída.

    Returns:
        Caminho do arquivo gerado.
    """
    proba = pd.Series(scores, index=y_val.index)
    fig, ax = plt.subplots(figsize=(6, 5))

    # Curva geral
    fpr, tpr, auc = _roc_curve_data(y_val, scores)
    ax.plot(
        fpr,
        tpr,
        color="black",
        linestyle="--",
        linewidth=1.5,
        label=f"Geral (AUC={auc:.4f})",
    )

    # Curvas por grupo
    if group_col == GENDER:
        groups = x_val[group_col].where(x_val[group_col].isin(["F", "M"]))
    elif group_col == "DAYS_BIRTH":
        groups = pd.cut(-x_val[group_col] / 365.25, AGE_BINS, labels=AGE_LABELS)
    else:
        groups = x_val[group_col]

    frame = pd.concat([y_val, proba, groups], axis=1, keys=["y", "s", "g"])
    colors = plt.cm.Set2(np.linspace(0, 1, frame["g"].dropna().nunique()))

    for (name, part), color in zip(
        frame.dropna(subset=["g"]).groupby("g", observed=True), colors, strict=False
    ):
        if part["y"].nunique() < 2:
            continue
        fpr_g, tpr_g, auc_g = _roc_curve_data(part["y"], part["s"])
        ax.plot(
            fpr_g, tpr_g, color=color, linewidth=1.5, label=f"{name} (AUC={auc_g:.4f})"
        )

    ax.plot([0, 1], [0, 1], color="gray", linestyle=":", linewidth=0.8)
    ax.set_xlabel("Taxa de Falsos Positivos (FPR)")
    ax.set_ylabel("Taxa de Verdadeiros Positivos (TPR / Recall)")
    ax.set_title(f"Curva ROC por {group_label}")
    ax.legend(loc="lower right", fontsize=8)
    ax.set_xlim(-0.01, 1.01)
    ax.set_ylim(-0.01, 1.01)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150)
    plt.close(fig)
    return output


def plot_error_rates_by_group(
    x_val: pd.DataFrame,
    y_val: pd.Series,
    scores: np.ndarray,
    threshold: float,
    group_col: str,
    group_label: str,
    output: Path,
) -> Path:
    """Plota FPR, FNR e recall por subgrupo em barras agrupadas.

    Args:
        x_val: features de validação (contém a coluna de grupo).
        y_val: rótulos reais.
        scores: probabilidades previstas.
        threshold: limiar de decisão.
        group_col: nome da coluna no ``x_val`` que define o grupo.
        group_label: rótulo humano do grupo (ex.: ``"Gênero"``).
        output: caminho do arquivo PNG de saída.

    Returns:
        Caminho do arquivo gerado.
    """
    proba = pd.Series(scores, index=y_val.index)
    y_pred = (proba >= threshold).astype(int)

    if group_col == GENDER:
        groups = x_val[group_col].where(x_val[group_col].isin(["F", "M"]))
    elif group_col == "DAYS_BIRTH":
        groups = pd.cut(-x_val[group_col] / 365.25, AGE_BINS, labels=AGE_LABELS)
    else:
        groups = x_val[group_col]

    frame = pd.concat([y_val, y_pred, groups], axis=1, keys=["y", "p", "g"])

    group_names: list[str] = []
    fpr_vals: list[float] = []
    fnr_vals: list[float] = []
    recall_vals: list[float] = []

    for name, part in frame.dropna(subset=["g"]).groupby("g", observed=True):
        rates = error_rates(part["y"], part["p"])
        group_names.append(str(name))
        fpr_vals.append(rates["fpr"])
        fnr_vals.append(rates["fnr"])
        recall_vals.append(rates["recall"])

    x = np.arange(len(group_names))
    width = 0.25
    fig, ax = plt.subplots(figsize=(7, 5))

    ax.bar(x - width, fpr_vals, width, label="FPR", color="#e74c3c")
    ax.bar(x, fnr_vals, width, label="FNR", color="#3498db")
    ax.bar(x + width, recall_vals, width, label="Recall", color="#2ecc71")

    ax.set_xticks(x)
    ax.set_xticklabels(group_names)
    ax.set_ylabel("Taxa")
    ax.set_title(f"FPR, FNR e Recall por {group_label}")
    ax.legend(fontsize=9)
    ax.set_ylim(0, 1.05)

    for i in range(len(group_names)):
        ax.text(
            i - width,
            fpr_vals[i] + 0.02,
            f"{fpr_vals[i]:.3f}",
            ha="center",
            fontsize=7,
        )
        ax.text(
            i,
            fnr_vals[i] + 0.02,
            f"{fnr_vals[i]:.3f}",
            ha="center",
            fontsize=7,
        )
        ax.text(
            i + width,
            recall_vals[i] + 0.02,
            f"{recall_vals[i]:.3f}",
            ha="center",
            fontsize=7,
        )

    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150)
    plt.close(fig)
    return output
