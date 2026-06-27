# app/evaluation_service.py
"""
Evaluation service for computing comprehensive metrics on test datasets.
Supports accuracy, precision, recall, F1, mAP, calibration error, and cross-domain robustness.
"""

import numpy as np
from typing import List, Dict, Tuple
from collections import defaultdict
from PIL import Image
import io

from .clip_service import classify_image


def calculate_metrics(predictions: List[Dict], ground_truths: List[str]) -> Dict:
    """
    Calculate comprehensive evaluation metrics.
    
    Args:
        predictions: List of classification results with 'candidates' (top-k predictions with confidences)
        ground_truths: List of true labels for each sample
        
    Returns:
        Dictionary with all computed metrics
    """
    if len(predictions) != len(ground_truths):
        raise ValueError(f"Mismatch: {len(predictions)} predictions vs {len(ground_truths)} ground truths")
    
    num_samples = len(ground_truths)
    
    # Collect all unique classes
    all_classes = set(ground_truths)
    for pred in predictions:
        for candidate in pred['candidates']:
            all_classes.add(candidate['label'])
    
    all_classes = sorted(list(all_classes))
    num_classes = len(all_classes)
    class_to_idx = {cls: idx for idx, cls in enumerate(all_classes)}
    
    # Initialize counters
    top1_correct = 0
    top5_correct = 0
    
    # Per-class metrics
    tp = defaultdict(int)  # true positives
    fp = defaultdict(int)  # false positives
    fn = defaultdict(int)  # false negatives
    class_samples = defaultdict(int)  # samples per class
    
    # For mAP calculation
    average_precisions = []
    
    # For calibration error
    confidence_bins = [[] for _ in range(10)]  # 10 bins
    
    # Domain tracking
    domain_performance = defaultdict(lambda: {'correct': 0, 'total': 0})
    
    # Process each prediction
    for pred, gt in zip(predictions, ground_truths):
        candidates = pred['candidates']
        domain = pred.get('domain', 'unknown')
        
        if not candidates:
            fn[gt] += 1
            class_samples[gt] += 1
            domain_performance[domain]['total'] += 1
            continue
        
        # Top-1 prediction
        top1_label = candidates[0]['label']
        top1_conf = candidates[0]['confidence']
        
        # Top-1 accuracy
        if top1_label == gt:
            top1_correct += 1
            tp[gt] += 1
            domain_performance[domain]['correct'] += 1
        else:
            fp[top1_label] += 1
            fn[gt] += 1
        
        domain_performance[domain]['total'] += 1
        class_samples[gt] += 1
        
        # Top-5 accuracy
        top5_labels = [c['label'] for c in candidates[:5]]
        if gt in top5_labels:
            top5_correct += 1
        
        # Calibration error (binning confidences)
        bin_idx = min(int(top1_conf * 10), 9)
        confidence_bins[bin_idx].append(1 if top1_label == gt else 0)
        
        # Average Precision for this sample
        precisions = []
        correct_count = 0
        for k, candidate in enumerate(candidates, 1):
            if candidate['label'] == gt:
                correct_count += 1
                precisions.append(correct_count / k)
        
        if precisions:
            average_precisions.append(np.mean(precisions))
        else:
            average_precisions.append(0.0)
    
    # Calculate top-k accuracies
    top1_accuracy = top1_correct / num_samples if num_samples > 0 else 0.0
    top5_accuracy = top5_correct / num_samples if num_samples > 0 else 0.0
    
    # Calculate per-class precision, recall, F1
    precisions = []
    recalls = []
    f1_scores = []
    class_weights = []
    
    for cls in all_classes:
        tp_c = tp[cls]
        fp_c = fp[cls]
        fn_c = fn[cls]
        samples = class_samples[cls]
        
        precision = tp_c / (tp_c + fp_c) if (tp_c + fp_c) > 0 else 0.0
        recall = tp_c / (tp_c + fn_c) if (tp_c + fn_c) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        precisions.append(precision)
        recalls.append(recall)
        f1_scores.append(f1)
        class_weights.append(samples)
    
    # Weighted averages (by class frequency)
    total_weight = sum(class_weights) if class_weights else 1
    weights_normalized = [w / total_weight for w in class_weights]
    
    precision_weighted = sum(p * w for p, w in zip(precisions, weights_normalized))
    recall_weighted = sum(r * w for r, w in zip(recalls, weights_normalized))
    f1_weighted = sum(f * w for f, w in zip(f1_scores, weights_normalized))
    
    # Macro averages (unweighted)
    precision_macro = np.mean(precisions) if precisions else 0.0
    recall_macro = np.mean(recalls) if recalls else 0.0
    f1_macro = np.mean(f1_scores) if f1_scores else 0.0
    
    # Mean Average Precision (mAP)
    map_score = np.mean(average_precisions) if average_precisions else 0.0
    
    # Expected Calibration Error (ECE)
    ece = 0.0
    for bin_idx, bin_accuracies in enumerate(confidence_bins):
        if bin_accuracies:
            bin_conf = (bin_idx + 0.5) / 10  # midpoint of bin
            bin_acc = np.mean(bin_accuracies)
            bin_weight = len(bin_accuracies) / num_samples
            ece += bin_weight * abs(bin_conf - bin_acc)
    
    # Cross-domain performance drop
    domain_accuracies = {}
    for domain, stats in domain_performance.items():
        if stats['total'] > 0:
            domain_accuracies[domain] = stats['correct'] / stats['total']
    
    if len(domain_accuracies) > 1:
        max_acc = max(domain_accuracies.values())
        min_acc = min(domain_accuracies.values())
        cross_domain_drop = max_acc - min_acc
    else:
        cross_domain_drop = 0.0
    
    return {
        'top1_accuracy': float(top1_accuracy),
        'top5_accuracy': float(top5_accuracy),
        'precision_weighted': float(precision_weighted),
        'recall_weighted': float(recall_weighted),
        'f1_weighted': float(f1_weighted),
        'precision_macro': float(precision_macro),
        'recall_macro': float(recall_macro),
        'f1_macro': float(f1_macro),
        'map': float(map_score),
        'cross_domain_drop': float(cross_domain_drop),
        'ece': float(ece),
        'num_samples': num_samples,
        'num_classes': num_classes,
        'per_class_metrics': {
            cls: {
                'precision': float(precisions[i]),
                'recall': float(recalls[i]),
                'f1': float(f1_scores[i]),
                'samples': int(class_weights[i])
            }
            for i, cls in enumerate(all_classes)
        },
        'domain_performance': {
            domain: {
                'accuracy': float(stats['correct'] / stats['total']) if stats['total'] > 0 else 0.0,
                'samples': stats['total']
            }
            for domain, stats in domain_performance.items()
        }
    }


async def evaluate_dataset(files: List[Tuple[bytes, str]], labels: List[str]) -> Dict:
    """
    Evaluate model on a dataset of images with ground truth labels.
    
    Args:
        files: List of (image_bytes, filename) tuples
        labels: List of ground truth labels corresponding to each file
        
    Returns:
        Evaluation metrics dictionary
    """
    if len(files) != len(labels):
        raise ValueError(f"Number of files ({len(files)}) must match number of labels ({len(labels)})")
    
    predictions = []
    ground_truths = []
    
    # Classify each image
    for (img_bytes, _), label in zip(files, labels):
        try:
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            result = classify_image(img, top_k=5)
            
            # Add domain to prediction
            prediction = {
                'candidates': result['candidates'],
                'confidence': result['confidence'],
                'domain': result.get('domain', 'unknown')
            }
            
            predictions.append(prediction)
            ground_truths.append(label.strip().lower())
            
        except Exception as e:
            print(f"Error processing image: {e}")
            # Add empty prediction for failed images
            predictions.append({
                'candidates': [],
                'confidence': 0.0,
                'domain': 'unknown'
            })
            ground_truths.append(label.strip().lower())
    
    # Calculate metrics
    metrics = calculate_metrics(predictions, ground_truths)
    
    return metrics
