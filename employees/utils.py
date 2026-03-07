import logging

logger = logging.getLogger(__name__)


def send_push_notification(employee, title, body, data=None):
    """
    Send push notification to an employee via FCM.
    Requires firebase-admin to be configured.
    Falls back gracefully if Firebase is not set up.
    """
    try:
        import firebase_admin
        from firebase_admin import messaging
    except ImportError:
        logger.warning('firebase-admin not installed. Push notifications disabled.')
        return False

    tokens = list(
        employee.device_tokens.filter(is_active=True).values_list('token', flat=True)
    )

    if not tokens:
        return False

    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        data=data or {},
        tokens=tokens,
    )

    try:
        response = messaging.send_each_for_multicast(message)
        # Deactivate failed tokens
        for i, send_response in enumerate(response.responses):
            if not send_response.success:
                from .models import DeviceToken
                DeviceToken.objects.filter(token=tokens[i]).update(is_active=False)
        return True
    except Exception as e:
        logger.error(f'FCM send failed: {e}')
        return False


def init_firebase():
    """Initialize Firebase Admin SDK. Call once at startup."""
    try:
        import firebase_admin
        from firebase_admin import credentials
        import os

        cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
        if cred_path and not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            logger.info('Firebase Admin SDK initialized')
    except Exception as e:
        logger.warning(f'Firebase init failed: {e}')
