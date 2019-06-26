function DetailDisplay(container) {
    let centers;
    let columns;
    let initialized = false;

    function _init(config) {
        if (!initialized) {
            ({centers, columns} = config);
            container.append("p").classed("caption", true);
            container
                .selectAll("div")
                .data(columns)
                .enter()
                .append("div")
                .html('<div></div><div></div>');
            initialized = true;
        }
    }

    async function detailChanged(id) {
        const data = centers[id].map((c, i) => [columns[i], c]);
        container.classed("active", true);
        container.selectAll("p")
            .data([id])
            .text(`cluster ${id} details:`);
        container.selectAll(":scope > div")
            .data(data)
            .selectAll("div")
            .data(d => d)
            .text(d => d);
    }

    return {_init, detailChanged}
}

function DimensionPicker(container, update) {
    let centers;
    let columns;
    let current;
    let initialized = false;

    function _init(config) {
        ({centers, columns} = config);
        if (!initialized) {
            ({current} = config);
            container.selectAll('div.dim-picker').data([
                {id: 'select-s', label: 'Size'},
                {id: 'select-c', label: 'Color'},
                {id: 'select-y', label: 'Y'},
                {id: 'select-x', label: 'X'},
            ]).enter()
                .append('div')
                .lower()
                .html(d => `<label for="${d.id}">${d.label}</label><select id="${d.id}"></select>`);
            loadOptions( 'x');
            loadOptions('y');
            loadOptions( 'c');
            loadOptions( 's');
            initialized = true;
        }
        dimensionChanged();
    }

    function loadOptions( dim) {
        const selector = `#select-${dim}`;
        container.select(selector)
            .on('change', () => {
                current[dim] = container.select(selector).property('selectedIndex');
                dimensionChanged();
            })
            .selectAll('option')
            .data(columns)
            .enter()
            .append('option')
            .property('selected', (_, i) => i === current[dim])
            .text(d => d);
    }

    async function dimensionChanged() {
        const {x, y, c, s} = current;
        const data = centers.map(r => [r[x], r[y], r[c], r[s]]);
        const dimensions = {"x": columns[x], "y": columns[y], "color": columns[c], "area": columns[s]};
        update(data, dimensions);
    }

    return {_init}
}

function startViz(result, dimensionPicker, detailsDisplay) {
    const columns = result.columns.concat(['counts']);
    const centers = result.centers.map((r, i) => r.concat([result.counts[i]]));
    const current = {x: 0, y: 1, c: 2, s: columns.length - 1};
    dimensionPicker._init({centers, columns, current});
    detailsDisplay._init({centers, columns, current})
}

function getResultId() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('result_id');
}

