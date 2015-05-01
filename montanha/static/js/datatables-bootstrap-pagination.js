/* Default class modification */
$.extend( $.fn.dataTableExt.oStdClasses, {
    'sWrapper': 'dataTables_wrapper form-inline',
    'sFilterInput': 'form-control input-sm',
    'sLengthSelect': 'form-control input-sm',
    'sPageEllipsis': 'paginate_ellipsis',
    'sPageNumber': 'paginate_number',
    'sPageNumbers': 'paginate_numbers'
});

/* API method to get paging information */
$.fn.dataTableExt.oApi.fnPagingInfo = function(oSettings)
{
  return {
    'iStart':         oSettings._iDisplayStart,
    'iEnd':           oSettings.fnDisplayEnd(),
    'iLength':        oSettings._iDisplayLength,
    'iTotal':         oSettings.fnRecordsTotal(),
    'iFilteredTotal': oSettings.fnRecordsDisplay(),
    'iPage':          oSettings._iDisplayLength === -1 ?
      0 : Math.ceil( oSettings._iDisplayStart / oSettings._iDisplayLength ),
    'iTotalPages':    oSettings._iDisplayLength === -1 ?
      0 : Math.ceil( oSettings.fnRecordsDisplay() / oSettings._iDisplayLength )
  };
};

$.fn.dataTableExt.oPagination.bootstrap_ellipses = {
    'oDefaults': {
        'iShowPages': 3
    },
    'fnClickHandler': function(e) {
        var fnCallbackDraw = e.data.fnCallbackDraw,
            oSettings = e.data.oSettings,
            sPage = e.data.sPage;

        if ($(this).is('[disabled]')) {
            return false;
        }

        e.preventDefault();
        oSettings.oApi._fnPageChange(oSettings, sPage);
        fnCallbackDraw(oSettings);

        return true;
    },
    // fnInit is called once for each instance of pager
    'fnInit': function(oSettings, nPager, fnCallbackDraw) {
        var oClasses = oSettings.oClasses,
            oLang = oSettings.oLanguage.oPaginate,
            that = this;

        var iShowPages = oSettings.oInit.iShowPages || this.oDefaults.iShowPages,
            iShowPagesHalf = Math.floor(iShowPages / 2);

        $.extend(oSettings, {
            _iShowPages: iShowPages,
            _iShowPagesHalf: iShowPagesHalf,
        });

        $(nPager).addClass('pagination').append(
                '<ul>'+
                    '<li class="prev disabled"><a href="#">&larr;</a></li>'+
                    '<li class="next disabled"><a href="#">&rarr; </a></li>'+
                '</ul>'
        );
        var els = $('a', nPager);
        $(els[0]).click({ 'fnCallbackDraw': fnCallbackDraw, 'oSettings': oSettings, 'sPage': 'previous' }, that.fnClickHandler);
        $(els[1]).click({ 'fnCallbackDraw': fnCallbackDraw, 'oSettings': oSettings, 'sPage': 'next' }, that.fnClickHandler);
    },
    // fnUpdate is only called once while table is rendered
    'fnUpdate': function(oSettings, fnCallbackDraw) {
        var oClasses = oSettings.oClasses,
            that = this;

        var tableWrapper = oSettings.nTableWrapper;

        // Update stateful properties
        this.fnUpdateState(oSettings);

        // Add / remove disabled classes from the static elements
        if (oSettings._iCurrentPage === 1) {
            $('li:first', tableWrapper).addClass('disabled');
        } else {
            $('li:first', tableWrapper).removeClass('disabled');
        }

        if (oSettings._iTotalPages === 0 || oSettings._iCurrentPage === oSettings._iTotalPages) {
            $('li:last', tableWrapper).addClass('disabled');
        } else {
            $('li:last', tableWrapper).removeClass('disabled');
        }

        var i, oNumber, oNumbers = $('.' + oClasses.sPageNumbers, tableWrapper);

        // Remove the middle elements
        $('li:gt(0)', tableWrapper).filter(':not(:last)').remove();

        for (i = oSettings._iFirstPage; i <= oSettings._iLastPage; i++) {
            oNumber = $('<li><a href="#" class="' + oClasses.sPageButton + ' ' + oClasses.sPageNumber + '">' + oSettings.fnFormatNumber(i) + '</a></li>');

            if (oSettings._iCurrentPage === i) {
                oNumber.attr('class', 'active');
            } else {
                oNumber.click({ 'fnCallbackDraw': fnCallbackDraw, 'oSettings': oSettings, 'sPage': i - 1 }, that.fnClickHandler);
            }

            // Draw
            oNumber.insertBefore($('li:last', tableWrapper));
        }

        // Add ellipses
        if (1 < oSettings._iFirstPage) {
            elipsis = $('<li><a class="' + oClasses.sPageButton + '">…</a></li>');
            elipsis.insertAfter($('li:first', tableWrapper));

            oNumber = $('<li><a href="#" class="' + oClasses.sPageButton + ' ' + oClasses.sPageNumber + '">' + oSettings.fnFormatNumber(1) + '</a></li>');
            oNumber.click({ 'fnCallbackDraw': fnCallbackDraw, 'oSettings': oSettings, 'sPage': 0 }, that.fnClickHandler);
            oNumber.insertAfter($('li:first', tableWrapper));
        }

        if (oSettings._iLastPage < oSettings._iTotalPages) {
            elipsis = $('<li><a class="' + oClasses.sPageButton + '">…</a></li>');
            elipsis.insertBefore($('li:last', tableWrapper));

            oNumber = $('<li><a href="#" class="' + oClasses.sPageButton + ' ' + oClasses.sPageNumber + '">' + oSettings.fnFormatNumber(oSettings._iTotalPages) + '</a></li>');
            oNumber.click({ 'fnCallbackDraw': fnCallbackDraw, 'oSettings': oSettings, 'sPage': oSettings._iTotalPages - 1 }, that.fnClickHandler);
            oNumber.insertBefore($('li:last', tableWrapper));
        }
    },
    // fnUpdateState used to be part of fnUpdate
    // The reason for moving is so we can access current state info before fnUpdate is called
    'fnUpdateState': function(oSettings) {
        var iCurrentPage = Math.ceil((oSettings._iDisplayStart + 1) / oSettings._iDisplayLength),
            iTotalPages = Math.ceil(oSettings.fnRecordsDisplay() / oSettings._iDisplayLength),
            iFirstPage = iCurrentPage - oSettings._iShowPagesHalf,
            iLastPage = iCurrentPage + oSettings._iShowPagesHalf;

        if (iTotalPages < oSettings._iShowPages) {
            iFirstPage = 1;
            iLastPage = iTotalPages;
        } else if (iFirstPage < 1) {
            iFirstPage = 1;
            iLastPage = oSettings._iShowPages;
        } else if (iLastPage > iTotalPages) {
            iFirstPage = (iTotalPages - oSettings._iShowPages) + 1;
            iLastPage = iTotalPages;
        }

        $.extend(oSettings, {
            _iCurrentPage: iCurrentPage,
            _iTotalPages: iTotalPages,
            _iFirstPage: iFirstPage,
            _iLastPage: iLastPage
        });
    }
};
