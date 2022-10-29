from typing import Optional, Any, Dict, Union

from fastapi import HTTPException
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST


def open_api_standard_responses(
    success_status_code: Optional[int] = HTTP_200_OK,
    success_response_model: Any = None,
    success_description: Optional[str] = None,
    success_content_type: Optional[str] = None,
    fail_status_code: Optional[int] = HTTP_400_BAD_REQUEST,
    fail_response_model: Optional[Any] = None,
    fail_description: Optional[str] = None,
    fail_content_type: Optional[str] = None,
) -> Dict[int, Union[dict, Dict[str, Optional[Any]]]]:

    status_code__details = dict()

    status_code__details[success_status_code] = dict()
    if success_response_model:
        status_code__details[success_status_code]['model'] = success_response_model
    if success_description:
        status_code__details[success_status_code]['description'] = success_description
    if success_content_type:
        status_code__details[success_status_code]['content'] = {
            success_content_type: {}
        }

    status_code__details[fail_status_code] = dict()
    if fail_response_model:
        status_code__details[fail_status_code]['model'] = fail_response_model
    if fail_description:
        status_code__details[fail_status_code]['description'] = fail_description
    if fail_content_type:
        status_code__details[fail_status_code]['content'] = {
            fail_content_type: {}
        }

    return status_code__details


def http_exception(
    status_code: Optional[int] = HTTP_400_BAD_REQUEST,
    error_code: str = '',
    description: Optional[str] = '',
) -> HTTPException:
    raise HTTPException(
        status_code=status_code,
        detail={
            'error_code': error_code,
            'description': description
        }
    )

