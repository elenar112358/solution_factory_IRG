from enum import StrEnum, auto


class Category(StrEnum):
    SUBSCRIPTION = auto()
    WARRANTY = auto()
    BILL = auto()
    INSURANCE = auto()


class Recurrence(StrEnum):
    MONTHLY = auto()
    QUARTERLY = auto()
    YEARLY = auto()


class Status(StrEnum):
    ACTIVE = auto()
    CANCELLED = auto()
    EXPIRED = auto()


class Currency(StrEnum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"