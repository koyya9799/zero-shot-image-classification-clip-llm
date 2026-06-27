# backend/config.py
from typing import Dict, List

# Configuration for dynamic domains
# We can easily add new domains here without changing model logic

DOMAINS: List[str] = [
    "animal",
    "industrial",
    "medical",
    "vegetable",
    "vehicle",
    "satellite image",
    "food",
    "fashion item"
]

# Keywords for text embedding when matching domain
DOMAIN_PROMPTS: Dict[str, str] = {
    "animal": "an image of an animal, wildlife, or pet",
    "industrial": "an image of industrial machinery, welding, metalwork, manufacturing, factory equipment, or mechanical component",
    "medical": "a medical radiology image such as x-ray, MRI, or CT scan",
    "vegetable": "an image of fresh vegetables, crops, harvested produce, or agricultural products",
    "vehicle": "an image of a vehicle, car, truck, or traffic scene",
    "satellite image": "a satellite or aerial top view image",
    "food": "an image of food, meal, dish, or fresh produce items",
    "fashion item": "an image of clothing, fashion item, or apparel"
}

# Domain-to-label base classes used by zero-shot prediction.
BASE_CLASSES: Dict[str, List[str]] = {
    "medical": [
        "chest x-ray", "normal chest x-ray", "radiology image", "MRI scan", "CT scan", "brain MRI",
        "fundus image", "retinal photograph", "ophthalmology", "optic disc",
        "pneumonia", "tuberculosis", "lung cancer", "covid-19", "pneumothorax", "pulmonary edema",
        "asthma", "bronchitis", "emphysema", "chronic obstructive pulmonary disease",
        "alzheimer's disease", "brain atrophy", "dementia", "neurodegenerative disease",
        "parkinson's disease", "huntington's disease", "multiple sclerosis", "stroke",
        "brain tumor", "glioma", "meningioma", "brain metastasis", "grey matter atrophy",
        "white matter disease", "traumatic brain injury", "brain lesion",
        "diabetic retinopathy", "proliferative diabetic retinopathy", "non-proliferative diabetic retinopathy",
        "normal fundus", "normal retina", "healthy retina",
        "glaucoma", "retinopathy", "eye disease",
        "retinal damage", "age-related macular degeneration", "macular edema",
        "cataract", "retinal detachment", "optic neuritis", "optic disc hemorrhage",
        "cotton wool spots", "hard exudates", "microaneurysms", "branch retinal artery occlusion",
        "central retinal artery occlusion", "diabetic macular edema",
        "bone fracture", "osteoarthritis", "rheumatoid arthritis", "bone tumor",
        "osteoporosis", "spinal stenosis", "herniated disc", "ligament tear",
        "meniscus tear", "dislocated joint", "bone metastasis", "bone lesion",
        "leukemia", "lymphoma", "melanoma", "skin cancer", "breast cancer",
        "prostate cancer", "colon cancer", "pancreatic cancer", "liver cancer",
        "ulcer", "gastritis", "colitis", "crohn's disease", "polyp",
        "epidermoid cyst", "cyst", "infection", "inflammation", "hemorrhage",
        "edema", "fibrosis", "nodule", "mass", "abscess",
        "normal anatomy", "healthy", "abnormal", "pathological finding",
    ],
    "industrial": [
        # Generic industrial classes
        "machinery", "factory", "assembly line", "warehouse",
        "industrial equipment", "manufacturing", "industrial process",
        
        # Welding and metal joining
        "welding", "welded joint", "weld seam", "weld bead",
        
        # Weld defects (HIGH CONFIDENCE LABELS)
        "weld crack defect", "metal weld crack", "fatigue crack in steel",
        "weld crack", "structural weld crack", "fatigue crack",
        "metal surface fracture", "weld joint fracture",
        "cracked welded metal", "fractured weld seam",
        "weld failure", "weld defect",
        
        # Metal defects and damage
        "metal crack", "structural crack", "surface fracture",
        "stress fracture", "fatigue failure",
        
        # Metal surface conditions
        "corroded metal", "rusted metal", "metal corrosion", "rust", "oxidation",
        "metal surface degradation", "oxidized steel surface",
        
        # Metalwork
        "metalwork", "metal fabrication", "fabrication", "metal joint",
        "steel joint", "metal plate",
        
        # Metal shaping processes
        "machining", "casting", "forging",
    ],
    "vegetable": [
        "vegetable", "fresh vegetable", "organic vegetable", "seasonal vegetable",
        # Generic categories
        "vegetable", "fresh vegetable", "organic vegetable", "seasonal vegetable",
        "leafy green", "root vegetable", "cruciferous vegetable", "allium vegetable",
        "legume vegetable", "gourd vegetable", "stem vegetable", "bulb vegetable",
        
        # Display and retail context
        "vegetable display", "fresh vegetables display", "produce display", "grocery produce",
        "vegetables in store", "supermarket vegetables", "farmers market vegetables",
        "organized vegetables", "vegetable arrangement", "produce section", "vegetable shelf",
        "fresh vegetables on shelf", "grocery shelf vegetables", "retail vegetable display",
        
        # Leafy and green vegetables
        "spinach", "lettuce", "kale", "cabbage", "green cabbage", "fresh cabbage",
        "napa cabbage", "bok choy", "swiss chard", "collard greens", "arugula",
        "mustard greens", "romaine lettuce", "iceberg lettuce", "endive", "watercress",
        "moringa leaves", "fresh greens", "salad greens",
        
        # Cruciferous vegetables
        "broccoli", "cauliflower", "fresh cauliflower", "white cauliflower",
        "brussels sprouts", "broccolini", "kohlrabi",
        
        # Root vegetables
        "carrot", "fresh carrot", "orange carrot", "carrots bunch",
        "beetroot", "parsnip", "sweet potato", "potato", "potatoes", "fresh potato",
        "cassava", "taro", "celeriac", "jicama", "daikon", "ginger", "turmeric",
        "radish", "turnip", "rutabaga",
        
        # Allium vegetables (onion family)
        "onion", "red onion", "white onion", "yellow onion", "green onion", "scallion",
        "leek", "shallot", "garlic", "chive",
        
        # Gourd and cucurbit vegetables
        "cucumber", "fresh cucumber", "cucumbers",
        "pumpkin", "pumpkins", "winter squash", "squash",
        "bottle gourd", "ridge gourd", "bitter gourd", "snake gourd",
        "ash gourd", "sponge gourd", "zucchini", "okra",
        
        # Fruiting vegetables
        "tomato", "eggplant", "bell pepper", "bell peppers", "red pepper", "yellow pepper", "green pepper",
        "capsicum", "mixed peppers", "peppers in store", "chili pepper", "jalapeno",
        "green beans", "french beans", "runner beans", "broad beans", "peas",
        "snow peas", "sugar snap peas", "edamame", "lima beans",
        
        # Stem and specialty vegetables
        "celery", "asparagus", "artichoke", "fennel", "banana stem", "lotus stem",
        "drumstick", "ivy gourd", "cluster beans", "amaranth leaves",
        "fenugreek leaves", "plantain", "raw banana", "green papaya",
        "chayote", "pointed gourd", "tindora", "chow chow",
    ],
    "animal": [
        "dog", "cat", "bird", "wildlife", "mammal", "reptile", "animal",
        "lion", "tiger", "bear", "elephant", "giraffe", "zebra", "monkey", "gorilla", "chimpanzee", "ape",
        "wolf", "fox", "deer", "moose", "elk", "rabbit", "hare", "squirrel", "raccoon",
        "horse", "cow", "pig", "sheep", "goat", "chicken", "duck", "goose", "turkey",
        "eagle", "hawk", "owl", "falcon", "penguin", "ostrich", "parrot", "flamingo",
        "snake", "lizard", "turtle", "crocodile", "alligator", "frog", "toad", "salamander",
        "fish", "shark", "whale", "dolphin", "seal", "walrus", "octopus", "squid", "crab", "lobster",
        "spider", "insect", "butterfly", "bee", "ant", "beetle", "fly", "mosquito",
    ],
    "vehicle": [
        # Generic vehicle classes
        "vehicle", "transport vehicle", "traffic scene", "road vehicle",

        # Passenger and personal vehicles
        "car", "sedan", "hatchback", "suv", "pickup truck", "van", "minivan",
        "taxi", "police car", "ambulance", "fire truck",

        # Heavy and commercial vehicles
        "truck", "cargo truck", "trailer truck", "dump truck", "cement mixer",
        "tow truck", "delivery van", "forklift", "tractor", "bulldozer", "excavator",

        # Public transport
        "bus", "city bus", "school bus", "coach bus", "tram", "metro train", "train",

        # Two and three wheelers
        "motorcycle", "scooter", "bicycle", "electric bicycle", "rickshaw", "auto rickshaw",

        # Water transport
        "boat", "ship", "ferry", "cargo ship", "sailboat", "speedboat", "yacht", "submarine",

        # Air transport
        "airplane", "passenger airplane", "cargo airplane", "helicopter", "drone",

        # Rail and special transport
        "locomotive", "freight train", "bullet train", "tank", "military vehicle",
    ],
    "satellite image": [
        # Generic remote sensing classes
        "satellite view", "aerial view", "top view", "remote sensing image",

        # Land cover classes
        "urban area", "residential area", "industrial area", "commercial area",
        "vegetation", "forest", "grassland", "shrubland", "wetland",
        "agricultural land", "crop field", "orchard", "plantation", "fallow land",
        "desert", "sand dunes", "bare soil", "rocky terrain", "mountain range",
        "snow", "glacier", "ice",

        # Water bodies
        "water", "river", "lake", "reservoir", "pond", "canal", "coastline", "ocean",

        # Built infrastructure
        "road network", "highway", "railway", "bridge", "airport", "runway", "harbor", "port",
        "dam", "solar farm", "wind farm",

        # Risk and event patterns
        "flooded area", "burned area", "deforestation", "landslide", "urban expansion",
    ],
    "fashion item": [
        # Generic fashion classes
        "fashion item", "apparel", "clothing", "outfit", "garment",

        # Tops
        "shirt", "t-shirt", "polo shirt", "blouse", "tank top", "sweater", "hoodie",
        "jacket", "coat", "blazer", "cardigan", "kurta",

        # Bottoms
        "pants", "jeans", "trousers", "shorts", "skirt", "leggings", "joggers",

        # One-piece and traditional wear
        "dress", "gown", "jumpsuit", "saree", "lehenga", "salwar kameez",

        # Footwear
        "shoes", "sneakers", "boots", "sandals", "heels", "slippers", "loafers",

        # Accessories
        "hat", "cap", "scarf", "belt", "tie", "sunglasses", "watch", "handbag", "backpack", "wallet",
        "necklace", "earrings", "bracelet", "ring",

        # Style categories
        "formal wear", "casual wear", "sportswear", "ethnic wear", "streetwear",
    ],
    "food": [
        # Generic food classes
        "food", "meal", "dish", "cuisine", "snack", "food ingredients",

        # Staple categories
        "rice dish", "noodle dish", "pasta", "bread", "sandwich", "burger", "pizza",

        # Protein and mains
        "chicken dish", "fish dish", "seafood", "egg dish", "meat dish", "vegetarian dish", "vegan dish",

        # Fruits and vegetables
        "fruit", "mixed fruit", "citrus fruit", "berries", "vegetable dish", "salad",

        # Regional/common foods
        "curry", "soup", "stew", "dumplings", "biryani", "fried rice", "noodles",
        "idli", "dosa", "chapati", "paratha",

        # Fast food and street food
        "fast food", "street food", "fried food", "grilled food", "barbecue",

        # Dessert and bakery
        "dessert", "cake", "pastry", "ice cream", "cookies", "chocolate", "sweet dish",

        # Drinks
        "beverage", "juice", "tea", "coffee", "smoothie", "milkshake",

        # Serving context
        "plated food", "buffet food", "home cooked meal",
    ],
}

# Global CLIP prompt templates used for every label.
BASE_PROMPT_TEMPLATES: List[str] = [
    "a high resolution photo of {label}",
    "a clear photo of {label}",
    "a detailed image of {label}",
    "a centered photo of {label}",
    "a close-up photo of {label}",
]

# Domain-level prompt enrichments appended for labels in the corresponding domain.
DOMAIN_PROMPT_TEMPLATES: Dict[str, List[str]] = {
    "vegetable": [
        "a fresh organic {label}",
        "raw {label} used for cooking",
        "a {label} from a grocery market",
        "a fresh farm {label}",
        "a {label} on display in supermarket",
        "a {label} on retail shelves",
        "organized fresh {label}",
        "a {label} in a produce section",
    ],
    "food": [
        "fresh {label} used for cooking",
        "a food ingredient {label}",
        "a plated {label} dish",
        "a close-up photo of {label} on a plate",
        "a high resolution food photo of {label}",
        "a cooked {label} meal",
    ],
    "satellite image": [
        "a satellite top view of {label}",
        "aerial imagery showing {label}",
        "remote sensing image of {label}",
        "high resolution satellite photo of {label}",
        "earth observation image containing {label}",
    ],
    "vehicle": [
        "a high resolution photo of a {label} on the road",
        "a clear image of a {label} vehicle",
        "a centered photo of {label} transportation",
        "a close-up photo of a {label}",
        "an outdoor traffic scene with a {label}",
    ],
    "fashion item": [
        "a fashion catalog photo of {label}",
        "a close-up product photo of {label}",
        "a studio image of {label} apparel",
        "a person wearing {label}",
        "a detailed photo of {label} clothing",
    ],
    "animal": [
        "a wildlife photo of {label}",
        "a close-up of a {label} animal",
        "a clear image of a {label} in nature",
    ],
    "industrial": [
        "an industrial inspection image of {label}",
        "a detailed close-up of {label}",
        "a macro photograph of {label}",
        "a high resolution image of {label}",
        "industrial documentation of {label}",
        "a close-up metal surface image showing {label}",
        "a magnified view of {label}",
        "structural engineering image of {label}",
        "quality control image of {label}",
    ],
    "medical": [
        "a clinical image showing {label}",
        "a diagnostic scan of {label}",
        "a medical radiology image indicating {label}",
        "a medical retinal fundus photograph showing {label}",
        "an ophthalmology image highlighting {label}",
    ],
}

# Keyword-based prompt enrichments for specialized label categories
KEYWORD_LABEL_PROMPTS: Dict[str, Dict[str, List[str]]] = {
    "industrial": {
        "weld crack": [
            "industrial metal weld crack defect on steel surface",
            "fractured steel weld joint with corrosion",
            "metal fatigue crack near weld seam",
            "damaged welded metal surface with fracture",
            "steel weld bead crack with rust and oxidation",
            "structural metal fracture in welded joint",
            "cracked weld defect on industrial metal plate",
            "welded steel surface showing fatigue failure",
            "metal crack propagating from weld seam",
            "corroded fractured weld joint on steel plate",
        ],
        "fracture": [
            "metal surface fracture and crack",
            "fractured steel plate with visible damage",
            "structural crack in metal material",
            "stress fracture on metal surface",
            "propagating fracture in steel material",
        ],
        "corrosion": [
            "corroded metal surface with rust",
            "oxidized steel surface showing rust damage",
            "corrosion and degradation on metal plate",
            "rust stains on industrial metal surface",
            "oxidation damage on metal material",
        ],
    },
}

# Exact-label prompt overrides for key labels.
EXACT_LABEL_PROMPTS: Dict[str, Dict[str, List[str]]] = {
    "vegetable": {
        "cauliflower": [
            "a high resolution photo of a cauliflower vegetable",
            "a close-up photo of fresh cauliflower heads",
            "a bunch of white cauliflower vegetables on a wooden table",
            "raw cauliflower vegetable used for cooking",
            "a fresh organic cauliflower with green leaves",
            "a fresh white cauliflower vegetable",
            "a cauliflower head with green leaves",
        ],
        "broccoli": [
            "a photo of broccoli",
            "green broccoli vegetable",
            "fresh broccoli florets",
        ],
        "vegetable": [
            "a photo of a vegetable",
            "a close-up photo of fresh vegetables",
            "a vegetable placed on a table",
            "a fresh organic vegetable",
            "a food ingredient vegetable",
        ],
    },
    "food": {
        "pizza": [
            "a top-down photo of a whole pizza",
            "a close-up image of pizza slices with melted cheese",
            "a baked pizza served on a plate",
        ],
        "burger": [
            "a close-up photo of a burger with bun and patty",
            "a fast food burger served on a tray",
            "a detailed image of a hamburger with toppings",
        ],
        "biryani": [
            "a bowl of biryani rice with spices",
            "a traditional biryani dish served hot",
            "a close-up photo of layered biryani",
        ],
        "salad": [
            "a fresh salad bowl with vegetables",
            "a healthy green salad on a plate",
            "a close-up image of mixed salad ingredients",
        ],
    },
    "vehicle": {
        "airplane": [
            "a passenger airplane on an airport runway",
            "a commercial airplane in flight",
            "a clear side view of an airplane",
        ],
        "bus": [
            "a city bus on an urban street",
            "a public transport bus at a bus stop",
            "a clear image of a large passenger bus",
        ],
        "train": [
            "a train on railway tracks",
            "a locomotive at a railway station",
            "a side view of a passenger train",
        ],
        "motorcycle": [
            "a parked motorcycle on a road",
            "a close-up photo of a motorcycle bike",
            "a two-wheeler motorcycle in traffic",
        ],
    },
    "satellite image": {
        "urban area": [
            "a satellite image of dense urban buildings",
            "an aerial view of a city block pattern",
            "a top view of urban infrastructure and roads",
        ],
        "forest": [
            "a satellite view of dense green forest cover",
            "an aerial image showing woodland vegetation",
            "a top view of continuous forest canopy",
        ],
        "river": [
            "a satellite image of a winding river channel",
            "an aerial top view of river and nearby land",
            "a remote sensing image of river water flow",
        ],
        "runway": [
            "a satellite top view of an airport runway",
            "an aerial image showing long runway strips",
            "a remote sensing photo of airport infrastructure",
        ],
    },
    "fashion item": {
        "dress": [
            "a fashion studio photo of a dress",
            "a full-length dress worn by a model",
            "a detailed apparel image of a dress",
        ],
        "sneakers": [
            "a product photo of casual sneakers",
            "a close-up shot of sneaker shoes",
            "a pair of sneakers on a plain background",
        ],
        "jacket": [
            "a catalog photo of a jacket",
            "a person wearing a stylish jacket",
            "a close-up of jacket fabric and zipper",
        ],
        "handbag": [
            "a product image of a leather handbag",
            "a fashion accessory photo of a handbag",
            "a close-up of a women's handbag",
        ],
    },
    "medical": {
        "diabetic retinopathy": [
            "retinal fundus image showing diabetic retinopathy",
            "medical retinal scan with diabetic retinopathy lesions",
            "fundus photograph with hemorrhages and microaneurysms typical of diabetic retinopathy",
            "ophthalmology image showing diabetic eye disease",
            "retinal photograph showing yellow exudates and diabetic retinopathy",
        ],
        "proliferative diabetic retinopathy": [
            "retinal fundus photograph showing proliferative diabetic retinopathy",
            "ophthalmology image with neovascularization from proliferative diabetic retinopathy",
            "fundus scan with severe diabetic retinal vascular changes",
            "retinal image showing advanced diabetic retinopathy with hemorrhages",
            "clinical fundus photo showing proliferative diabetic retinal disease",
        ],
        "non-proliferative diabetic retinopathy": [
            "retinal fundus image showing non-proliferative diabetic retinopathy",
            "fundus photograph with microaneurysms and hard exudates",
            "ophthalmology retinal scan showing early diabetic retinopathy",
            "medical retinal image of non-proliferative diabetic eye disease",
            "diabetic fundus image without neovascular proliferation",
        ],
        "age-related macular degeneration": [
            "a retinal fundus photograph showing age-related macular degeneration with drusen deposits",
            "ophthalmology image of macular degeneration with drusen",
            "retinal scan showing age-related degeneration in the macula",
            "clinical fundus photo with age-related macular disease",
            "medical retinal image indicating age-related macular degeneration",
        ],
        "central retinal artery occlusion": [
            "a retinal fundus photograph showing central retinal artery occlusion with pale retina",
            "ophthalmology image showing retinal whitening due to arterial occlusion",
            "fundus photograph with central retinal artery blockage signs",
            "retinal image with ischemic pale retina and arterial occlusion",
            "clinical retinal scan indicating central retinal artery occlusion",
        ],
        "normal fundus": [
            "a normal retinal fundus photograph of a healthy human eye",
            "ophthalmology image showing a healthy retina and optic disc",
            "medical retinal scan without pathological findings",
            "clear fundus photograph of normal retinal anatomy",
            "normal retina with no hemorrhages exudates or drusen",
        ],
    },
}

# Keyword-driven prompt enrichments applied when keyword is present in label text.
KEYWORD_LABEL_PROMPTS: Dict[str, Dict[str, List[str]]] = {
    "food": {
        "cake": [
            "a decorated cake on a dessert table",
            "a close-up of cake layers and frosting",
        ],
        "ice cream": [
            "a scoop of ice cream in a bowl",
            "a close-up frozen dessert photo",
        ],
    },
    "vehicle": {
        "truck": [
            "a heavy truck driving on a highway",
            "a large cargo truck viewed from the side",
        ],
        "ship": [
            "a cargo ship on open water",
            "a large vessel at a harbor port",
        ],
    },
    "satellite image": {
        "flood": [
            "a satellite image of flooded terrain",
            "an aerial view of water inundation over land",
        ],
        "road": [
            "a satellite top view showing road networks",
            "an aerial image with connected highway lines",
        ],
    },
    "fashion item": {
        "shoe": [
            "a close-up product photo of footwear",
            "a pair of shoes on display",
        ],
        "watch": [
            "a close-up image of a wrist watch accessory",
            "a product photo of a fashion watch",
        ],
    },
    "medical": {
        "retina": [
            "retinal fundus image showing optic disc and macula",
            "ophthalmology fundus photograph of retinal structures",
        ],
        "diabetic": [
            "retinal image showing diabetic microaneurysms and hemorrhages",
            "medical retinal scan with diabetic hard exudates",
        ],
        "macular": [
            "fundus photo showing macular pathology",
            "retinal scan focused on macular region abnormalities",
        ],
        "occlusion": [
            "retinal image with vascular occlusion patterns",
            "fundus scan showing retinal ischemic whitening",
        ],
    },
}

# Thresholds
MEDICAL_THRESHOLD = 0.08
TRAFFIC_THRESHOLD = 0.35
