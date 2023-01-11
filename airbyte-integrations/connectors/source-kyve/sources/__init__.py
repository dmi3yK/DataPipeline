from .EVM import EVM
from .Uniswap import Uniswap

runtime_mapping = {
    "@kyvejs/evm": EVM,
    "@kyvejs/uniswap": Uniswap
    }