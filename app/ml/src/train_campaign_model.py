"""
Train Campaign Recommendation Model
====================================
Train and save the campaign recommender model from historical data.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import argparse
from datetime import datetime
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.campaign_analyzer import CampaignAnalyzer
from src.campaign_recommender import CampaignRecommender


def load_training_data(data_dir: str = "data/training"):
    """
    Load training data from CSV files.
    
    Expected files:
    - orders.csv: Historical orders
    - campaigns.csv: Past campaigns
    - order_items.csv: Order-item relationships
    """
    
    data_path = Path(data_dir)
    
    print(f"Loading training data from {data_path}...")
    
    # Load orders
    orders_file = data_path / "orders.csv"
    if orders_file.exists():
        orders_df = pd.read_csv(orders_file)
        print(f"  ✓ Loaded {len(orders_df)} orders")
    else:
        print(f"  ✗ Orders file not found: {orders_file}")
        orders_df = pd.DataFrame()
    
    # Load campaigns
    campaigns_file = data_path / "campaigns.csv"
    if campaigns_file.exists():
        campaigns_df = pd.read_csv(campaigns_file)
        
        # Convert to list of dicts
        campaigns_data = []
        for _, row in campaigns_df.iterrows():
            # Parse items_included (it's stored as string representation of list)
            items = row['items_included']
            if isinstance(items, str):
                # Remove brackets and quotes, split by comma
                items = items.strip("[]'\"").replace("'", "").replace('"', '').split(', ')
            
            campaigns_data.append({
                'id': row.get('id', f"campaign_{_}"),
                'start_time': row['start_time'],
                'end_time': row['end_time'],
                'items_included': items,
                'discount': float(row['discount'])
            })
        
        print(f"  ✓ Loaded {len(campaigns_data)} campaigns")
    else:
        print(f"  ✗ Campaigns file not found: {campaigns_file}")
        campaigns_data = []
    
    # Load order items
    order_items_file = data_path / "order_items.csv"
    if order_items_file.exists():
        order_items_df = pd.read_csv(order_items_file)
        print(f"  ✓ Loaded {len(order_items_df)} order-item relationships")
    else:
        print(f"  ✗ Order items file not found: {order_items_file}")
        order_items_df = pd.DataFrame()
    
    return orders_df, campaigns_data, order_items_df


def train_model(
    orders_df: pd.DataFrame,
    campaigns_data: list,
    order_items_df: pd.DataFrame,
    use_xgboost: bool = True
):
    """Train the campaign recommender model"""
    
    print("\n" + "="*80)
    print("TRAINING CAMPAIGN RECOMMENDATION MODEL")
    print("="*80)
    
    # Initialize analyzer
    print("\n1. Initializing Campaign Analyzer...")
    analyzer = CampaignAnalyzer()
    
    # Analyze campaigns
    if len(campaigns_data) > 0:
        print(f"\n2. Analyzing {len(campaigns_data)} historical campaigns...")
        campaign_metrics = analyzer.analyze_campaign_effectiveness(
            orders_df,
            campaigns_data,
            order_items_df
        )
        
        print(f"   ✓ Analyzed campaigns:")
        for metric in campaign_metrics[:5]:  # Show first 5
            print(f"     - {metric.campaign_id}: ROI={metric.roi:.1f}%, Uplift={metric.uplift_percentage:.1f}%")
        
        if len(campaign_metrics) > 5:
            print(f"     ... and {len(campaign_metrics) - 5} more")
    else:
        print("\n2. No campaigns to analyze")
        return None
    
    # Extract patterns
    print("\n3. Extracting patterns...")
    
    print("   a. Temporal patterns...")
    patterns = analyzer.extract_temporal_patterns(orders_df)
    print(f"      ✓ Extracted patterns for {len(patterns['by_day_of_week'])} days, "
          f"{len(patterns['by_hour'])} hours, {len(patterns['by_season'])} seasons")
    
    if len(order_items_df) > 10:
        print("   b. Item affinity...")
        affinity = analyzer.extract_item_affinity(order_items_df, min_support=0.01)
        print(f"      ✓ Found {len(affinity)} item pairs with high affinity")
        
        # Show top 3 pairs
        if affinity:
            top_pairs = sorted(affinity.items(), key=lambda x: x[1], reverse=True)[:3]
            for (item1, item2), score in top_pairs:
                print(f"         - {item1} + {item2}: {score:.2f}")
    else:
        print("   b. Skipping item affinity (insufficient data)")
    
    # Get summary statistics
    summary = analyzer.get_summary_statistics()
    if summary:
        print(f"\n4. Campaign Analysis Summary:")
        print(f"   • Total campaigns: {summary['total_campaigns_analyzed']}")
        print(f"   • Average uplift: {summary['avg_uplift']:.1f}%")
        print(f"   • Average ROI: {summary['avg_roi']:.1f}%")
        print(f"   • Success rate: {summary['success_rate']:.1f}%")
    
    # Initialize recommender
    print("\n5. Initializing Campaign Recommender...")
    recommender = CampaignRecommender(
        analyzer=analyzer,
        exploration_rate=0.15,
        min_samples_for_prediction=max(3, len(campaigns_data) // 2)
    )
    
    # Train model
    if len(campaigns_data) >= 3:
        print(f"\n6. Training ML model (XGBoost={use_xgboost})...")
        recommender.fit(use_xgboost=use_xgboost)
        print("   ✓ Model trained successfully")
        
        if recommender.feature_importance:
            print("\n   Top 5 important features:")
            top_features = sorted(
                recommender.feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            for feature, importance in top_features:
                print(f"     - {feature}: {importance:.4f}")
    else:
        print(f"\n6. Skipping ML training (only {len(campaigns_data)} campaigns, need ≥3)")
    
    return recommender


def save_model_and_metadata(
    recommender: CampaignRecommender,
    orders_df: pd.DataFrame,
    campaigns_data: list,
    order_items_df: pd.DataFrame,
    output_dir: str = "data/models",
    use_xgboost: bool = True
):
    """Save model and metadata"""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    model_file = output_path / "campaign_recommender.json"
    
    print(f"\n7. Saving model to {model_file}...")
    recommender.save_model(str(model_file))
    
    # Save metadata
    metadata = {
        "trained_at": datetime.now().isoformat(),
        "training_data": {
            "num_orders": len(orders_df),
            "num_campaigns": len(campaigns_data),
            "num_order_items": len(order_items_df),
            "date_range": {
                "start": datetime.fromtimestamp(orders_df['created'].min()).isoformat() if not orders_df.empty else None,
                "end": datetime.fromtimestamp(orders_df['created'].max()).isoformat() if not orders_df.empty else None
            }
        },
        "model_config": {
            "exploration_rate": recommender.exploration_rate,
            "min_samples_for_prediction": recommender.min_samples_for_prediction,
            "use_xgboost": use_xgboost
        },
        "performance": recommender.analyzer.get_summary_statistics(),
        "templates": len(recommender.campaign_templates),
        "item_affinities": len(recommender.analyzer.item_affinity)
    }
    
    metadata_file = output_path / "campaign_recommender_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2, default=str)
    
    print(f"   ✓ Saved metadata to {metadata_file}")
    
    return metadata


def main():
    """Main training function"""
    
    parser = argparse.ArgumentParser(description="Train campaign recommendation model")
    parser.add_argument(
        "--data-dir",
        default="data/training",
        help="Directory containing training data (default: data/training)"
    )
    parser.add_argument(
        "--output-dir",
        default="data/models",
        help="Directory to save trained model (default: data/models)"
    )
    parser.add_argument(
        "--no-xgboost",
        action="store_true",
        help="Use simple model instead of XGBoost"
    )
    
    args = parser.parse_args()
    
    # Check if data exists
    data_path = Path(args.data_dir)
    if not data_path.exists():
        print(f"\n❌ ERROR: Data directory not found: {data_path}")
        print(f"\nPlease generate training data first:")
        print(f"  python generate_campaign_test_data.py")
        return
    
    # Load data
    orders_df, campaigns_data, order_items_df = load_training_data(args.data_dir)
    
    if orders_df.empty or len(campaigns_data) == 0:
        print("\n❌ ERROR: No training data found!")
        print(f"\nPlease generate training data first:")
        print(f"  python generate_campaign_test_data.py")
        return
    
    # Train model
    recommender = train_model(
        orders_df,
        campaigns_data,
        order_items_df,
        use_xgboost=not args.no_xgboost
    )
    
    if recommender is None:
        print("\n❌ Training failed!")
        return
    
    # Save model and metadata
    metadata = save_model_and_metadata(
        recommender,
        orders_df,
        campaigns_data,
        order_items_df,
        args.output_dir,
        use_xgboost=not args.no_xgboost
    )
    
    print("\n" + "="*80)
    print("✅ MODEL TRAINING COMPLETE!")
    print("="*80)
    print(f"\nModel saved to: {Path(args.output_dir) / 'campaign_recommender.json'}")
    print(f"\nTraining Statistics:")
    print(f"  • Orders: {metadata['training_data']['num_orders']:,}")
    print(f"  • Campaigns: {metadata['training_data']['num_campaigns']}")
    print(f"  • Templates: {metadata['templates']}")
    print(f"  • Item Affinities: {metadata['item_affinities']}")
    
    if metadata['performance']:
        perf = metadata['performance']
        print(f"\nModel Performance:")
        print(f"  • Average ROI: {perf['avg_roi']:.1f}%")
        print(f"  • Success Rate: {perf['success_rate']:.1f}%")
    
    print(f"\nTo use this model:")
    print(f"  1. Start the API: uvicorn api.main:app --reload")
    print(f"  2. Test: python test_campaign_api.py")
    print(f"\nTo view metadata:")
    print(f"  cat {Path(args.output_dir) / 'campaign_recommender_metadata.json'}")


if __name__ == "__main__":
    main()