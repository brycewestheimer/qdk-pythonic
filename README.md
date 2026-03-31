# qdk-pythonic

A Pythonic circuit-builder API for the Microsoft Quantum Development Kit.

> This project is under active development. See the [design document](docs/design/design_document.md) for architecture and API details.

## Quick start

```python
from qdk_pythonic import Circuit

circ = Circuit()
q = circ.allocate(2)
circ.h(q[0]).cx(q[0], q[1]).measure_all()

print(circ.to_qsharp())
results = circ.run(shots=1000)
estimate = circ.estimate()
```

## License

[MIT](LICENSE)
