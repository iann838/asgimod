from concurrent.futures.thread import ThreadPoolExecutor
from re import escape
from typing import Callable, Optional, TypeVar, Awaitable

try:
    from typing import ParamSpec
    SUPPORT_PARAM_SPEC = True
    P = ParamSpec("P")
except ImportError:
    SUPPORT_PARAM_SPEC = False

from asgiref.sync import sync_to_async as untyped_sync_to_async, async_to_sync as untyped_async_to_sync


R = TypeVar("R")


# NOTE: BEFORE PYTHON 3.10, THERE IS NO WAY TO FORWARD
#       CALLABLE PARAMS SPECIFICATIONS IN DECORATORS.
#       SUPPORT FOR TYPED PARAM SPECIFICATION WILL BE
#       ADDED IN LATER VERSION, OR MAY BE COMPATIBLE
#       IN BOTH PRE 3.10 AND PRO 3.10 VERSIONS. 

if SUPPORT_PARAM_SPEC:

    def sync_to_async(func: Callable[P, R], thread_sensitive: bool = True, executor: Optional[ThreadPoolExecutor] = None) -> Callable[P, Awaitable[R]]:
        return untyped_sync_to_async(func, thread_sensitive=thread_sensitive, executor=executor)


    def async_to_sync(func: Callable[P, Awaitable[R]], force_new_loop=False) -> Callable[P, R]:
        return untyped_async_to_sync(func, force_new_loop=force_new_loop)

else:

    def sync_to_async(func: Callable[..., R], thread_sensitive: bool = True, executor: Optional[ThreadPoolExecutor] = None) -> Callable[..., Awaitable[R]]:
        return untyped_sync_to_async(func, thread_sensitive=thread_sensitive, executor=executor)


    def async_to_sync(func: Callable[..., Awaitable[R]], force_new_loop=False) -> Callable[..., R]:
        return untyped_async_to_sync(func, force_new_loop=force_new_loop)
