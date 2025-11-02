class TokenServiceError(Exception):
    pass

class InvalidTokenVersionError(TokenServiceError):
    pass

class UserAlreadyExistsError(Exception):
    pass

class UserNotFoundError(Exception):
    pass

class InstagramCredsAlreadyExistsError(Exception):
    pass

class InstagramCredsNotFoundError(Exception):
    pass

class PostNotFoundError(Exception):
    pass

class PostBaseContextNotFoundError(Exception):
    pass

class PostBaseContextAlreadyExistsError(Exception):
    pass

class WikibaseContextNotFoundError(Exception):
    pass

class WikibaseContextAlreadyExistsError(Exception):
    pass

