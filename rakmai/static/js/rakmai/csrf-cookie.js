// Set a custom X-CSRFToken header to the value of the CSRF token
// https://docs.djangoproject.com/en/2.0/ref/csrf/#acquiring-the-token-if-csrf-use-sessions-is-false
function getCSRFCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Acquiring the token from cookie when CSRF_USE_SESSIONS is False
var csrftoken = getCSRFCookie('csrftoken');

// Acquiring the token when CSRF_USE_SESSIONS is True
// var csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();

// Check if HTTP methods do not require CSRF protection
// https://docs.djangoproject.com/en/2.0/ref/csrf/#setting-the-token-on-the-ajax-request
function csrfSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
