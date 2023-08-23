import fiona
import requests
import zipfile
import io
from shapely.geometry import shape
from shapely import Point, GeometryCollection, LineString, MultiPolygon, union_all, minimum_rotated_rectangle, buffer, is_empty
from shapely.validation import make_valid
import os
import matplotlib.pyplot as plt
import numpy as np
import pyproj
import csv

BUBBLE_LIMIT = 200

england_shapefile_url = 'https://boundarycommissionforengland.independent.gov.uk/wp-content/uploads/2023/06/984162_2023_06_27_Final_recommendations_England_shp.zip'
scotland_shapefile_path = 'https://www.bcomm-scotland.independent.gov.uk/sites/default/files/2023_review_final/bcs_final_recs_2023_review.zip'
wales_shapefile_path = 'https://bcomm-wales.gov.uk/sites/bcomm/files/review/Shapefiles.zip'

england_shapefile_filename = '2023_06_27_Final_recommendations_England.shp'
scotland_shapefile_filename = 'All_Scotland_Final_Recommended_Constituencies_2023_Review.shp'
wales_shapefile_filename = 'Final Recs Shapefiles/Final Recommendations_region.shp'

def download_and_extract(url, path):
    if not os.path.exists('data/' + path):
        response = requests.get(url)
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        zip_file.extractall('data/' + path)

download_and_extract(england_shapefile_url, 'england')
download_and_extract(scotland_shapefile_path, 'scotland')
download_and_extract(wales_shapefile_path, 'wales')

def create_constituency_list(shapefile_path, constituency_name_key):
   constituencies = []
   with fiona.open('data/' + shapefile_path) as boundaries:
    for constituency in boundaries:
      constituency_shape = make_valid(shape(constituency['geometry']))
      constituencies.append((constituency.properties[constituency_name_key], constituency_shape))
    return constituencies

england_constituencies = create_constituency_list('england/' + england_shapefile_filename, 'Constituen')
scotland_constituencies = create_constituency_list('scotland/' + scotland_shapefile_filename, 'NAME')
wales_constituencies = create_constituency_list('wales/' + wales_shapefile_filename, 'Official_N')

constituencies = england_constituencies + scotland_constituencies + wales_constituencies

if not os.path.exists('output'):
    os.makedirs('output')

transformer = pyproj.Transformer.from_crs("epsg:27700", "epsg:4326")

def calculate_radius_upper_bound(boundary):
  mrr = minimum_rotated_rectangle(boundary)
  x, y = mrr.exterior.xy
  edge_lengths = (
    Point(x[0], y[0]).distance(Point(x[1], y[1])),
    Point(x[1], y[1]).distance(Point(x[2], y[2]))
  )

  width = min(edge_lengths)
  return int((width // 2000) * 1000)

def calculate_step(polygons, radius, iteration_count, bubble_length):
  total_polygon_length = sum([polygon.exterior.length for polygon in polygons])
  iteration_bubble_count = total_polygon_length / radius
  step = radius
  is_last_iteration = radius == 1000 or iteration_count == 2 or (bubble_length + iteration_bubble_count) > BUBBLE_LIMIT
  
  if is_last_iteration:
    step = total_polygon_length / (BUBBLE_LIMIT - bubble_length)

  return step

def calculate_bubbles(boundary):
  radius = calculate_radius_upper_bound(boundary)
  island_of_possibility = None
  iteration_count = 0
  
  bubbles = []
  bubblesData = []

  while radius > 0 and iteration_count < 3:
    island_of_possibility = buffer(boundary, -(radius + 30))

    if not is_empty(island_of_possibility):
      print(radius)
      polygons = island_of_possibility.geoms if isinstance(island_of_possibility, MultiPolygon) else [island_of_possibility]

      step = calculate_step(polygons, radius, iteration_count, len(bubbles))
      for polygon in polygons:
        for interpolation in np.arange(0, polygon.exterior.length, step):
          point = polygon.exterior.interpolate(interpolation)
          bubble = point.buffer(radius)
          if boundary.contains(bubble):
            bubbles.append(bubble)
            bubblesData.append([point.x, point.y, int(radius / 1000)])

    if len(bubbles) > 0:
      iteration_count += 1
      radius = (radius // 1500) * 1000
    else:
      radius -= 1000

  return bubbles[:BUBBLE_LIMIT], bubblesData[:BUBBLE_LIMIT]

with (
  open('output/bubbles.csv', 'w') as csv_output,
  open('output/statistics.csv', 'w') as stastics_output
):
  output_writer = csv.writer(csv_output)
  output_writer.writerow(['bubble', 'constituency'])

  statistics_writer = csv.writer(stastics_output)
  statistics_writer.writerow(['constituency', 'coverage'])

  statistics = []

  for constituency in constituencies:
    constituency_name = constituency[0]
    boundary = constituency[1]
    print(constituency_name)

    bubbles, bubblesData = calculate_bubbles(boundary)

    for (x, y, radius) in bubblesData:
      lat, long = transformer.transform(x, y)
      output_writer.writerow(['({}, {}) +{}km'.format(lat, long, radius), constituency_name])

    fig, ax = plt.subplots(1, 2)
    ax[0].set_aspect('equal', adjustable='box')
    ax[1].set_aspect('equal', adjustable='box')
    fig.suptitle(constituency_name)
    coverage_percentage = 100 * union_all(bubbles).area / boundary.area

    statistics_writer.writerow([constituency_name, coverage_percentage])
    statistics.append(coverage_percentage)
    fig.text(0.5, 0.9, '{:.0f}% coverage'.format(coverage_percentage), ha='center', fontsize=12)

    ax[0].xaxis.set_visible(False)
    ax[0].yaxis.set_visible(False)

    ax[1].xaxis.set_visible(False)
    ax[1].yaxis.set_visible(False)

    polygons = boundary.geoms if isinstance(boundary, GeometryCollection) or isinstance(boundary, MultiPolygon) else [boundary]
    for polygon in polygons:
      if isinstance(polygon, LineString):
        continue
      x, y = polygon.exterior.xy
      ax[0].plot(x, y, color='blue')
      ax[1].plot(x, y, color='blue')

    for valid_circle in bubbles:
      x, y = valid_circle.exterior.xy
      ax[0].plot(x, y, color='red', linewidth=0.5)
      ax[1].fill(x, y, color='red')

    fig.savefig('output/JPGs/' + constituency_name + '.jpg', dpi=300)
    plt.close(fig)
  
  statistics_writer.writerow(['', ''])
  statistics_writer.writerow(['mean', sum(statistics) / len(statistics)])
  statistics_writer.writerow(['median', np.median(statistics)])
  statistics_writer.writerow(['min', min(statistics)])
  statistics_writer.writerow(['max', max(statistics)])
  statistics_writer.writerow(['sigma', np.std(statistics)])
