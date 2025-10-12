"""
File loader with automatic type detection
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Literal
import pandas as pd


FileType = Literal["historical", "experiment_results", "enrichment", "unknown"]


class DataLoader:
    """Load and analyze uploaded files"""

    @staticmethod
    def load_file(file_path: str) -> pd.DataFrame:
        """
        Load a file (CSV or JSON) into a DataFrame

        Args:
            file_path: Path to the file

        Returns:
            DataFrame with file contents

        Raises:
            ValueError: If file format is not supported
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = path.suffix.lower()

        if suffix == ".csv":
            return pd.read_csv(file_path)
        elif suffix == ".json":
            with open(file_path, "r") as f:
                data = json.load(f)

            # Handle both list of objects and single object
            if isinstance(data, list):
                return pd.DataFrame(data)
            elif isinstance(data, dict):
                # If single object, wrap in list
                return pd.DataFrame([data])
            else:
                raise ValueError(f"Unsupported JSON structure in {file_path}")
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    @staticmethod
    def detect_file_type(df: pd.DataFrame) -> FileType:
        """
        Detect file type based on columns

        Args:
            df: DataFrame to analyze

        Returns:
            File type classification
        """
        columns = set(col.lower() for col in df.columns)

        # Check for experiment results indicators
        experiment_indicators = {"experiment_id", "variant", "variation", "test_group", "control"}
        if experiment_indicators.intersection(columns):
            return "experiment_results"

        # Check for historical campaign data
        campaign_indicators = {
            "campaign_name", "campaign_id", "spend", "conversions",
            "impressions", "clicks", "ctr", "cpa", "roas"
        }
        if len(campaign_indicators.intersection(columns)) >= 3:
            return "historical"

        # Check for enrichment data (competitor, market, etc.)
        enrichment_indicators = {
            "competitor", "market", "benchmark", "industry", "category"
        }
        if enrichment_indicators.intersection(columns):
            return "enrichment"

        return "unknown"

    @staticmethod
    def analyze_file(file_path: str) -> Dict[str, Any]:
        """
        Load and analyze a file

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with file analysis
        """
        df = DataLoader.load_file(file_path)
        file_type = DataLoader.detect_file_type(df)

        # Get basic stats
        analysis = {
            "file_path": file_path,
            "file_name": Path(file_path).name,
            "type": file_type,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "data": df.to_dict(orient="records"),  # Full data for processing
            "sample": df.head(3).to_dict(orient="records"),  # First 3 rows for display
        }

        # Add type-specific analysis
        if file_type == "historical":
            analysis["metrics"] = DataLoader._analyze_historical(df)
        elif file_type == "experiment_results":
            analysis["metrics"] = DataLoader._analyze_experiments(df)

        return analysis

    @staticmethod
    def _analyze_historical(df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze historical campaign data"""
        metrics = {}

        # Calculate aggregates if numeric columns exist
        numeric_cols = df.select_dtypes(include=["number"]).columns

        for col in numeric_cols:
            col_lower = col.lower()
            if col_lower in ["spend", "cost", "budget"]:
                total_spend = df[col].sum()
                avg_spend = df[col].mean()
                # Convert NaN to None for JSON serialization
                metrics["total_spend"] = None if pd.isna(total_spend) else float(total_spend)
                metrics["avg_daily_spend"] = None if pd.isna(avg_spend) else float(avg_spend)
            elif col_lower in ["conversions", "conv"]:
                total_conv = df[col].sum()
                metrics["total_conversions"] = None if pd.isna(total_conv) else float(total_conv)
            elif col_lower in ["cpa", "cost_per_acquisition"]:
                avg_cpa = df[col].mean()
                metrics["avg_cpa"] = None if pd.isna(avg_cpa) else float(avg_cpa)
            elif col_lower in ["ctr", "click_through_rate"]:
                avg_ctr = df[col].mean()
                metrics["avg_ctr"] = None if pd.isna(avg_ctr) else float(avg_ctr)
            elif col_lower in ["roas", "return_on_ad_spend"]:
                avg_roas = df[col].mean()
                metrics["avg_roas"] = None if pd.isna(avg_roas) else float(avg_roas)

        return metrics

    @staticmethod
    def _analyze_experiments(df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze experiment results data"""
        metrics = {}

        # Look for experiment identifiers
        if "experiment_id" in df.columns:
            metrics["experiment_count"] = df["experiment_id"].nunique()

        # Look for variants
        variant_cols = [col for col in df.columns if "variant" in col.lower() or "variation" in col.lower()]
        if variant_cols:
            metrics["variants"] = df[variant_cols[0]].unique().tolist()

        # Date range if available
        date_cols = [col for col in df.columns if "date" in col.lower()]
        if date_cols:
            try:
                dates = pd.to_datetime(df[date_cols[0]])
                metrics["date_range"] = {
                    "start": dates.min().isoformat(),
                    "end": dates.max().isoformat(),
                }
            except:
                pass

        return metrics

    @staticmethod
    def get_detailed_analysis(campaigns: List[Dict[str, Any]], max_sample: int = 100) -> Dict[str, Any]:
        """
        Generate detailed performance analysis from campaign data

        Args:
            campaigns: List of campaign dictionaries
            max_sample: Maximum number of top/bottom performers to include

        Returns:
            Detailed analysis dictionary for LLM consumption
        """
        if not campaigns:
            return {"summary": "No campaign data available"}

        df = pd.DataFrame(campaigns)
        analysis = {
            "total_campaigns": len(df),
            "date_range": {},
            "performance_summary": {},
            "by_platform": {},
            "by_creative": {},
            "by_audience": {},
            "top_performers": [],
            "bottom_performers": [],
            "sample_campaigns": []
        }

        # Date range analysis
        date_cols = [col for col in df.columns if 'date' in col.lower()]
        if date_cols:
            try:
                dates = pd.to_datetime(df[date_cols[0]], errors='coerce')
                valid_dates = dates.dropna()
                if len(valid_dates) > 0:
                    analysis["date_range"] = {
                        "start": valid_dates.min().isoformat(),
                        "end": valid_dates.max().isoformat(),
                        "days": (valid_dates.max() - valid_dates.min()).days
                    }
            except:
                pass

        # Performance summary with NaN handling
        numeric_cols = df.select_dtypes(include=["number"]).columns
        for col in numeric_cols:
            col_lower = col.lower()
            values = df[col].dropna()
            if len(values) > 0:
                analysis["performance_summary"][col] = {
                    "mean": float(values.mean()),
                    "median": float(values.median()),
                    "min": float(values.min()),
                    "max": float(values.max()),
                    "std": float(values.std()) if len(values) > 1 else 0.0
                }

        # Platform analysis
        platform_cols = [col for col in df.columns if 'platform' in col.lower()]
        if platform_cols:
            platform_col = platform_cols[0]
            for platform in df[platform_col].unique():
                if pd.notna(platform):
                    platform_data = df[df[platform_col] == platform]
                    platform_metrics = {}
                    for col in numeric_cols:
                        values = platform_data[col].dropna()
                        if len(values) > 0:
                            platform_metrics[col] = {
                                "mean": float(values.mean()),
                                "total": float(values.sum()) if col.lower() in ['spend', 'cost', 'conversions', 'clicks'] else None
                            }
                    analysis["by_platform"][str(platform)] = {
                        "campaign_count": len(platform_data),
                        "metrics": platform_metrics
                    }

        # Creative type analysis
        creative_cols = [col for col in df.columns if 'creative' in col.lower() or 'ad_type' in col.lower()]
        if creative_cols:
            creative_col = creative_cols[0]
            for creative in df[creative_col].unique()[:10]:  # Limit to top 10
                if pd.notna(creative):
                    creative_data = df[df[creative_col] == creative]
                    analysis["by_creative"][str(creative)] = len(creative_data)

        # Audience analysis
        audience_cols = [col for col in df.columns if 'audience' in col.lower() or 'targeting' in col.lower()]
        if audience_cols:
            audience_col = audience_cols[0]
            for audience in df[audience_col].unique()[:10]:  # Limit to top 10
                if pd.notna(audience):
                    audience_data = df[df[audience_col] == audience]
                    analysis["by_audience"][str(audience)] = len(audience_data)

        # Top and bottom performers (by CPA if available, else by conversions)
        perf_col = None
        for col in ['cpa', 'cost_per_acquisition', 'conversions', 'roas']:
            if col in df.columns or col.upper() in df.columns or col.title() in df.columns:
                matching_cols = [c for c in df.columns if c.lower() == col]
                if matching_cols:
                    perf_col = matching_cols[0]
                    break

        if perf_col:
            df_sorted = df.dropna(subset=[perf_col]).copy()
            ascending = 'cpa' in perf_col.lower() or 'cost' in perf_col.lower()
            df_sorted = df_sorted.sort_values(by=perf_col, ascending=ascending)

            # Top performers
            top_n = min(10, len(df_sorted))
            for _, row in df_sorted.head(top_n).iterrows():
                # Convert row to dict, handling NaN values
                record = {}
                for k, v in row.items():
                    if pd.isna(v):
                        record[k] = None
                    elif isinstance(v, (int, float)):
                        record[k] = float(v)
                    else:
                        record[k] = str(v)
                analysis["top_performers"].append(record)

            # Bottom performers
            bottom_n = min(10, len(df_sorted))
            for _, row in df_sorted.tail(bottom_n).iterrows():
                record = {}
                for k, v in row.items():
                    if pd.isna(v):
                        record[k] = None
                    elif isinstance(v, (int, float)):
                        record[k] = float(v)
                    else:
                        record[k] = str(v)
                analysis["bottom_performers"].append(record)

        # Sample of recent campaigns for context
        sample_size = min(max_sample, len(df))
        for _, row in df.head(sample_size).iterrows():
            record = {}
            for k, v in row.items():
                if pd.isna(v):
                    record[k] = None
                elif isinstance(v, (int, float)):
                    record[k] = float(v)
                else:
                    record[k] = str(v)
            analysis["sample_campaigns"].append(record)

        return analysis

    @staticmethod
    def load_multiple_files(file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Load and analyze multiple files

        Args:
            file_paths: List of file paths

        Returns:
            List of file analyses
        """
        results = []

        for file_path in file_paths:
            try:
                analysis = DataLoader.analyze_file(file_path)
                results.append(analysis)
            except Exception as e:
                results.append({
                    "file_path": file_path,
                    "error": str(e),
                    "type": "error",
                })

        return results
