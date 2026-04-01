import asyncio
import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from helpers.dotenv import get_dotenv_value, load_dotenv


@pytest.mark.skip(
    reason="Manual integration test requiring a live email account and a supported email helper implementation."
)
@pytest.mark.asyncio
async def test_manual_email_parser():
    from helpers.email_client import read_messages

    load_dotenv()
    messages = await read_messages(
        account_type=get_dotenv_value("TEST_SERVER_TYPE", "imap"),
        server=get_dotenv_value("TEST_EMAIL_SERVER"),
        port=int(get_dotenv_value("TEST_EMAIL_PORT", 993)),
        username=get_dotenv_value("TEST_EMAIL_USERNAME"),
        password=get_dotenv_value("TEST_EMAIL_PASSWORD"),
    )
    print(messages)


if __name__ == "__main__":
    asyncio.run(test_manual_email_parser())
