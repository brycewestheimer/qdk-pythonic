"""Quantum machine learning: feature encoding, kernels, classifiers.

Example::

    from qdk_pythonic.domains.ml import AngleEncoding, QuantumKernel

    encoding = AngleEncoding(n_features=4)
    kernel = QuantumKernel(encoding)
    circuit = kernel.to_circuit(x=[0.1, 0.2, 0.3, 0.4],
                                 y=[0.5, 0.6, 0.7, 0.8])
"""

from qdk_pythonic.domains.ml.encoding import AmplitudeEncoding, AngleEncoding
from qdk_pythonic.domains.ml.kernels import QuantumKernel
from qdk_pythonic.domains.ml.variational import VariationalClassifier

__all__ = [
    "AmplitudeEncoding",
    "AngleEncoding",
    "QuantumKernel",
    "VariationalClassifier",
]
