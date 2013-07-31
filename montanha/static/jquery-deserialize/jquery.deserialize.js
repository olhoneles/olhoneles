(function ($) {
    $.deserialize = function (str, options) {
        var pairs = str.split(/&amp;|&/i),
            h = {},
            options = options || {};
        for(var i = 0; i < pairs.length; i++) {
            var kv = pairs[i].split('=');
            kv[0] = decodeURIComponent(kv[0]);
            if(!options.except || options.except.indexOf(kv[0]) == -1) {
                if((/^\w+\[\w+\]$/).test(kv[0])) {
                    var matches = kv[0].match(/^(\w+)\[(\w+)\]$/);
                    if(typeof h[matches[1]] === 'undefined') {
                        h[matches[1]] = {};
                    }
                    h[matches[1]][matches[2]] = decodeURIComponent(kv[1]);
                } else {
                    h[kv[0]] = decodeURIComponent(kv[1]);
                }
            }
        }
        return h;
    };

    $.fn.deserialize = function (options) {
        return $.deserialize($(this).serialize(), options);
    };
})(jQuery);

