class PlatformError(Exception):
    pass


class DuplicateAccount(PlatformError):
    pass


class InvalidCollegeEmail(PlatformError):
    pass


class InvalidCredentials(PlatformError):
    pass


class AccountLocked(PlatformError):
    pass


class NotVerified(PlatformError):
    pass


class NotAuthorised(PlatformError):
    pass


class InvalidReview(PlatformError):
    pass


class DuplicateReport(PlatformError):
    pass


class NotFound(PlatformError):
    pass
