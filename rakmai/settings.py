from django.conf import settings

# The content-type header uploaded with the file (e.g. text/plain or application/pdf)
UPLOAD_FILE_CONTENT_TYPES = getattr(settings, 'UPLOAD_FILE_CONTENT_TYPES', ['image', 'video'])

# The allowed file extensions
UPLOAD_FILE_EXTENSIONS = getattr(settings, 'UPLOAD_FILE_EXTENSIONS', ['jpg', 'jpeg', 'gif', 'png'])

# The size, in bytes, of the uploaded file (default: 2MB)
UPLOAD_FILE_MAX_SIZE = getattr(settings, 'UPLOAD_FILE_MAX_SIZE', 2097152)
