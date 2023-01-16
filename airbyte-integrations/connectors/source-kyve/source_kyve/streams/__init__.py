from .evm import EVM
from .uniswap import Uniswap

runtime_mapping = {
    "@kyvejs/evm": EVM,
    "@kyvejs/uniswap": Uniswap
}
