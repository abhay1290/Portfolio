# utils/decorators.py
import functools
import logging
import time
from typing import Callable

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def transaction_rollback(func: Callable) -> Callable:
    """Decorator to handle database transaction rollbacks"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        session = None
        # Try to find session in arguments
        for arg in args:
            if isinstance(arg, Session):
                session = arg
                break

        if 'session' in kwargs:
            session = kwargs['session']

        if not session:
            # Look for session in self if it's a method
            if args and hasattr(args[0], '__dict__'):
                for attr_name in ['session', 'db_session', '_session']:
                    if hasattr(args[0], attr_name):
                        session = getattr(args[0], attr_name)
                        break

        try:
            result = func(*args, **kwargs)
            if session:
                session.commit()
            return result
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"Error in {func.__name__}: {str(e)}")
            raise

    return wrapper


def audit_trail(func: Callable) -> Callable:
    """Decorator to log function calls for audit purposes"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        func_name = func.__name__

        # Log function call
        logger.info(f"Executing {func_name} with args: {len(args)} kwargs: {list(kwargs.keys())}")

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"Successfully executed {func_name} in {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Failed to execute {func_name} after {duration:.3f}s: {str(e)}")
            raise

    return wrapper


def validation_required(func: Callable) -> Callable:
    """Decorator to ensure proper validation before function execution"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Basic validation - can be extended
        if args and hasattr(args[0], 'validate'):
            args[0].validate()

        return func(*args, **kwargs)

    return wrapper


def retry_on_failure(max_retries: int = 3, delay: float = 1.0,
                     exceptions: tuple = (Exception,)):
    """Decorator to retry function on specific exceptions"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. Retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")

            raise last_exception

        return wrapper

    return decorator


def performance_monitor(func: Callable) -> Callable:
    """Decorator to monitor function performance"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            start_memory = process.memory_info().rss / 1024 / 1024  # MB

            result = func(*args, **kwargs)

            end_time = time.time()
            duration = end_time - start_time

            memory_info = ""
            if start_memory:
                end_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_delta = end_memory - start_memory
                memory_info = f", Memory: {memory_delta:+.2f}MB"

            logger.info(f"Performance - {func.__name__}: {duration:.3f}s{memory_info}")
            return result

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Performance - {func.__name__} failed after {duration:.3f}s: {str(e)}")
            raise

    return wrapper
