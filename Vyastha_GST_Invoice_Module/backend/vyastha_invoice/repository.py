from __future__ import annotations

import asyncio
from copy import deepcopy


class InvoiceRepository:
    """Development adapter.

    Replace these methods with the existing Vyastha MongoDB repository/service.
    Do not use this in production for multi-worker deployments.
    """

    def __init__(self):
        self._data = {}
        self._lock = asyncio.Lock()

    async def create(self, invoice):
        async with self._lock:
            if invoice.invoice_number in {x.invoice_number for x in self._data.values()}:
                raise ValueError("Invoice number already exists")
            self._data[invoice.id] = deepcopy(invoice)
            return deepcopy(invoice)

    async def get(self, invoice_id):
        return deepcopy(self._data.get(invoice_id))

    async def list(self):
        return [deepcopy(x) for x in self._data.values()]

    async def next_number(self):
        async with self._lock:
            nums = []
            for x in self._data.values():
                try:
                    nums.append(int(x.invoice_number.replace("INV-", "")))
                except ValueError:
                    pass
            return f"INV-{max(nums, default=0) + 1:05d}"
