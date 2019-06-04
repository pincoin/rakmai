$(document).ready(function () {
    $('.simplemde-widget').each(function (index) {
        // Select simplemde container (#id-content)
        var $sm = $('#' + $(this).attr('id'));

        // Select file input (#id-content-file)
        var $file_input = $('#' + $(this).attr('id') + '-file');

        // Check if input data was changed
        var dirty = false;
        var submitted = false;

        var simplemde = new SimpleMDE({
            element: $sm[0],
            spellChecker: false,
            autofocus: false,
            indentWithTabs: false,
            lineWrapping: true,
            promptURLs: true,
            toolbar: [
                "bold", "italic", "heading", "|",
                "code", "unordered-list", "ordered-list", "table", "quote", "|",
                "link",
                {
                    name: "upload",
                    action: function imageUploadFunction(editor) {
                        $file_input.click();
                    },
                    className: "far fa-image",
                    title: "Upload Images"
                },
                {
                    name: "youtube",
                    action: function youtubeFunction(editor) {
                        var cm = editor.codemirror;
                        var output = '';
                        var text = cm.getSelection();
                        output = '[![Youtube_Label](http://img.youtube.com/vi/Youtube_ID/0.jpg)](Youtube_Link)';
                        cm.replaceSelection(output);
                    },
                    className: "fab fa-youtube",
                    title: "Youtube"
                },
                "|",
                "preview", "side-by-side", "fullscreen", "|",
                "guide"
            ]
        });

        $file_input.on('change', function (e) {
            var uploaded_files = this.files;

            var formData = new FormData();

            $.ajax({
                url: options.upload_url,    // Point to django upload handler view
                type: 'post',
                processData: false,         // file-transfer
                contentType: false,         // file-transfer
                data: formData,
                beforeSend: function (xhr, settings) {
                    // Set CSRF token by calling default `beforeSend`.
                    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", csrftoken);
                    }

                    // Get the number of thumbnails.
                    var file_count = $('#thumbnail-list > div').length;

                    // Construct form data with each file.
                    $.each(uploaded_files, function (index, file) {
                        formData.append('files', file);

                        // Check if maximum file size exceeds.
                        if (file.size > options.max_upload_size) {
                            console.error('Maximum file size exceeded.');
                            xhr.abort();
                        }

                        // Limit maximum number of files.
                        if (++file_count > options.max_file_count) {
                            console.error('Maximum number of files exceeded.');
                            xhr.abort();
                        }
                    });
                }
            }).done(function (data, textStatus, jqXHR) {
                $.each(data.files, function (index, file) {
                    // Insert image into the editor
                    var selected = simplemde.codemirror.getSelection();
                    simplemde.codemirror.replaceSelection('![Image_Alt_Label](' + file.url + ')');

                    //
                    // YOU MUST IMPLEMENT YOUR OWN CODE HERE:
                    //
                    // Append thumbnail images at the bottom.
                    $('#thumbnail-list').append(
                        '<div id="thumbnail-card-' + file.uid + '" class="col-lg-3 col-md-3 col-sm-4 mt-2">\n' +
                        '  <div class="card h-100">\n' +
                        '    <div class="card-body">\n' +
                        '      <img class="card-img-top page-thumbnail-image" src="' + file.url + '">\n' +
                        '    </div>\n' +
                        '    <div class="card-footer text-center">\n' +
                        '      <a href="#" id="thumbnail-' + file.uid + '"\n' +
                        '           class="btn-sm btn-danger page-thumbnail-delete-button">Delete</a>\n' +
                        '    </div>\n' +
                        '  </div>\n' +
                        '</div>');

                    // Add hidden fields in order to make a relationship.
                    $('<input>', {
                        type: 'hidden',
                        name: 'attachments',
                        value: file.uid
                    }).appendTo('form');
                });
            }).fail(function (jqXHR, textStatus, errorThrown) {
                console.error('Failed to upload');
            });
        });

        $(document).on('click', '.page-thumbnail-image', function () {
            // Insert image into the editor when clicked thumbnail images
            var selected = simplemde.codemirror.getSelection();
            simplemde.codemirror.replaceSelection('![Image_Alt_Label](' + $(this).attr('src') + ')');
        });

        $(document).on('click', '.page-thumbnail-delete-button', function () {
            var uid = $(this).attr('id').split('thumbnail-')[1];

            $.ajax({
                url: options.delete_url,
                type: 'post',
                data: {uid: uid},
                beforeSend: function (xhr, settings) {
                    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", csrftoken);
                    }
                }
            }).done(function (data, textStatus, jqXHR) {
                $.each(data.files, function (index, file) {
                    // Remove thumbnail image itself.
                    $('#thumbnail-card-' + file.uid).remove();

                    // Remove hidden field (It's saved if not removed).
                    $('input:hidden[name=attachments][value=' + file.uid + ']').remove();
                });
            }).fail(function (jqXHR, textStatus, errorThrown) {
                console.error('Failed to delete');
            });
        });

        $('form :input').change(function () {
            dirty = true;
        });

        $('form').on('submit', function () {
            submitted = true;
        });

        $(window).on('beforeunload', function () {
            if (dirty && !submitted) {
                return 'You have unsaved changes, are you sure you want to discard them?';
            }
        });
    });
});