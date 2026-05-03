var map = L.map('map').setView([47.6573, 23.5681], 14);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: 'OSM'
}).addTo(map);

var clicks = [];
var routeLine;
var markers = [];

function clearMap() {
    markers.forEach(m => map.removeLayer(m));
    markers = [];

    if (routeLine) {
        map.removeLayer(routeLine);
        routeLine = null;
    }
}

function normalizeAddress(str) {
    return str
        .toLowerCase()
        .trim();
}

map.on('click', function(e) {

    if (clicks.length === 0 && markers.length > 0) {
        clearMap();
    }

    clicks.push([e.latlng.lat, e.latlng.lng]);

    var marker = L.marker(e.latlng).addTo(map);
    markers.push(marker);

    if (clicks.length == 2) {
        fetch('/route', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                start: clicks[0],
                end: clicks[1]
            })
        })
        .then(res => res.json())
        .then(data => {

            if (routeLine) {
                map.removeLayer(routeLine);
            }

            routeLine = L.polyline(data.route, {color: 'blue'}).addTo(map);

            document.getElementById("distance").innerText =
            "Distanta: " + (data.distance / 1000).toFixed(2) + "km";
        });

        clicks = [];
    }
});

function calcRoute() {
    clearMap();
    const start = normalizeAddress(document.getElementById("start").value);
    const end = normalizeAddress(document.getElementById("end").value);

    fetch('/route', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            start_address: start,
            end_address: end
        })
    })
    .then(res => res.json())
    .then(data => {

        if (routeLine) {
            map.removeLayer(routeLine);
        }

        routeLine = L.polyline(data.route, {color: 'blue'}).addTo(map);

        document.getElementById("distance").innerText =
            "Distanta: " + (data.distance / 1000).toFixed(2) + " km";

        map.fitBounds(routeLine.getBounds());
    });
}