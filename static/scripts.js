function view(url) {
    $.getJSON('/' + url, function(data) {
        var table = document.createElement('table');

        var tr = document.createElement('tr');
        table.appendChild(tr);

        var th = document.createElement('th');
        th.innerText = 'Tipo de gasto';
        tr.appendChild(th);

        th = document.createElement('th');
        th.innerText = 'Valor ressarcido';
        tr.appendChild(th);

        for (i = 0; i < data.length; i++) {
            tr = document.createElement('tr');
            table.appendChild(tr);

            if ((i + 1) == data.length) {
                tr.setAttribute('class', 'final');
            } else if (i % 2 != 0) {
                tr.setAttribute('class', 'odd');
            }

            td = document.createElement('td');
            td.innerText = data[i][0];
            tr.appendChild(td);

            td = document.createElement('td');
            td.setAttribute('class', 'right');
            td.innerText = data[i][1];
            tr.appendChild(td);
        }

        var results_pane = document.getElementById('results');
        if (results_pane.firstChild != null) {
            results_pane.replaceChild(results_pane.firstChild, table);
        } else {
            results_pane.appendChild(table);
        }
    });
}
