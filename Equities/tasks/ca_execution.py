# def execute_corporate_action(self, ca: CorporateActionBase) -> ExecutionResult:
#     """Execute a single corporate action"""
#     logger.info(f"Starting execution of {ca.action_type} for equity_id: {ca.equity_id}")
#
#     # Get appropriate executor
#     executor = self.executors.get(ca.action_type)
#     if not executor:
#         return ExecutionResult(
#             success=False,
#             message=f"No executor found for action type: {ca.action_type}",
#             execution_time=datetime.now(),
#             errors=[f"Unsupported action type: {ca.action_type}"]
#         )
#
#     # Validate before execution
#     validation_errors = executor.validate(ca)
#     if validation_errors:
#         return ExecutionResult(
#             success=False,
#             message="Validation failed",
#             execution_time=datetime.now(),
#             errors=validation_errors
#         )
#
#     # Check if execution date has arrived
#     if ca.execution_date > date.today():
#         return ExecutionResult(
#             success=False,
#             message=f"Execution date {ca.execution_date} has not arrived yet",
#             execution_time=datetime.now(),
#             errors=["Execution date not reached"]
#         )
#
#     # Execute the corporate action
#     return executor.execute(ca, session)
#
# def execute_batch(self, corporate_actions: List[CorporateActionBase]) -> Dict[
#     int, ExecutionResult]:
#     """Execute multiple corporate actions in priority order"""
#     # Sort by priority and execution date
#     sorted_actions = sorted(
#         corporate_actions,
#         key=lambda x: (x.priority.value, x.execution_date, x.created_at)
#     )
#
#     results = {}
#     for ca in sorted_actions:
#         if ca.status != StatusEnum.PENDING:
#             logger.info(f"Skipping CA {ca.id} - status is {ca.status}")
#             continue
#
#         result = self.execute_corporate_action(ca, session)
#         results[ca.id] = result
#
#         if not result.success:
#             logger.error(f"Failed to execute CA {ca.id}: {result.message}")
#         else:
#             logger.info(f"Successfully executed CA {ca.id}")
#
#     return results
