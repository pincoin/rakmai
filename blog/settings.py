from django.conf import settings

# Minimum count of most common tags
BLOG_MINIMUM_COUNT_OF_TAGS = getattr(settings, 'BLOG_MINIMUM_COUNT_OF_TAGS', 1)

# The maximum number of uploaded files
POST_MAX_FILE_COUNT = getattr(settings, 'POST_MAX_FILE_COUNT', 10)

# URL for file upload
BLOG_FILE_UPLOAD_URL = getattr(settings, 'BLOG_FILE_UPLOAD_URL', '/blog/upload-file')

# URL for file download
BLOG_FILE_DELETE_URL = getattr(settings, 'BLOG_FILE_DELETE_URL', '/blog/delete-file')
