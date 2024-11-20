# 🍃 iNaturalist Dataset Creator
A tool for creating image datasets by leveraging the open iNaturalist API. This project allows you to collect images of various species and organize them into a dataset, sorted by their scientific names.
### Features
- **Automated Data Collection**: Fetch images from iNaturalist based on specified species.
- **Organized Dataset**: The images are stored in a directory structure where each species has its own subfolder named after its scientific name.
- **Customizable**: You can specify which species to collect, the number of images, and other parameters.
### Output
The tool generates a root folder containing subfolders for each species. The subfolders are named after the scientific name of each species, and contain the respective images.
#### Folder Structure
```
<root-folder>
│
├── <species-name-1>/
│   ├── image_1.jpg
│   ├── image_2.jpg
│   └── ...
│
├── <species-name-2>/
│   ├── image_1.jpg
│   ├── image_2.jpg
│   └── ...
│
└── ...
```
### Installation
1. Clone this repository
   ```bash
   git clone https://github.com/your-username/inaturalist-dataset-creator.git
   ```
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Usage
1. **Run the script** to start downloading images for the species you want:
   ```bash
   python create_dataset.py --species "Homo sapiens, Canis lupus, Panthera leo" --num_images 50
   ```
2. **Arguments:**
   - --species: A comma-separated list of species names (common or scientific).
   - --num_images: The number of images to fetch for each species (default is 30).
3. The images will be saved in a folder structure as described above.

### Example
```bash
python create_dataset.py --species "Ailuropoda melanoleuca, Panthera tigris" --num_images 100
```
This will create a folder structure where each species (Giant Panda, Bengal Tiger) will have 100 images downloaded from iNaturalist.
### Contributing
Feel free to submit pull requests for bug fixes, improvements, or additional features!

