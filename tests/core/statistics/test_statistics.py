import pytest

from app.core.facade import (
    BitcoinWalletCore,
    StatisticsResponse,
    UserResponse,
    WalletResponse,
)
from app.core.transactions.interactor import Transaction
from app.core.users.interactor import User
from app.infra.in_memory.in_memory_api_key_repository import InMemoryAPIKeyRepository
from app.infra.in_memory.in_memory_transactions_repository import (
    InMemoryTransactionsRepository,
)
from app.infra.in_memory.in_memory_users_repository import InMemoryUsersRepository
from app.infra.in_memory.in_memory_wallets_repository import InMemoryWalletsRepository
from app.infra.utils.currency_converter import DefaultCurrencyConverter
from app.infra.utils.fee_strategy import FeeRateStrategy
from app.infra.utils.generator import DefaultUniqueValueGenerators
from app.infra.utils.hasher import DefaultHashFunction

hash_function: DefaultHashFunction = DefaultHashFunction()
currency_converter: DefaultCurrencyConverter = DefaultCurrencyConverter()
fee_strategy: FeeRateStrategy = FeeRateStrategy()


@pytest.fixture
def core() -> BitcoinWalletCore:
    users_repository: InMemoryUsersRepository = InMemoryUsersRepository()
    wallets_repository: InMemoryWalletsRepository = InMemoryWalletsRepository()
    api_key_repository: InMemoryAPIKeyRepository = InMemoryAPIKeyRepository()
    transactions_repository: InMemoryTransactionsRepository = (
        InMemoryTransactionsRepository()
    )
    return BitcoinWalletCore.create(
        users_repository=users_repository,
        wallets_repository=wallets_repository,
        api_key_repository=api_key_repository,
        transactions_repository=transactions_repository,
        hash_function=DefaultHashFunction(),
        currency_converter=DefaultCurrencyConverter(),
        fee_strategy=FeeRateStrategy(),
        unique_value_generator=DefaultUniqueValueGenerators(),
    )


@pytest.fixture
def user1() -> User:
    username: str = "Mamuka"
    password: str = "password"

    return User(_user_id=0, _username=username, _password=password)


@pytest.fixture
def user2() -> User:
    username: str = "Gocha"
    password: str = "password"

    return User(_user_id=1, _username=username, _password=password)


def test_deposit_and_statistics(user1: User, core: BitcoinWalletCore) -> None:
    api_key: str = core.register_user(
        username=user1.get_username(), password=user1.get_password()
    ).api_key
    address: str = core.create_wallet(api_key=api_key).wallet_info["address"] or ""
    core.deposit(api_key=api_key, address=address, amount_in_usd=1000)

    statistics_response: StatisticsResponse = core.get_statistics(
        admin_api_key="admin_api_key"
    )

    assert statistics_response.platform_profit_in_usd == 0
    assert statistics_response.platform_profit_in_btc == 0
    assert statistics_response.total_number_of_transactions == 1


def test_withdraw_and_statistics(user1: User, core: BitcoinWalletCore) -> None:
    api_key: str = core.register_user(
        username=user1.get_username(), password=user1.get_password()
    ).api_key
    address: str = core.create_wallet(api_key=api_key).wallet_info["address"]
    core.withdraw(api_key=api_key, address=address, amount_in_usd=1000)

    statistics_response: StatisticsResponse = core.get_statistics(
        admin_api_key="admin_api_key"
    )

    assert statistics_response.platform_profit_in_usd == 0
    assert statistics_response.platform_profit_in_btc == 0
    assert statistics_response.total_number_of_transactions == 1


def test_deposit_withdraw_statistics(user1: User, core: BitcoinWalletCore) -> None:
    api_key: str = core.register_user(
        username=user1.get_username(), password=user1.get_password()
    ).api_key
    address: str = core.create_wallet(api_key=api_key).wallet_info["address"]
    core.deposit(api_key=api_key, address=address, amount_in_usd=100000)
    core.withdraw(api_key=api_key, address=address, amount_in_usd=1000)

    statistics_response: StatisticsResponse = core.get_statistics(
        admin_api_key="admin_api_key"
    )

    assert statistics_response.platform_profit_in_usd == 0
    assert statistics_response.platform_profit_in_btc == 0
    assert statistics_response.total_number_of_transactions == 2


def test_deposit_and_transaction_to_same_wallet_neg_user_has_two_wallets(
    user1: User, core: BitcoinWalletCore
) -> None:
    api_key: str = core.register_user(
        username=user1.get_username(), password=user1.get_password()
    ).api_key

    address1: str = core.create_wallet(api_key=api_key).wallet_info["address"]
    assert address1 != ""
    address1 = core.create_wallet(api_key=api_key).wallet_info["address"]

    amount: float = 1
    core.make_transaction(
        api_key=api_key, from_address=address1, to_address=address1, amount=amount
    )

    statistics_response: StatisticsResponse = core.get_statistics(
        admin_api_key="admin_api_key"
    )
    assert statistics_response.platform_profit_in_usd == 0
    assert statistics_response.platform_profit_in_btc == 0
    assert statistics_response.total_number_of_transactions == 0


def test_deposit_and_transaction_to_same_wallet_neg_user_has_one_wallet(
    user1: User, core: BitcoinWalletCore
) -> None:
    api_key: str = core.register_user(
        username=user1.get_username(), password=user1.get_password()
    ).api_key

    address1: str = core.create_wallet(api_key=api_key).wallet_info["address"]

    amount: float = 1
    core.make_transaction(
        api_key=api_key, from_address=address1, to_address=address1, amount=amount
    )

    statistics_response: StatisticsResponse = core.get_statistics(
        admin_api_key="admin_api_key"
    )
    assert statistics_response.platform_profit_in_usd == 0
    assert statistics_response.platform_profit_in_btc == 0
    assert statistics_response.total_number_of_transactions == 0


def test_deposit_and_transaction_to_different_wallet_of_same_user(
    user1: User, core: BitcoinWalletCore
) -> None:
    api_key: str = core.register_user(
        username=user1.get_username(), password=user1.get_password()
    ).api_key

    address1: str = core.create_wallet(api_key=api_key).wallet_info["address"]
    address2: str = core.create_wallet(api_key=api_key).wallet_info["address"]

    amount: float = 1
    core.make_transaction(
        api_key=api_key, from_address=address1, to_address=address2, amount=amount
    )

    statistics_response: StatisticsResponse = core.get_statistics(
        admin_api_key="admin_api_key"
    )
    assert (
        statistics_response.platform_profit_in_usd
        == currency_converter.convert_to_usd(
            amount_in_btc=amount * fee_strategy.get_fee_rate_for_same_owner()
        )
    )
    assert (
        statistics_response.platform_profit_in_btc
        == amount * fee_strategy.get_fee_rate_for_same_owner()
    )
    assert statistics_response.total_number_of_transactions == 1


def test_transaction_to_other_user_wallet_neg_no_funds(
    user1: User, user2: User, core: BitcoinWalletCore
) -> None:
    api_key1: str = core.register_user(
        username=user1.get_username(), password=user1.get_password()
    ).api_key

    api_key2: str = core.register_user(
        username=user2.get_username(), password=user2.get_password()
    ).api_key

    address1: str = core.create_wallet(api_key=api_key1).wallet_info["address"]
    address2: str = core.create_wallet(api_key=api_key2).wallet_info["address"]

    amount: float = 10
    core.make_transaction(
        api_key=api_key1, from_address=address1, to_address=address2, amount=amount
    )

    statistics_response: StatisticsResponse = core.get_statistics(
        admin_api_key="admin_api_key"
    )
    assert statistics_response.platform_profit_in_usd == 0
    assert statistics_response.platform_profit_in_btc == 0
    assert statistics_response.total_number_of_transactions == 0


# transaction with insufficient funds


def test_deposit_and_transaction_to_different_wallet_of_same_user_neg_no_funds(
    user1: User, core: BitcoinWalletCore
) -> None:
    api_key: str = core.register_user(
        username=user1.get_username(), password=user1.get_password()
    ).api_key

    address1: str = core.create_wallet(api_key=api_key).wallet_info["address"]
    address2: str = core.create_wallet(api_key=api_key).wallet_info["address"]

    amount: float = 10
    core.make_transaction(
        api_key=api_key, from_address=address1, to_address=address2, amount=amount
    )

    statistics_response: StatisticsResponse = core.get_statistics(
        admin_api_key="admin_api_key"
    )
    assert statistics_response.platform_profit_in_usd == 0
    assert (
        statistics_response.platform_profit_in_btc
        == amount * fee_strategy.get_fee_rate_for_same_owner()
    )
    assert statistics_response.total_number_of_transactions == 0


def test_empty_get_statistics_with_wrong_api_key(core: BitcoinWalletCore) -> None:
    assert core.get_statistics("wrong_key").status == 403


def test_get_transactions(user1: User, user2: User, core: BitcoinWalletCore) -> None:
    user_response1: UserResponse = core.register_user(
        username=user1.get_username(), password=user1.get_password()
    )
    wallet_response1: WalletResponse = core.create_wallet(
        api_key=user_response1.api_key
    )

    user_response2: UserResponse = core.register_user(
        username=user2.get_username(), password=user2.get_password()
    )
    wallet_response2: WalletResponse = core.create_wallet(
        api_key=user_response2.api_key
    )

    transaction1: Transaction = Transaction(
        from_address="DEPOSIT",
        to_address=wallet_response1.wallet_info["address"],
        amount=currency_converter.convert_to_btc(amount_in_usd=100),
        fee=float(
            fee_strategy.get_fee_rate_for_deposit()
            * currency_converter.convert_to_btc(amount_in_usd=100)
        ),
    )
    core.deposit(
        api_key=user_response1.api_key,
        address=wallet_response1.wallet_info["address"],
        amount_in_usd=100,
    )
    transaction2: Transaction = Transaction(
        from_address=wallet_response1.wallet_info["address"],
        to_address="WITHDRAW",
        amount=currency_converter.convert_to_btc(amount_in_usd=50),
        fee=float(
            fee_strategy.get_fee_rate_for_withdraw()
            * currency_converter.convert_to_btc(amount_in_usd=100)
        ),
    )
    core.withdraw(
        api_key=user_response1.api_key,
        address=wallet_response1.wallet_info["address"],
        amount_in_usd=50,
    )
    transaction3: Transaction = Transaction(
        from_address=wallet_response1.wallet_info["address"],
        to_address=wallet_response2.wallet_info["address"],
        amount=0.3,
        fee=float(fee_strategy.get_fee_rate_for_different_owners() * 0.3),
    )
    core.make_transaction(
        api_key=user_response1.api_key,
        from_address=wallet_response1.wallet_info["address"],
        to_address=wallet_response2.wallet_info["address"],
        amount=0.3,
    )

    assert (
        core.get_transactions_of_wallet(
            api_key=user_response1.api_key + "wrong",
            address=wallet_response1.wallet_info["address"],
        ).status
        == 403
    )
    assert (
        core.get_transactions_of_wallet(
            api_key=user_response1.api_key,
            address=wallet_response1.wallet_info["address"] + "wrong",
        ).status
        == 404
    )
    assert (
        core.get_transactions_of_wallet(
            api_key=user_response2.api_key,
            address=wallet_response1.wallet_info["address"],
        ).status
        == 403
    )
    # TODO test for correct transactions list
    assert (
        core.get_transactions_of_wallet(
            api_key=user_response1.api_key,
            address=wallet_response1.wallet_info["address"],
        ).status
        == 200
    )
    assert core.get_transactions_of_wallet(
        api_key=user_response1.api_key,
        address=wallet_response1.wallet_info["address"],
    ).transactions == [
        transaction1.to_dict(),
        transaction2.to_dict(),
        transaction3.to_dict(),
    ]
