from sqlalchemy.orm import Session

from Identifier_management.managers.generic_identifer_operations_manager import GenericOperationsManager
from Identifier_management.managers.generic_identifier_manager import GenericIdentifierManager
from Identifier_management.managers.generic_identifier_version_manager import GenericVersionManager
from Identifier_management.managers.generic_identifier_workflow_manager import GenericWorkflowManager


class GenericIdentifierServiceFactory:
    """Factory to create generic identifier managers for any asset class"""

    @staticmethod
    def create_identifier_manager(session: Session,
                                  history_model,
                                  snapshot_model,
                                  change_request_model,
                                  entity_model,
                                  identifier_enum_class,
                                  change_reason_enum_class=None) -> GenericIdentifierManager:
        """Create a complete generic identifier manager"""

        return GenericIdentifierManager(
            session=session,
            history_model=history_model,
            snapshot_model=snapshot_model,
            change_request_model=change_request_model,
            entity_model=entity_model,
            identifier_enum_class=identifier_enum_class,
            change_reason_enum_class=change_reason_enum_class
        )

    @staticmethod
    def create_version_manager(session: Session,
                               history_model,
                               identifier_enum_class,
                               change_reason_enum_class=None) -> GenericVersionManager:
        """Create just the version manager"""

        return GenericVersionManager(
            session=session,
            history_model=history_model,
            identifier_enum_class=identifier_enum_class,
            change_reason_enum_class=change_reason_enum_class
        )

    @staticmethod
    def create_workflow_manager(session: Session,
                                change_request_model,
                                version_manager: GenericVersionManager,
                                identifier_enum_class,
                                change_reason_enum_class=None) -> GenericWorkflowManager:
        """Create just the workflow manager"""

        return GenericWorkflowManager(
            session=session,
            change_request_model=change_request_model,
            version_manager=version_manager,
            identifier_enum_class=identifier_enum_class,
            change_reason_enum_class=change_reason_enum_class
        )

    @staticmethod
    def create_operations_manager(session: Session,
                                  snapshot_model,
                                  entity_model,
                                  version_manager: GenericVersionManager,
                                  identifier_enum_class,
                                  change_reason_enum_class=None) -> GenericOperationsManager:
        """Create just the operations manager"""

        return GenericOperationsManager(
            session=session,
            snapshot_model=snapshot_model,
            entity_model=entity_model,
            version_manager=version_manager,
            identifier_enum_class=identifier_enum_class,
            change_reason_enum_class=change_reason_enum_class
        )
