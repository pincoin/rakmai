$(document).ready(function () {
    function intcomma(number) {
        return number.toString().replace(/(\d)(?=(\d\d\d)+(?!\d))/g, "$1,");
    }

    function update_cart(data) {
        var total = 0;

        $.each(data, function (key, item) {
            $('#id-quantity-' + key).val(item.quantity);

            var subtotal = item.quantity * item.price;
            total += subtotal;
            $('#id-subtotal-' + key).text('₩ ' + intcomma(subtotal));
        });

        $('#id-total').text('₩ ' + intcomma(total));
    }

    function empty_cart() {
        $('#id-cart-list').html('<li class="list-group-item">장바구니가 비었습니다.</li>');
        $('#id-total').text('₩ 0');
    }

    function delete_cart_item(data) {
        var rows = $('input[id^="id-quantity-"]');
        rows.each(function () {
            var product_id = $(this).data('item');

            if (!(product_id in data)) {
                $(this).closest('li').remove();

                if (rows.length === 1) {
                    empty_cart();
                }
            }
        });
    }

    $(document).on('click', '.add-one-to-cart-button', function (e) {
        var pk = $(this).data('item');
        $.ajax({
            url: '/shop/default/cart/add/',
            type: 'post',
            dataType: 'json',
            data: {
                'product_pk': pk,
                'quantity': 1
            },
            beforeSend: function (xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            }
        }).done(function (data, textStatus, jqXHR) {
            $('#cart_alert_product').text(data[pk].name + ' x 1');
            $('.cart-alert').show();

            $('#cart-badge').text(Object.keys(data).length);

            setTimeout(function () {
                $('.cart-alert').hide();
            }, 1000);
        }).fail(function (jqXHR, textStatus, errorThrown) {
            console.error('Failed to add item to cart');
        });
    });

    $(document).on('click', '.add-to-cart-button', function (e) {
        $.ajax({
            url: '/shop/default/cart/add/',
            type: 'post',
            dataType: 'json',
            data: {
                'product_pk': $(this).data('item'),
                'quantity': 1
            },
            beforeSend: function (xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            }
        }).done(function (data, textStatus, jqXHR) {
            update_cart(data);

            $('#cart-badge').text(Object.keys(data).length);
        }).fail(function (jqXHR, textStatus, errorThrown) {
            console.error('Failed to add item to cart');
        });
    });

    $(document).on('click', '.remove-from-cart-button', function (e) {
        $.ajax({
            url: '/shop/default/cart/remove/',
            type: 'post',
            dataType: 'json',
            data: {
                'product_pk': $(this).data('item'),
                'quantity': 1
            },
            beforeSend: function (xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            }
        }).done(function (data, textStatus, jqXHR) {
            update_cart(data);
            delete_cart_item(data);
            $('#cart-badge').text(Object.keys(data).length);
        }).fail(function (jqXHR, textStatus, errorThrown) {
            console.error('Failed to delete item from cart');
        });
    });

    $(document).on('click', '.delete-from-cart-button', function (e) {
        $.ajax({
            url: '/shop/default/cart/delete/',
            type: 'post',
            dataType: 'json',
            data: {
                'product_pk': $(this).data('item')
            },
            beforeSend: function (xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            }
        }).done(function (data, textStatus, jqXHR) {
            update_cart(data);
            delete_cart_item(data);
            $('#cart-badge').text(Object.keys(data).length);
        }).fail(function (jqXHR, textStatus, errorThrown) {
            console.error('Failed to delete item from cart');
        });
    });

    $(document).on('focusout', '.input-item-quantity', function (e) {
        var input = $(this);
        var num = input.val();

        // `quantity` must be greater than ONE.
        var quantity = Math.floor(Number(num));
        if (quantity !== Infinity && String(quantity) === num && quantity > 0) {
            $.ajax({
                url: '/shop/default/cart/set-quantity/',
                type: 'post',
                dataType: 'json',
                data: {
                    'product_pk': input.data('item'),
                    'quantity': quantity
                },
                beforeSend: function (xhr, settings) {
                    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", csrftoken);
                    }
                }
            }).done(function (data, textStatus, jqXHR) {
                update_cart(data);
            }).fail(function (jqXHR, textStatus, errorThrown) {
                console.error('Failed to change cart item quantity');
            });
        } else {
            input.val(1);
        }
    });

    $(document).on('click', '.plus-cart-button', function (e) {
        var input = $('#id-quantity-detail');
        var num = input.val();

        // `quantity` must be greater than zero.
        var quantity = Math.floor(Number(num));
        if (quantity !== Infinity && String(quantity) === num && quantity > 0) {
            input.val(quantity + 1);
        } else {
            input.val(1);
        }
    });

    $(document).on('click', '.minus-cart-button', function (e) {
        var input = $('#id-quantity-detail');
        var num = input.val();

        // `quantity` must be greater than ONE.
        var quantity = Math.floor(Number(num));
        if (quantity !== Infinity && String(quantity) === num && quantity > 1) {
            input.val(quantity - 1);
        } else {
            input.val(1);
        }
    });

    $(document).on('click', '.detail-add-to-cart-button', function (e) {
        var input = $('#id-quantity-detail');
        var num = input.val();

        var pk = $(this).data('item');
        var quantity = Math.floor(Number(num)); // `quantity` must be greater than zero.
        if (quantity !== Infinity && String(quantity) === num && quantity > 0) {
            $.ajax({
                url: '/shop/default/cart/add/',
                type: 'post',
                dataType: 'json',
                data: {
                    'product_pk': pk,
                    'quantity': quantity
                },
                beforeSend: function (xhr, settings) {
                    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", csrftoken);
                    }
                }
            }).done(function (data, textStatus, jqXHR) {
                $('#cart_alert_product').text(data[pk].name + ' x ' + quantity);
                $('.cart-alert').show();
                $('#cart-badge').text(Object.keys(data).length);

                setTimeout(function () {
                    $('.cart-alert').hide();
                }, 1000);
            }).fail(function (jqXHR, textStatus, errorThrown) {
                console.error('Failed to add item to cart');
            });
        } else {
            input.val(1);
        }
    });

    $(document).on('click', '#cart-empty-button', function (e) {
        $.ajax({
            url: '/shop/default/cart/clear/',
            type: 'post',
            dataType: 'json',
            data: {},
            beforeSend: function (xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            }
        }).done(function (data, textStatus, jqXHR) {
            empty_cart();
            $('#cart-badge').text(0);
        }).fail(function (jqXHR, textStatus, errorThrown) {
            console.error('Failed to empty cart');
        });
    });

    $(document).on('click', '.close', function (e) {
        // data-dismiss completely removes the element.
        // Use jQuery's .hide() method instead.
        $('.cart-alert').hide();
    });
});