"""Contains classes for monitoring the blockchain"""
from .blockchain.utils import is_valid_address
from .transactions import OperationTypes, SimplifiedTransaction, RawTransaction
from .errors import CantSimplifyError, StellarAddressInvalidError

from typing import Optional, AsyncGenerator

import logging

logger = logging.getLogger(__name__)


async def single_monitor(kin_client: 'KinClient', address: str,
                         timeout: Optional[float] = None) -> AsyncGenerator[SimplifiedTransaction, None]:
    """
    Monitors a single account for kin payments

    :param kin_client: a kin client directed to the correct network
    :param address: address to watch
    :param timeout: How long to wait for a new event

    :raises: asyncio.TimeoutError: If too much time has passed between events (only if "timeout" is set)
    """
    if not is_valid_address(address):
        raise StellarAddressInvalidError('invalid address: {}'.format(address))

    sse_client = await kin_client.horizon.account_transactions(address, sse=True, sse_timeout=timeout)

    async for tx in sse_client:
        try:
            tx_data = SimplifiedTransaction(RawTransaction(tx))
        except CantSimplifyError:
            logger.debug("SSE transaction couldn't be simplified: ", tx)
            continue

        if tx_data.operation.type != OperationTypes.PAYMENT:
            logger.debug("Non-payment SSE transaction skipped: ", tx_data)
            continue

        yield tx_data


async def multi_monitor(kin_client: 'KinClient') -> AsyncGenerator[SimplifiedTransaction, None]:
    """
    Monitors a single account for kin payments

    :param kin_client: a kin client directed to the correct network
    :param addresses: set of addresses to watch
    """

    sse_client = await kin_client.horizon.transactions(sse=True)

    async for tx in sse_client:
        try:
            # tx_data = SimplifiedTransaction(RawTransaction(tx))
            tx_data = RawTransaction(tx)

        except CantSimplifyError:
            logger.debug("SSE transaction couldn't be simplified: ", tx)
            continue
        except TypeError as e:
            logger.debug(e)
            continue

        # if tx_data.operation.type != OperationTypes.PAYMENT:
            # logger.debug("Non-payment SSE transaction skipped: ", tx_data)
            # continue

        # Will yield twice if both of these are correct. (someone sent to himself) - which it fine
        yield tx_data.source, tx_data
