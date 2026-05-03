import heapq
import math
from flask import Flask, request, jsonify, render_template
import osmnx as ox
import pyproj

app = Flask(__name__)

oras = "Baia Mare, Romania"

G = ox.graph_from_place(oras, network_type='drive')
G = ox.project_graph(G)

projector = pyproj.Transformer.from_crs("epsg:4326", G.graph["crs"], always_xy=True)
projector_back = pyproj.Transformer.from_crs(G.graph["crs"], "epsg:4326", always_xy=True)

@app.route("/")
def index():
    return render_template("index.html")

def shortest_path(n1, n2):
    x1, y1 = G.nodes[n1]['x'], G.nodes[n1]['y']
    x2, y2 = G.nodes[n2]['x'], G.nodes[n2]['y']
    return math.hypot(x1 - x2, y1 - y2)

def astar(G, start, goal):
    open_set = []
    heapq.heappush(open_set, (0, start))

    came_from = {}
    g_score = {start: 0}

    f_score = {start: shortest_path(start, goal)}

    while open_set:
        _, nod_curent = heapq.heappop(open_set)

        if nod_curent == goal:
            path = [nod_curent]
            while nod_curent in came_from:
                nod_curent = came_from[nod_curent]
                path.append(nod_curent)
            return path[::-1]

        for vecin in G.neighbors(nod_curent):
            edge_data = G.get_edge_data(nod_curent, vecin)
            edge = min(edge_data.values(), key=lambda x: x.get("length", 1))
            weight = edge.get("length", 1)

            g_posibil = g_score[nod_curent] + weight

            if vecin not in g_score or g_posibil < g_score[vecin]:
                came_from[vecin] = nod_curent
                g_score[vecin] = g_posibil
                f = g_posibil + shortest_path(vecin, goal)
                heapq.heappush(open_set, (f, vecin))

    return None

def nearest_node_from_edge(G, x, y):
    u, v, key = ox.distance.nearest_edges(G, x, y)

    x_u, y_u = G.nodes[u]['x'], G.nodes[u]['y']
    x_v, y_v = G.nodes[v]['x'], G.nodes[v]['y']

    dist_u = math.hypot(x - x_u, y - y_u)
    dist_v = math.hypot(x - x_v, y - y_v)

    return u if dist_u < dist_v else v

@app.route("/route", methods=["POST"])
def route():
    data = request.json

    if "start_address" in data and "end_address" in data:
        start_lat, start_lon = ox.geocode(data["start_address"])
        end_lat, end_lon = ox.geocode(data["end_address"])
    else:
        start_lat, start_lon = data["start"]
        end_lat, end_lon = data["end"]

    x1, y1 = projector.transform(start_lon, start_lat)
    x2, y2 = projector.transform(end_lon, end_lat)

    orig = nearest_node_from_edge(G, x1, y1)
    dest = nearest_node_from_edge(G, x2, y2)

    route = astar(G, orig, dest)

    distanta_totala = 0

    coords = []

    for i, (u, v) in enumerate(zip(route[:-1], route[1:])):
        edge_data = G.get_edge_data(u, v)
        edge = min(edge_data.values(), key=lambda x: x.get("length", 1))
        distanta_totala += edge.get("length", 0)

        if "geometry" in edge:
            xs, ys = edge["geometry"].xy
            points = list(zip(xs, ys))
        else:
            points = [
                (G.nodes[u]['x'], G.nodes[u]['y']),
                (G.nodes[v]['x'], G.nodes[v]['y'])
            ]

        if i > 0:
            points = points[1:]

        for x, y in points:
            lon, lat = projector_back.transform(x, y)
            coords.append((lat, lon))

    return jsonify({
        "route": coords,
        "distance": distanta_totala
    })


if __name__ == "__main__":
    app.run(debug=True)
