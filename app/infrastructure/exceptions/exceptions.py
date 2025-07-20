class DomainException(Exception):
    pass


class InfrastructureException(Exception):
    pass


class PresentationException(Exception):
    pass


class TaskNotFoundException(DomainException):
    pass


class WorkerUnavailableException(DomainException):
    pass


class WorkerNotFoundException(DomainException):
    pass


class TaskExecutionException(DomainException):
    pass


class DatabaseConnectionException(InfrastructureException):
    pass


class ExternalServiceException(InfrastructureException):
    pass


class S3ServiceException(InfrastructureException):
    pass


class SlackServiceException(InfrastructureException):
    pass


class GCPServiceException(InfrastructureException):
    pass


class AMCServiceException(InfrastructureException):
    pass
