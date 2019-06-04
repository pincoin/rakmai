(function (d, s) {
    var j, e = d.getElementsByTagName(s)[0];

    if (typeof LivereTower === 'function') {
        return;
    }

    j = d.createElement(s);
    j.src = 'https://cdn-city.livere.com/js/embed.dist.js';
    j.async = true;

    e.parentNode.insertBefore(j, e);
})(document, 'script');

/*
<script src="{% static "js/rakmai/livere.js" %}"></script>

<div id="lv-container" data-id="city" data-uid="MTAyMC80MTU3Mi8xODExOQ==">
<noscript> 라이브리 댓글 작성을 위해 JavaScript를 활성화 해주세요</noscript>
</div>
 */
