import base64


WEBHOOK_MESSAGING_PAYLOAD = {
    "object": "instagram",
    "entry": [
        {
            "id": "0",
            "time": 1762076519,
            "messaging": [
                {
                    "sender": {"id": "123456789"},
                    "recipient": {"id": "987654321"},
                    "timestamp": 1762076518,
                    "message": {
                        "mid": "mid.1234567890",
                        "text": "Hello, this is a test message!"
                    }
                }
            ]
        }
    ]
}


WEBHOOK_CHANGES_PAYLOAD = {
    "object": "instagram",
    "entry": [
        {
            "id": "0",
            "time": 1762076519,
            "changes": [
                {
                    "field": "comments",
                    "value": {
                        "from": {
                            "id": "232323232",
                            "username": "test_user"
                        },
                        "media": {
                            "id": "17912345678901234"
                        },
                        "comment_id": "17812345678901234",
                        "text": "This is an example comment."
                    }
                }
            ]
        }
    ]
}


WEBHOOK_VERIFICATION_REQUEST = {
    "hub.mode": "subscribe",
    "hub.challenge": "460578810",
    "hub.verify_token": "change_me_instagram_webhook_verification_token"
}


SAMPLE_BASE64_IMAGE = base64.b64encode(
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
).decode('utf-8')


SAMPLE_POST_DATA = {
    "instagram_creation_id": "test_creation_id_123",
    "caption": "Test post caption",
    "image_url": "http://localhost:9000/images/test_image.jpg"
}


SAMPLE_CONTEXT_CONTENT = "This is a sample context for testing purposes. It contains enough content to validate the system."

