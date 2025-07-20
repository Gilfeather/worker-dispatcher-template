import pytest
from app.infrastructure.exceptions import (
    DomainException,
    InfrastructureException,
    PresentationException,
    TaskNotFoundException,
    WorkerUnavailableException,
    WorkerNotFoundException,
    TaskExecutionException,
    DatabaseConnectionException,
    ExternalServiceException,
    S3ServiceException,
    SlackServiceException,
    GCPServiceException,
    AMCServiceException,
)


class TestDomainExceptions:
    def test_domain_exception(self):
        with pytest.raises(DomainException):
            raise DomainException("Test domain exception")

    def test_task_not_found_exception(self):
        with pytest.raises(TaskNotFoundException):
            raise TaskNotFoundException("Task not found")

        # Test inheritance
        with pytest.raises(DomainException):
            raise TaskNotFoundException("Task not found")

    def test_worker_unavailable_exception(self):
        with pytest.raises(WorkerUnavailableException):
            raise WorkerUnavailableException("Worker unavailable")

        # Test inheritance
        with pytest.raises(DomainException):
            raise WorkerUnavailableException("Worker unavailable")

    def test_worker_not_found_exception(self):
        with pytest.raises(WorkerNotFoundException):
            raise WorkerNotFoundException("Worker not found")

        # Test inheritance
        with pytest.raises(DomainException):
            raise WorkerNotFoundException("Worker not found")

    def test_task_execution_exception(self):
        with pytest.raises(TaskExecutionException):
            raise TaskExecutionException("Task execution failed")

        # Test inheritance
        with pytest.raises(DomainException):
            raise TaskExecutionException("Task execution failed")


class TestInfrastructureExceptions:
    def test_infrastructure_exception(self):
        with pytest.raises(InfrastructureException):
            raise InfrastructureException("Test infrastructure exception")

    def test_database_connection_exception(self):
        with pytest.raises(DatabaseConnectionException):
            raise DatabaseConnectionException("Database connection failed")

        # Test inheritance
        with pytest.raises(InfrastructureException):
            raise DatabaseConnectionException("Database connection failed")

    def test_external_service_exception(self):
        with pytest.raises(ExternalServiceException):
            raise ExternalServiceException("External service failed")

        # Test inheritance
        with pytest.raises(InfrastructureException):
            raise ExternalServiceException("External service failed")

    def test_s3_service_exception(self):
        with pytest.raises(S3ServiceException):
            raise S3ServiceException("S3 service failed")

        # Test inheritance
        with pytest.raises(InfrastructureException):
            raise S3ServiceException("S3 service failed")

    def test_slack_service_exception(self):
        with pytest.raises(SlackServiceException):
            raise SlackServiceException("Slack service failed")

        # Test inheritance
        with pytest.raises(InfrastructureException):
            raise SlackServiceException("Slack service failed")

    def test_gcp_service_exception(self):
        with pytest.raises(GCPServiceException):
            raise GCPServiceException("GCP service failed")

        # Test inheritance
        with pytest.raises(InfrastructureException):
            raise GCPServiceException("GCP service failed")

    def test_amc_service_exception(self):
        with pytest.raises(AMCServiceException):
            raise AMCServiceException("AMC service failed")

        # Test inheritance
        with pytest.raises(InfrastructureException):
            raise AMCServiceException("AMC service failed")


class TestPresentationExceptions:
    def test_presentation_exception(self):
        with pytest.raises(PresentationException):
            raise PresentationException("Test presentation exception")
