import logging
from functools import wraps
from inspect import signature
from typing import Callable, ParamSpec, TypeVar

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

P = ParamSpec("P")
R = TypeVar("R")
logger = logging.getLogger(__name__)


def handle_database_errors(
    operation: str,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorate(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            db = signature(func).bind(*args, **kwargs).arguments["db"]
            try:
                return func(*args, **kwargs)
            except IntegrityError as exc:
                _rollback(db)
                logger.exception("Database integrity error during %s", operation)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"{operation}: dữ liệu không thỏa mãn ràng buộc.",
                ) from exc
            except SQLAlchemyError as exc:
                _rollback(db)
                logger.exception("Database error during %s", operation)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"{operation}: không thể hoàn tất thao tác với cơ sở dữ liệu.",
                ) from exc

        return wrapped

    return decorate


def _rollback(db) -> None:
    try:
        db.rollback()
    except SQLAlchemyError:
        logger.exception("Database rollback failed")
