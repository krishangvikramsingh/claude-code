class PlatformError(Exception):
    message = "The request could not be completed."


class DuplicateAccount(PlatformError):
    message = "An account with this email already exists."


class InvalidCollegeEmail(PlatformError):
    message = "Please use your college email address."


class InvalidCredentials(PlatformError):
    message = "Incorrect email or password."


class AccountLocked(PlatformError):
    message = "Too many failed attempts. Try again in 15 minutes."


class AccountSuspended(PlatformError):
    message = "This account has been suspended. Contact an administrator."


class NotVerified(PlatformError):
    message = "Complete college verification before posting reviews."


class NotAuthorised(PlatformError):
    message = "You do not have permission to do this."


class InvalidReview(PlatformError):
    message = "The review could not be accepted."


class DuplicateReview(PlatformError):
    message = "You have already reviewed this place."


class DuplicateReport(PlatformError):
    message = "You have already reported this review."


class InvalidInput(PlatformError):
    message = "Some fields are missing or invalid."


class NotFound(PlatformError):
    message = "The requested item does not exist."
