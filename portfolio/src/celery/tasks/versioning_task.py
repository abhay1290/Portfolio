# @app.task(bind=True)
# def execute_portfolio_rebalance(self, portfolio_id: int, rebalance_data: dict):
#     db = SessionLocal()
#     try:
#         portfolio = db.query(Portfolio).get(portfolio_id)
#         if not portfolio:
#             raise ValueError("Portfolio not found")
#
#         # Perform rebalance operations...
#         # This would modify the portfolio and its constituents
#
#         # Create version for the rebalance
#         version_manager = PortfolioVersioningManager(db)
#         version = version_manager.create_version(
#             portfolio=portfolio,
#             operation_type=VersionOperationTypeEnum.REBALANCE,
#             change_reason=f"Automatic rebalance: {rebalance_data['reason']}",
#             created_by="system"
#         )
#
#         # Update portfolio
#         portfolio.current_version_id = version.id
#         portfolio.version = version.version_id
#         portfolio.version_hash = version.state_hash
#         portfolio.updated_at = datetime.now()
#
#         db.commit()
#         return {"status": "success", "new_version": version.version_id}
#     except Exception as e:
#         db.rollback()
#         raise self.retry(exc=e)
#     finally:
#         db.close()
#
#
# @app.task
# def verify_portfolio_versions_integrity():
#     db = SessionLocal()
#     try:
#         version_manager = PortfolioVersioningManager(db)
#         corrupted_versions = []
#
#         # Check all versions
#         versions = db.query(PortfolioVersion).all()
#         for version in versions:
#             # Recompute hash
#             snapshot = PortfolioStateSnapshot(
#                 portfolio_data=version.portfolio_state,
#                 constituents_data=version.constituents_state,
#                 timestamp=version.created_at
#             )
#             computed_hash = version_manager._generate_state_hash(snapshot)
#
#             if computed_hash != version.state_hash:
#                 corrupted_versions.append({
#                     "version_id": version.id,
#                     "portfolio_id": version.portfolio_id,
#                     "stored_hash": version.state_hash,
#                     "computed_hash": computed_hash
#                 })
#
#         if corrupted_versions:
#             alert_admins(corrupted_versions)
#             return {"status": "issues_found", "corrupted_versions": corrupted_versions}
#         return {"status": "ok"}
#     finally:
#         db.close()
