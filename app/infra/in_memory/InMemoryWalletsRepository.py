from collections import defaultdict
from typing import DefaultDict, Optional, List

from app.core.wallets.interactor import Wallet


class InMemoryWalletsRepository:
    _wallets: DefaultDict[str, Wallet]

    def __init__(self) -> None:
        self._wallets = defaultdict()

    # WALLET
    def add_wallet(
        self, wallet: Wallet
    ) -> None:  # address is generated by the system and is unique
        self._wallets[wallet.get_address()] = wallet

    def get_wallet(self, address: str) -> Optional[Wallet]:
        return self._wallets.get(address, None)

    def deposit(self, address: str, amount: float) -> bool:
        if address in self._wallets.keys():
            self._wallets[address].deposit(amount=amount)
            return True
        return False

    def withdraw(self, address: str, amount: float) -> bool:
        if address in self._wallets.keys():
            self._wallets[address].withdraw(amount=amount)
            return True
        return False

    def get_all_wallets_of_user(self, user_id: int) -> List[Wallet]:
        user_wallets: List[Wallet] = []
        for _, wallet in self._wallets.items():
            if wallet.get_owner_id() == user_id:
                user_wallets.append(wallet)
        return user_wallets

    def get_number_of_wallets_of_user(self, user_id: int) -> int:
        return len(self.get_all_wallets_of_user(user_id))
