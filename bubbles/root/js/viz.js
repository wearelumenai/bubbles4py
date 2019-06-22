function DetailDisplay(container) {
    let centers;
    let columns;

    function _init(config) {
        ({centers, columns} = config);
        container.append("p").classed("caption", true);
        container
            .selectAll("div")
            .data(columns)
            .enter()
            .append("div")
            .html('<div></div><div></div>');
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

    function _init(config) {
        ({centers, columns} = config);
        container.selectAll('div.dim-picker').data([
            {id: 'select-s', label: 'Size'},
            {id: 'select-c', label: 'Color'},
            {id: 'select-y', label: 'Y'},
            {id: 'select-x', label: 'X'},
        ]).enter()
            .append('div')
            .lower()
            .html(d => `<label for="${d.id}">${d.label}</label><select id="${d.id}"></select>`);
        const current = {x: 0, y: 1, c: 2, s: columns.length - 1};
        loadOptions(current, 'x');
        loadOptions(current, 'y');
        loadOptions(current, 'c');
        loadOptions(current, 's');
        dimensionChanged(current);
    }

    function loadOptions(current, dim) {
        const selector = `#select-${dim}`;
        container.select(selector)
            .on('change', () => {
                current[dim] = container.select(selector).property('selectedIndex');
                dimensionChanged(current);
            })
            .selectAll('option')
            .data(columns)
            .enter()
            .append('option')
            .property('selected', (_, i) => i === current[dim])
            .text(d => d);
    }

    async function dimensionChanged({x, y, c, s}) {
        const data = centers.map(r => [r[x], r[y], r[c], r[s]]);
        const dimensions = {"x": columns[x], "y": columns[y], "color": columns[c], "area": columns[s]};
        update(data, dimensions);
    }

    return {_init}
}

function startViz(result, dimensionPicker, detailsDisplay) {
    const columns = result.columns.concat(['counts']);
    const centers = result.centers.map((r, i) => r.concat([result.counts[i]]));
    dimensionPicker._init({centers, columns});
    detailsDisplay._init({centers, columns})
}

function getResultId() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('result_id');
}

