"""Reporting use cases."""

from store.domain.ports import OrderRepositoryPort


class ReportController:
    def __init__(self, repository: OrderRepositoryPort):
        self.repository = repository

    def sales(self) -> dict:
        return self.repository.report()
