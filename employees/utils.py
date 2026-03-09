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


def compare_faces(reference_image_path, check_in_image):
    """
    Compare a check-in selfie against the employee's stored reference photo.
    Returns (is_match, confidence) tuple.
    - reference_image_path: path to the stored reference face photo
    - check_in_image: InMemoryUploadedFile or path to the check-in selfie
    """
    try:
        import face_recognition
        import numpy as np
        import tempfile
        import os

        # Load reference image
        ref_image = face_recognition.load_image_file(reference_image_path)
        ref_locations = face_recognition.face_locations(ref_image, model='hog')
        if not ref_locations:
            ref_locations = face_recognition.face_locations(ref_image, number_of_times_to_upsample=2, model='hog')
        ref_encodings = face_recognition.face_encodings(ref_image, known_face_locations=ref_locations) if ref_locations else []
        if not ref_encodings:
            logger.warning('No face found in reference photo')
            return False, 0.0, 'No face found in your registered photo. Please re-register your face.'

        ref_encoding = ref_encodings[0]

        # Load check-in image (handle uploaded file)
        if hasattr(check_in_image, 'read'):
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                for chunk in check_in_image.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name
            try:
                checkin_image = face_recognition.load_image_file(tmp_path)
            finally:
                os.unlink(tmp_path)
            # Reset file pointer so Django can still save it
            check_in_image.seek(0)
        else:
            checkin_image = face_recognition.load_image_file(check_in_image)

        checkin_locations = face_recognition.face_locations(checkin_image, model='hog')
        if not checkin_locations:
            checkin_locations = face_recognition.face_locations(checkin_image, number_of_times_to_upsample=2, model='hog')
        checkin_encodings = face_recognition.face_encodings(checkin_image, known_face_locations=checkin_locations) if checkin_locations else []
        if not checkin_encodings:
            return False, 0.0, 'No face detected in your selfie. Please try again.'

        checkin_encoding = checkin_encodings[0]

        # Compare faces - face_distance returns euclidean distance (lower = more similar)
        face_distance = face_recognition.face_distance([ref_encoding], checkin_encoding)[0]

        # Convert distance to confidence (0-1 scale, higher = better match)
        confidence = max(0.0, 1.0 - face_distance)

        is_match = confidence >= 0.55  # ~0.45 distance threshold (stricter than default 0.6)

        return is_match, round(confidence, 4), None

    except ImportError:
        logger.error('face_recognition package not installed')
        return False, 0.0, 'Face recognition not available on server.'
    except Exception as e:
        logger.error(f'Face comparison failed: {e}')
        return False, 0.0, f'Face verification error: {str(e)}'


def generate_face_encoding(image_path):
    """Generate face encoding from an image file. Returns list or None."""
    try:
        import face_recognition
    except ImportError:
        logger.error('face_recognition not installed. Install with: pip install face-recognition')
        return None

    try:
        from PIL import Image
        import numpy as np

        # Open and normalize the image
        pil_image = Image.open(image_path)
        logger.info(f'Original image: {image_path}, size: {pil_image.size}, mode: {pil_image.mode}')

        # Convert to RGB (face_recognition only works with RGB)
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')

        # Resize large images
        max_dimension = 1200
        if max(pil_image.size) > max_dimension:
            pil_image.thumbnail((max_dimension, max_dimension))

        # Save as JPEG to ensure clean format
        clean_path = image_path.rsplit('.', 1)[0] + '_clean.jpg'
        pil_image.save(clean_path, 'JPEG', quality=95)

        # Load with face_recognition (uses numpy array)
        image = face_recognition.load_image_file(clean_path)
        logger.info(f'Image loaded, shape: {image.shape}, dtype: {image.dtype}')

        # Try HOG detector
        face_locations = face_recognition.face_locations(image, model='hog')
        logger.info(f'HOG detection: {len(face_locations)} faces')

        if not face_locations:
            # Upsample for small/distant faces
            face_locations = face_recognition.face_locations(image, number_of_times_to_upsample=2, model='hog')
            logger.info(f'HOG upsampled: {len(face_locations)} faces')

        if not face_locations:
            # Last resort: try CNN model (more accurate but slower)
            try:
                face_locations = face_recognition.face_locations(image, model='cnn')
                logger.info(f'CNN detection: {len(face_locations)} faces')
            except Exception as cnn_err:
                logger.warning(f'CNN detection failed (expected on CPU): {cnn_err}')

        # Clean up temp file
        import os
        try:
            os.unlink(clean_path)
        except OSError:
            pass

        if not face_locations:
            logger.warning(f'No face detected in image after all attempts: {image_path}')
            return None

        encodings = face_recognition.face_encodings(image, known_face_locations=face_locations)
        if encodings:
            logger.info(f'Face encoding generated successfully, {len(face_locations)} face(s)')
            return encodings[0].tolist()
        return None
    except Exception as e:
        logger.error(f'Face encoding generation failed: {e}', exc_info=True)
        return None


def init_firebase():
    """Initialize Firebase Admin SDK. Call once at startup."""
    try:
        import firebase_admin
        from firebase_admin import credentials
        import os
        import json

        if firebase_admin._apps:
            return

        # Option 1: JSON string in env var (recommended for Railway)
        cred_json = os.getenv('FIREBASE_CREDENTIALS_JSON')
        if cred_json:
            cred = credentials.Certificate(json.loads(cred_json))
            firebase_admin.initialize_app(cred)
            logger.info('Firebase Admin SDK initialized from JSON env var')
            return

        # Option 2: File path
        cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
        if cred_path:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            logger.info('Firebase Admin SDK initialized from file')
    except Exception as e:
        logger.warning(f'Firebase init failed: {e}')
