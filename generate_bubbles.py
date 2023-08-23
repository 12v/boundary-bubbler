import fiona
import requests
import zipfile
import io
from shapely.geometry import shape
from shapely import Point, GeometryCollection, LineString, Polygon, MultiPolygon, union_all, minimum_rotated_rectangle, buffer, is_empty, intersection
from shapely.validation import make_valid
import os
import matplotlib.pyplot as plt
import math
import numpy as np

BUBBLE_LIMIT = 200
MIN_RADIUS = 1 * 1000

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

output_path = 'output/postcode_to_constituency_mapping.csv'

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

def test_bubbles(bounds, spacing, radius):
  minx, miny, maxx, maxy = bounds
  grid_points = []
  for i, y in enumerate(np.arange(miny, maxy, math.sqrt(3) * spacing * radius/10)):
    offset = 0 if i % 2 == 0 else spacing * radius / (2 * 10)
    for x in np.arange(minx + offset, maxx, math.sqrt(3) * spacing * radius/10):
      grid_points.append(Point(x, y))
  circles = [point.buffer(radius) for point in grid_points]
  circle_iterator = (circle for circle in circles if shape.contains(circle))
  valid_circles = [next(circle_iterator, None) for j in range(201)]
  valid_circles = [circle for circle in valid_circles if circle is not None]
  if len(valid_circles) > 200:
    return None
  else:
    return valid_circles

def calculate_radius_upper_bound(mrr):
  x, y = mrr.exterior.xy
  edge_lengths = (
    Point(x[0], y[0]).distance(Point(x[1], y[1])),
    Point(x[1], y[1]).distance(Point(x[2], y[2]))
  )

  width = min(edge_lengths)
  return int((width // 2000) * 1000)

def get_possible_centers(mrr, shape, radius):
  buffered_mrr = buffer(mrr, -radius)
  buffered_shape = buffer(shape, -radius)

  return intersection(buffered_mrr, buffered_shape)

for constituency in constituencies:
  print(constituency[0])
  shape = constituency[1]
  mrr = minimum_rotated_rectangle(shape)
  radius_upper_bound = calculate_radius_upper_bound(mrr)

  print("Upper bound for circle radius", radius_upper_bound)

  test_radius = radius_upper_bound
  possible_centers = None
  
  valid_circles = []

  while test_radius > 0:
    possible_centers = get_possible_centers(mrr, shape, test_radius)
    if not is_empty(possible_centers):
      polygons = possible_centers.geoms if isinstance(possible_centers, MultiPolygon) else [possible_centers]
      for polygon in polygons:
        for interpolation in np.arange(0, polygon.exterior.length, 1000):
          point = polygon.exterior.interpolate(interpolation)
          valid_circles.append(point.buffer(test_radius))
    test_radius -= 1000

  bounds = shape.bounds

  radius = 1000
  spacing_factor = 0
  # valid_circles = None

  # while (valid_circles is None):
  #   if spacing_factor < 10:
  #     spacing_factor += 1
  #   else:
  #     radius += 1000
  #     spacing_factor = 1
  #   valid_circles = test_bubbles(bounds, spacing_factor, radius)

  print(len(valid_circles), union_all(valid_circles).area/shape.area)

  fig, ax = plt.subplots()
  ax.set_aspect('equal', adjustable='box')
  if isinstance(shape, GeometryCollection) or isinstance(shape, MultiPolygon):
    for geom in shape.geoms:
      sub_shape = geom
      if isinstance(geom, LineString):
        continue
      x, y = sub_shape.exterior.xy
      ax.plot(x, y, color='blue')
  else:
    x, y = shape.exterior.xy
    ax.plot(x, y, color='blue')
  for valid_circle in valid_circles:
    x, y = valid_circle.exterior.xy
    ax.plot(x, y, color='red')
  x, y = mrr.exterior.xy
  ax.plot(x, y, color='green')
  polygons = []
  if isinstance(possible_centers, MultiPolygon):
    for geom in possible_centers.geoms:
      x, y = geom.exterior.xy
      ax.plot(x, y, color='yellow')
  else:
    x, y = possible_centers.exterior.xy
    ax.plot(x, y, color='yellow')
  plt.show()


# half the smallest dimension of the minimum-rotated rectangle sets the upper-bound for the radius
# we can also constrain the centre to be at least the radius away from the nearest minimum-rotate rectangle edge
# radius = 1km sets the lower-bound
# binary search to find the radius and position of largest enclosed circle