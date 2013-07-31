// Copyright (©) 2013 Gustavo Noronha Silva <gustavo@noronha.eti.br>
//
//  This program is free software: you can redistribute it and/or modify
//  it under the terms of the GNU Affero General Public License as
//  published by the Free Software Foundation, either version 3 of the
//  License, or (at your option) any later version.
//
//  This program is distributed in the hope that it will be useful,
//  but WITHOUT ANY WARRANTY; without even the implied warranty of
//  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//  GNU Affero General Public License for more details.
//
//  You should have received a copy of the GNU Affero General Public License
//  along with this program.  If not, see <http://www.gnu.org/licenses/>.

function set_sort(th, ascending) {
    var new_uri;
    if (window.location.search == "") {
        new_uri = window.location.pathname + '?order_by=' + th.id;
        if (ascending)
            new_uri = new_uri + '&asc=1';
    } else {
        var query_string = $.deserialize(window.location.search.substr(1));
        if (!ascending)
            delete query_string.asc;
        else
            query_string.asc = 1;
        query_string.order_by = th.id;
        query_string = $.param(query_string);
        new_uri = window.location.pathname + '?' + query_string;
    }
    window.location = new_uri;
}

$('th').addClass('sortable');
$('th').click(function(e) {
    var th = e.currentTarget;
    if ($(th).hasClass("sorted"))
        set_sort(th, true);
    else
        set_sort(th, false);
});
