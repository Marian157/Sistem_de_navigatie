from flask import Flask, request, jsonify
import osmnx as ox
import networkx as nx
import pyproj

app = Flask(__name__)

oras = "Baia Mare, Romania"

G = ox.graph_from_place(oras, network_type='drive')
G = ox.project_graph(G)

@app.route("/")
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Navigator</title>
        <meta charset="utf-8" />
        <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
        <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
    </head>
    <body>
    <div id="map" style="height: 100vh;"></div>

    <script>
    var map = L.map('map').setView([47.6573, 23.5681], 14);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: 'OSM'
    }).addTo(map);
    
    var clicks = [];
    var routeLine;
    var markers = [];

    map.on('click', function(e) {

        if (clicks.length === 0 && markers.length > 0) {
            markers.forEach(m => map.removeLayer(m));
            markers = [];

            if (routeLine) {
                map.removeLayer(routeLine);
            }
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
        });

        clicks = [];
    }
});
    </script>
    </body>
    </html>
    """

@app.route("/route", methods=["POST"])
def route():
    data = request.json
    start = data["start"]
    end = data["end"]

    projector = pyproj.Transformer.from_crs("epsg:4326", G.graph["crs"], always_xy=True)

    x1, y1 = projector.transform(start[1], start[0])
    x2, y2 = projector.transform(end[1], end[0])

    orig = ox.distance.nearest_nodes(G, x1, y1)
    dest = ox.distance.nearest_nodes(G, x2, y2)

    route = nx.shortest_path(G, orig, dest, weight='length')

    projector_back = pyproj.Transformer.from_crs(G.graph["crs"], "epsg:4326", always_xy=True)

    coords = []

    for u, v in zip(route[:-1], route[1:]):
        edge_data = G.get_edge_data(u, v)

        edge = list(edge_data.values())[0]

        if "geometry" in edge:
            xs, ys = edge["geometry"].xy
            for x, y in zip(xs, ys):
                lon, lat = projector_back.transform(x, y)
                coords.append((lat, lon))
        else:
            x = G.nodes[u]['x']
            y = G.nodes[u]['y']
            lon, lat = projector_back.transform(x, y)
            coords.append((lat, lon))

    return jsonify({"route": coords})

if __name__ == "__main__":
    app.run(debug=True)
