from .evm import EVM
from .uniswap import Uniswap
from .bitcoin import Bitcoin
from .celo import Celo
from .cosmos import Cosmos

runtime_mapping = {
    "@kyvejs/bitcoin": Bitcoin,
    "@kyvejs/celo": Celo,
    "@kyvejs/cosmos": Cosmos,
    "@kyvejs/evm": EVM,
    "@kyvejs/uniswap": Uniswap,
}
