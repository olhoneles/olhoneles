function view(url) {
    $.getJSON('/' + url, function(response) {
        var columns = response.columns
        var data = response.data;
        var show_graph = response.show_graph;
        var graph_column = response.graph_column;

        var canvas = document.getElementById('graph');

        // First of all, cleanup the graph.
        context = canvas.getContext('2d');
        context.clearRect(0, 0, canvas.width, canvas.height);

        // Remove the labels too.
        var graphparent = document.getElementById('graphparent');
        var divs = $(graphparent).find('div');
        for (var i = 0; i < divs.length; i++) {
            graphparent.removeChild(divs[i]);
        }

        // Now let's start building the new data display.
        var table = document.createElement('table');

        var tr = document.createElement('tr');
        table.appendChild(tr);

        // First of all, the titles.
        for (var i = 0; i < columns.length; i++) {
            var col_label = columns[i]['label'];

            var th = document.createElement('th');
            th.innerHTML = col_label;
            tr.appendChild(th);
        }

        // If we display a graph, we need to collect some information
        // to help us, and build the list of numbers to plot.
        if (show_graph) {
            // The last row is the total.
            var total = data[data.length - 1][graph_column];
            var graph_xticks = [];
            var graph_data = [];
            var graph_counter = 0;
            var other = 0;
        }

        for (var i = 0; i < data.length; i++) {
            tr = document.createElement('tr');
            table.appendChild(tr);

            is_last = (i + 1) == data.length;

            if (is_last) {
                tr.setAttribute('class', 'final');
            } else if (i % 2 != 0) {
                tr.setAttribute('class', 'odd');
            }

            if (show_graph) {
                if (!is_last) {
                    if ((data[i][graph_column] / total) > 0.05) {
                        graph_xticks[graph_counter] = {v: graph_counter, label: data[i][0]};
                        graph_data[graph_counter] = [graph_counter, data[i][graph_column]];
                        graph_counter++;
                    } else { // Track too small to show slices.
                        other += data[i][graph_column];
                    }
                }
            }

            for (var j = 0; j < columns.length; j++) {
                var skip_total = columns[j].skip_total;
                var coltype = columns[j]['type'];
                var colindex = columns[j]['index'];

                td = document.createElement('td');

                if (is_last && skip_total) {
                    td.setAttribute('class', 'empty');
                    tr.appendChild(td);
                    continue;
                }

                if (coltype == 'money') {
                    td.setAttribute('class', 'right');
                    td.innerHTML = jQuery().number_format(data[i][colindex], { symbol: 'R$' });
                } else {
                    td.innerHTML = data[i][colindex];
                }

                tr.appendChild(td);
            }

        }

        var results_pane = document.getElementById('results');
        if (results_pane.firstChild != null) {
            results_pane.replaceChild(table, results_pane.firstChild);
        } else {
            results_pane.appendChild(table);
        }

        // Graph.

        // No graph will be displayed - make sure the canvas is empty.
        if (!show_graph) {
            return;
        }

        // The "Other" slice of the pie.
        graph_xticks[graph_counter] = {v: graph_counter, label: 'Outros'};
        graph_data[graph_counter] = [graph_counter, other];

        var options = {
            'xTicks': graph_xticks,
            'drawBackground': false,
            'axisLabelWidth': '90',
            'axisLabelFontSize': 12,
        };

        var layout = new Layout('pie', options);
        layout.addDataset('expenses', graph_data);
        layout.evaluate();

        var plotter = new PlotKit.SweetCanvasRenderer(canvas, layout, options);
        plotter.render();
    });
}
