class DomainError(Exception):
    pass


class UserNotFoundError(DomainError):
    def __init__(self, identifier: str | None = None):
        msg = f"User '{identifier}' not found." if identifier else "User not found."
        super().__init__(msg)


class UserAlreadyExistsError(DomainError):
    def __init__(self, field_name: str, value: str):
        super().__init__(f"User with {field_name} '{value}' already exists.")


class GroupNotFoundError(DomainError):
    def __init__(self, group_id: int):
        super().__init__(f"Group with id {group_id} not found.")
