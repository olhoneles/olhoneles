function view(url) {
    $.getJSON('/' + url, function(response) {
        var columns = response.columns
        var data = response.data;

        var table = document.createElement('table');

        var tr = document.createElement('tr');
        table.appendChild(tr);

        var th = document.createElement('th');
        th.innerHTML = columns[0];
        tr.appendChild(th);

        th = document.createElement('th');
        th.innerHTML = columns[1];
        tr.appendChild(th);

        // The last row is the total.
        var total = data[data.length - 1][1];

        var graph_xticks = [];
        var graph_data = [];
        var graph_counter = 0;
        var other = 0;
        for (var i = 0; i < data.length; i++) {
            tr = document.createElement('tr');
            table.appendChild(tr);

            if ((i + 1) == data.length) {
                tr.setAttribute('class', 'final');
            } else if (i % 2 != 0) {
                tr.setAttribute('class', 'odd');
            }

            if ((i + 1) != data.length) {
                if ((data[i][1] / total) > 0.05) {
                    graph_xticks[graph_counter] = {v: graph_counter, label: data[i][0]};
                    graph_data[graph_counter] = [graph_counter, data[i][1]];
                    graph_counter++;
                } else { // Track too small to show slices.
                    other += data[i][1];
                }
            }

            td = document.createElement('td');
            td.innerHTML = data[i][0];
            tr.appendChild(td);

            td = document.createElement('td');
            td.setAttribute('class', 'right');
            td.innerHTML = jQuery().number_format(data[i][1], { symbol: 'R$' });
            tr.appendChild(td);
        }

        // The "Other" slice of the pie.
        graph_xticks[graph_counter] = {v: graph_counter, label: 'Outros'};
        graph_data[graph_counter] = [graph_counter, other];

        var results_pane = document.getElementById('results');
        if (results_pane.firstChild != null) {
            results_pane.replaceChild(results_pane.firstChild, table);
        } else {
            results_pane.appendChild(table);
        }

        // Graph.
        var options = {
            'xTicks': graph_xticks,
            'drawBackground': false,
            'axisLabelWidth': '90',
            'axisLabelFontSize': 12,
        };

        var layout = new Layout('pie', options);
        layout.addDataset('expenses', graph_data);
        layout.evaluate();

        var canvas = document.getElementById('graph');
        var plotter = new PlotKit.SweetCanvasRenderer(canvas, layout, options);
        plotter.render();
    });
}
