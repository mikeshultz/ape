""" Script to generate a python const file with public chain RPC endpoints from the Ethereum
Foundation ethereum-lists/chains repo.

Usage
-----
python scripts/update_rpc.py
"""
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urljoin

import requests
from pydantic import BaseModel

from ape.logging import logger

CHAIN_IDS = {
    "base": {
        "mainnet": 8453,
        "sepolia": 84532,
    },
    "ethereum": {
        "mainnet": 1,
        "goerli": 5,
        "sepolia": 11155111,
    },
    "gnosis": {
        "mainnet": 100,
    },
    "polygon": {
        "mainnet": 137,
        "mumbai": 80001,
    },
    "polygon-zkevm": {
        "mainnet": 1101,
        "testnet": 1442,
    },
}
INCLUDE_PROTOCOLS = ["http", "https"]
SOURCE_URL = "https://raw.githubusercontent.com/ethereum-lists/chains/master/_data/chains/"
CHAIN_CONST_FILE = Path(__file__).parent.parent / "src" / "ape_geth" / "chains.py"


class Chain(BaseModel):
    name: str
    chain: str
    icon: Optional[str] = None
    rpc: list[str]
    features: Optional[list[dict[str, str]]] = None
    faucets: list[str]
    nativeCurrency: dict[str, Any]
    infoURL: str
    shortName: str
    chainId: int
    networkId: int
    slip44: Optional[int] = None
    ens: Optional[dict[str, str]] = None
    explorers: list[dict[str, str]]


def stamp() -> str:
    """UTC timestamp for file header"""
    return str(datetime.utcnow())


def ensure_dict(d: dict[str, Any], key: str):
    if key in d and isinstance(d[key], dict):
        return
    d[key] = dict()


def fetch_chain(chain_id: int) -> Chain:
    """Fetch a chain from the ethereum-lists repo."""
    url = urljoin(SOURCE_URL, f"eip155-{chain_id}.json")

    logger.info(f"GET {url}")
    r = requests.get(url)

    if r.status_code != 200:
        raise Exception(f"Failed to fetch {url}")

    chain = Chain.model_validate_json(r.text)

    # Filter out unwanted protocols (e.g. websocket)
    chain.rpc = list(filter(lambda rpc: rpc.split(":")[0] in INCLUDE_PROTOCOLS, chain.rpc))

    return chain


def fetch_chains() -> dict[str, dict[str, Chain]]:
    """Fetch all chains from the ethereum-lists repo."""
    chains: dict[str, dict[str, Chain]] = {}
    for ecosystem in CHAIN_IDS.keys():
        for network, chain_id in CHAIN_IDS[ecosystem].items():
            logger.info(f"Fetching chain {ecosystem}:{network} ({chain_id})")
            ensure_dict(chains, ecosystem)
            chains[ecosystem][network] = fetch_chain(chain_id)
    return chains


def write_chain_const(chains: dict[str, dict[str, Chain]]):
    """Write the file with Python constant"""
    with CHAIN_CONST_FILE.open("w") as const_file:
        const_file.write("# This file is auto-generated by scripts/update_rpc.py\n")
        const_file.write(f"# {stamp()}\n")
        const_file.write("# Do not edit this file directly.\n")
        const_file.write("PUBLIC_CHAIN_RPCS: dict[str, dict[str, list[str]]] = {\n")
        for ecosystem in chains.keys():
            const_file.write(f'    "{ecosystem}": {{\n')
            for network, chain in chains[ecosystem].items():
                const_file.write(f'        "{network}": [\n')
                for rpc in chain.rpc:
                    if "${" in rpc:
                        continue
                    const_file.write(f'            "{rpc}",\n')
                const_file.write("        ],\n")
            const_file.write("    },\n")
        const_file.write("}\n")


def main():
    logger.info("Fetching chain data...")
    logger.info(f"    Source: {SOURCE_URL}")
    logger.info(f"    Dest: {CHAIN_CONST_FILE}")
    chains = fetch_chains()
    write_chain_const(chains)


if __name__ == "__main__":
    main()
