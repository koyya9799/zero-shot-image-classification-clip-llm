# backend/models/medclip_model.py
import torch
import numpy as np
from PIL import Image
from typing import List, Tuple
from .model_cache import ModelLoader, DEVICE

class MedCLIPModel:
    def __init__(self):
        self.device = DEVICE
        self._loaded = False
        self._cache_data = None
    
    def _ensure_loaded(self):
        if self._loaded and self._cache_data:
            return
        self._cache_data = ModelLoader.load_medclip_fast()
        self._loaded = True
            
    @property
    def model(self):
        self._ensure_loaded()
        return self._cache_data["model"]
    
    @property
    def processor(self):
        self._ensure_loaded()
        return self._cache_data.get("processor")
    
    def encode_image(self, image: Image.Image) -> np.ndarray:
        self._ensure_loaded()
        with torch.no_grad():
            if self.processor:
                inputs = self.processor(images=image, return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                image_features = self.model.encode_image(**inputs)
            else:
                image_input = self._cache_data["preprocess"](image).unsqueeze(0).to(self.device)
                image_features = self.model.encode_image(image_input)
            image_features /= image_features.norm(dim=-1, keepdim=True)
        return image_features.cpu().numpy()[0]
    
    def encode_text(self, texts: List[str]) -> np.ndarray:
        self._ensure_loaded()
        medical_prompts = [f"a medical x-ray showing {text}" if not any(k in text.lower() for k in ["xray","ct","mri","scan","medical"]) else text for text in texts]
        with torch.no_grad():
            if self.processor:
                inputs = self.processor(text=medical_prompts, return_tensors="pt", padding=True)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                text_features = self.model.encode_text(**inputs)
            else:
                text_tokens = self._cache_data["tokenizer"](medical_prompts).to(self.device)
                text_features = self.model.encode_text(text_tokens)
            text_features /= text_features.norm(dim=-1, keepdim=True)
        return text_features.cpu().numpy()

    def compute_similarity(self, image_emb: np.ndarray, text_embs: np.ndarray) -> np.ndarray:
        return text_embs @ image_emb
        
    def get_prompt_ensembles(self, label: str) -> List[str]:
        # Enhanced prompts for better medical diagnosis accuracy
        label_lower = label.lower()
        
        # Eye-specific conditions get specialized prompts
        if any(term in label_lower for term in ['glaucoma']):
            return [
                f"fundus image showing glaucoma",
                f"optic disc with glaucomatous cupping",
                f"ophthalmology image of glaucoma",
                f"retinal image indicating glaucoma",
                f"glaucoma with increased intraocular pressure",
                f"optic nerve head changes in glaucoma"
            ]
        elif any(term in label_lower for term in ['diabetic retinopathy', 'retinopathy', 'macular edema']):
            return [
                f"fundus image showing diabetic retinopathy",
                f"diabetic eye damage with retinopathy",
                f"ophthalmology image of diabetic retinopathy",
                f"diabetic microaneurysms and hemorrhages",
                f"retinal damage from diabetes",
                f"cotton wool spots and hard exudates"
            ]
        elif any(term in label_lower for term in ['macular degeneration', 'amd', 'age-related']):
            return [
                f"fundus image with age-related macular degeneration",
                f"retinal image showing macular changes",
                f"drusen deposits in macula",
                f"macular atrophy image"
            ]
        elif any(term in label_lower for term in ['cataract', 'lens']):
            return [
                f"anterior segment image showing cataract",
                f"slit lamp photograph of cataract",
                f"lens opacity image",
                f"cataract formation"
            ]
        elif any(term in label_lower for term in ['retinal detachment', 'detached retina']):
            return [
                f"fundus image showing retinal detachment",
                f"retina detached from epithelium",
                f"separated retinal tissue",
                f"retinal break and detachment"
            ]
        # Brain-specific conditions
        elif any(term in label_lower for term in ['alzheimer', 'dementia', 'brain atrophy']):
            return [
                f"brain MRI showing {label}",
                f"neurological scan indicating {label}",
                f"brain imaging of {label}",
                f"MRI demonstrating {label}",
                f"diagnostic brain scan with {label}",
                f"radiological evidence of {label}"
            ]
        elif any(term in label_lower for term in ['parkinson', 'movement disorder']):
            return [
                f"brain imaging showing Parkinson's disease",
                f"MRI indicating movement disorder",
                f"neurological imaging of Parkinson's",
                f"substantia nigra changes"
            ]
        elif any(term in label_lower for term in ['stroke', 'infarct', 'ischemic']):
            return [
                f"brain CT showing stroke",
                f"MRI revealing acute infarction",
                f"ischemic brain lesion",
                f"cerebral infarct imaging"
            ]
        elif any(term in label_lower for term in ['glioma', 'tumor', 'mass', 'lesion', 'cancer']):
            return [
                f"brain scan showing {label}",
                f"MRI revealing {label}",
                f"neuroimaging of {label}",
                f"clinical brain scan with {label}",
                f"radiological finding of {label}"
            ]
        # Chest/Pulmonary conditions
        elif any(term in label_lower for term in ['pneumonia', 'tuberculosis', 'covid', 'lung']):
            return [
                f"chest x-ray showing {label}",
                f"pulmonary imaging of {label}",
                f"lung infiltrate indicating {label}",
                f"thoracic radiograph with {label}",
                f"respiratory infection image"
            ]
        # Bone/Orthopedic conditions
        elif any(term in label_lower for term in ['fracture', 'break', 'bone', 'osteoarthritis', 'arthritis']):
            return [
                f"x-ray showing {label}",
                f"radiographic image of {label}",
                f"orthopedic imaging of {label}",
                f"skeletal radiograph with {label}"
            ]
        else:
            return [
                f"a medical image of {label}",
                f"a clinical radiograph showing {label}",
                f"a diagnostic scan of {label}",
                f"a radiology scan indicating {label}",
                f"a hospital imaging showing {label}",
                f"clinical evidence of {label}"
            ]

    def classify(self, image: Image.Image, labels: List[str], top_k: int = 5, custom_ensembles: dict = None) -> Tuple[List[dict], np.ndarray]:
        image_emb = self.encode_image(image)
        
        text_embs = []
        for label in labels:
            if custom_ensembles and label in custom_ensembles:
                prompts = custom_ensembles[label]
            else:
                prompts = self.get_prompt_ensembles(label)
                
            encoded = self.encode_text(prompts)
            avg_emb = np.mean(encoded, axis=0)
            avg_emb /= np.linalg.norm(avg_emb)
            text_embs.append(avg_emb)
            
        text_embs = np.array(text_embs)
        
        similarities = self.compute_similarity(image_emb, text_embs)
        
        # Temperature Scaling
        logits = similarities / 0.03
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / np.sum(exp_logits)
        
        top_indices = np.argsort(-probs)[:top_k]
        predictions = [{"label": labels[idx], "score": float(probs[idx])} for idx in top_indices]
        return predictions, image_emb

_medclip_model = None
def get_medclip_model() -> MedCLIPModel:
    global _medclip_model
    if _medclip_model is None:
        _medclip_model = MedCLIPModel()
    return _medclip_model
