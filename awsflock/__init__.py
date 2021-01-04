"""
Based upon a reading of the source and write-up from AWS for their java client:
  https://aws.amazon.com/blogs/database/building-distributed-locks-with-the-dynamodb-lock-client/

This client code is intentionally simpler and is not focused on in-application
use cases or usage with very high numbers of locks.
The same basic protocol set forth by AWS is used, however, so that those
use-cases could be supported in a future version.
"""

from .main import main as cli

__all__ = ("cli",)
