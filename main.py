# Time to scrape a website
# The goal is to scrape an entire website that contain fish photos of a specie
import os
import argparse
from pyinaturalist import get_observation_species_counts
import re
import time
import requests
from PIL import Image
from io import BytesIO
import concurrent.futures
from threading import Lock
from diskcache import Cache

root_folder = "fish_photos"  # Root folder where species folders will be created

# Thread-safe counters
request_count = 0
species_done = 0
total_results = 0
lock = Lock()
cache = Cache('cache', size_limit=1 * 1024 * 1024 * 1024)

def to_snake_case(string):
    # Replace spaces with underscores
    string = re.sub(r'[\s]+', '_', string)
    
    # Convert camelCase or PascalCase to snake_case
    string = re.sub(r'([a-z])([A-Z])', r'\1_\2', string)
    
    # Convert all characters to lowercase
    string = string.lower()
    
    return string

def create_species_folder(root_folder, species_name):
    species_folder = os.path.join(root_folder, species_name)
    if not os.path.exists(species_folder):
        os.makedirs(species_folder)
    return species_folder

# Define a function to introduce a delay to respect the rate limit
def respect_rate_limit():
    global request_count
    if request_count >= 60:
        print("Rate limit reached, waiting for next minute...")
        time.sleep(60)  # Wait for the next minute to avoid exceeding the limit
        request_count = 0  # Reset the request count
    else :
        request_count += 1

def download_and_process_photo(photo_url, species_folder, photo_index):
    try:
        # Download the image
        response = requests.get(photo_url)
        if response.status_code == 200:
            
            # Ensure the content is actually an image
            if 'image' not in response.headers['Content-Type']:
                print(f"Skipping non-image URL: {photo_url}")
                return  # Skip if it's not an image
            img = Image.open(BytesIO(response.content))
                        
            # Check the image format before saving
            if img.format not in ['JPEG', 'PNG']:
                print(f"Skipping non-JPEG/PNG image: {photo_url}")
                return  # Skip non-JPEG/PNG files
            
            # Check if image dimensions are valid (non-zero width/height)
            if img.width == 0 or img.height == 0:
                print(f"Skipping invalid image with zero dimensions: {photo_url}")
                return  # Skip images with invalid dimensions

            # Save the image with a unique name
            photo_filename = f"{species_folder}/photo_{photo_index}.{img.format.lower()}"
                        
            if img.mode != 'RGB' and img.format == 'JPEG':
                # Convert the image to RGB if it is a JPEG (other formats may need different handling)
                img = img.convert('RGB')
            
            img.save(photo_filename)

            # print(f"Downloaded and saved {photo_filename}")
        else:
            print(f"Failed to download image: {photo_url}")
    except Exception as e:
        print(f"Error downloading image {photo_url}: {e}")

def get_observations(taxon_id, quality_grade, order_by, photos, per_page):
    params = {
        'taxon_id': taxon_id,
        'order_by': order_by,
        'quality_grade': quality_grade,
        'photo_license': 'any',
        'photos': photos,
        'page' : '',
        'per_page': per_page 
    }
    try :
        r = requests.get(url="https://api.inaturalist.org/v1/observations", params=params, timeout=5)
        return r.json()
    except requests.exceptions.RequestException as e :
        raise e
    
def search_specy(query):
    params = {
       'q' : query
    }
    try :
        r = requests.get(url="https://api.inaturalist.org/v1/search", params=params)
        return r.json()
    except requests.exceptions.RequestException as e :
        raise e
    

def cached_get_observations(taxon_id, quality_grade, order_by, photos, per_page, species_folder):
    cache_key = species_folder 
    if cache_key in cache:
        print(f"Cache used for {species_folder}")
        return cache[cache_key]
    else :
        lock.acquire()
        respect_rate_limit()
        lock.release()
      
        res = get_observations(taxon_id=taxon_id, quality_grade=quality_grade, order_by=order_by, photos=photos, per_page=per_page)
        cache[cache_key] = res
        return res

def process_specy(specy, nb_img):
    global request_count, species_done
    
    common_name = to_snake_case(specy['taxon']['name'])
    species_folder = os.path.join(root_folder, common_name)
    
    if os.path.exists(species_folder) :
        num_images = len([name for name in os.listdir(species_folder) if os.path.isfile(os.path.join(species_folder, name))])
        
        if num_images >= 30 :
            with lock:
                species_done += 1
                # print("🫵 Already found ", common_name)     
                # report_stats()
            return

    species_folder = create_species_folder(root_folder, common_name)
    
    # print(f"Getting observations for {common_name}")
    obs = cached_get_observations(taxon_id=specy['taxon']['id'], quality_grade="research", order_by="votes", photos=True, per_page=nb_img, species_folder=species_folder)
    total_results = obs['total_results']
    obs = obs['results']
    # print("Observations fetched for ", common_name, " !")
    
    photo_urls = []
    for anObs in obs :
        if anObs['observation_photos']: 
            photoUrl = anObs['observation_photos'][0]['photo']['url']
            mediumPhotoUrl = re.sub(r'square', 'medium', photoUrl, count=1)
            photo_urls.append(mediumPhotoUrl)
        
    num_images = len([name for name in os.listdir(species_folder) if os.path.isfile(os.path.join(species_folder, name))])
    if num_images < 100 and num_images < total_results:
        # Download photos in parallel with ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(lambda url: download_and_process_photo(url[1], species_folder, url[0]), enumerate(photo_urls))
    
    with lock:
        species_done += 1
        
    num_images = len([name for name in os.listdir(species_folder) if os.path.isfile(os.path.join(species_folder, name))])
        
    print(f"🐟 Done specy: {common_name} with {num_images} images")
    report_stats()

def report_stats():
    global request_count, species_done, total_results
    print(f"Total requests made: {request_count}")
    print(f"Runtime progress : {(species_done / total_results) * 100 }%")
    
def process_indian_oceanic_fish_species(nb_img):
    page = 1
    per_page = 500  # Maximum number of results per page
    observations = get_observation_species_counts(
        lat=-15.760536148501288,
        lng=77.64325073204107,
        radius=4054.037977613122,
        iconic_taxa="Actinopterygii",
        captive=False,
        spam=False,
        verifiable=True,
        per_page=per_page,
        page=page
    )
    
    total_results = observations['total_results']
    print(f'Total species to process: {total_results}')
    
    all_species = observations['results']
    
    # Loop through pages to get all results
    while len(all_species) < total_results:
        page += 1
        observations = get_observation_species_counts(
            lat=-15.760536148501288,
            lng=77.64325073204107,
            radius=4054.037977613122,
            iconic_taxa="Actinopterygii",
            captive=False,
            spam=False,
            verifiable=True,
            per_page=per_page,
            page=page
        )
        all_species.extend(observations['results'])
    
    print(f'Total species fetched: {len(all_species)}')
    
    # Process species in parallel using ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(process_specy, all_species, [nb_img] * len(all_species))

if __name__ == "__main__":  
    parser = argparse.ArgumentParser(description="Scrape fish photos from iNaturalist")
    parser.add_argument('--species', type=int, help="Taxon name the species to process (scientific name)")
    parser.add_argument('--num_images', type=int, help="Number of images to download per species", default=100)
    args = parser.parse_args()
    
    if args.species:
        # TODO: fetch the specy from scientific name
        taxonNameList = args.species.split(",")
        for taxonName in taxonNameList:
            r = search_specy(taxonName)
            if r['total_results'] > 0:
                specy = r['results'][0]
                process_specy(specy=specy, nb_img=args.num_images)
            else :
                raise ValueError(f'Specy not found for {taxonName}')
    else :
        process_indian_oceanic_fish_species(nb_img=args.num_images)