from abc import ABC, abstractmethod


class BaseSource(ABC):
    name: str

    @abstractmethod
    def fetch(self) -> list[dict]:
        """Return list of normalized job dicts.

        Each dict has keys: id, source, title, company, location,
        salary_min, salary_max, salary_is_predicted, url, date_posted.
        """
        ...
