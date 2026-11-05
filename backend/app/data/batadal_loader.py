"""
SENTINEL AI - BATADAL Dataset Loader & EPANET Topology Parser
Handles ingestion of BATADAL C-Town water network SCADA files and EPANET .inp topology.
"""
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import os
import re
import pandas as pd
import numpy as np
from app.config import settings, BATADAL_SENSORS, TOPOLOGICAL_COUPLES
from app.data.validation import DataValidator


class BatadalLoader:
    """Manages discovery, loading, and structural parsing of the BATADAL dataset."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or settings.BATADAL_RAW_DIR
        self.validator = DataValidator()

    def get_dataset_status(self) -> Dict[str, Any]:
        """Reports the presence, file sizes, and status of official BATADAL files."""
        expected_files = {
            "training_dataset_1": ["BATADAL_dataset03.csv", "dataset03.csv", "training1.csv"],
            "training_dataset_2": ["BATADAL_dataset04.csv", "dataset04.csv", "training2.csv"],
            "test_dataset": ["BATADAL_test_dataset.csv", "test_dataset.csv", "test.csv"],
            "epanet_model": ["C-Town.inp", "ctown.inp", "CTown.inp"],
        }
        
        status = {}
        for key, candidates in expected_files.items():
            matched_path = None
            for c in candidates:
                candidate_path = self.data_dir / c
                if candidate_path.exists() and candidate_path.is_file():
                    matched_path = candidate_path
                    break
            
            if matched_path:
                status[key] = {
                    "exists": True,
                    "filename": matched_path.name,
                    "size_bytes": matched_path.stat().st_size,
                    "size_mb": round(matched_path.stat().st_size / (1024 * 1024), 2),
                    "path": str(matched_path)
                }
            else:
                status[key] = {
                    "exists": False,
                    "filename": candidates[0],
                    "size_bytes": 0,
                    "size_mb": 0.0,
                    "path": None
                }
        
        all_ready = status["training_dataset_1"]["exists"] and status["training_dataset_2"]["exists"]
        return {
            "dataset_name": "BATADAL (C-Town Water Network)",
            "directory": str(self.data_dir),
            "files": status,
            "ready_for_training": all_ready,
            "status_message": "All required training files present" if all_ready else "BATADAL files not found. Please place CSVs into data/raw/batadal/."
        }

    def _find_file(self, candidates: List[str]) -> Optional[Path]:
        for c in candidates:
            p = self.data_dir / c
            if p.exists() and p.is_file():
                return p
        return None

    def load_training_dataset_1(self) -> Optional[pd.DataFrame]:
        """Loads Dataset 03: Normal operational baseline (~1 year SCADA)."""
        file_path = self._find_file(["BATADAL_dataset03.csv", "dataset03.csv", "training1.csv"])
        if not file_path:
            return None
        
        df = pd.read_csv(file_path)
        df = self.validator.clean_columns(df)
        df, ts_col = self.validator.parse_timestamps(df)
        df = self.validator.handle_missing_values(df)
        return df

    def load_training_dataset_2(self) -> Optional[pd.DataFrame]:
        """Loads Dataset 04: Attack evaluation dataset (~6 months with attack flags)."""
        file_path = self._find_file(["BATADAL_dataset04.csv", "dataset04.csv", "training2.csv"])
        if not file_path:
            return None

        df = pd.read_csv(file_path)
        df = self.validator.clean_columns(df)
        df, ts_col = self.validator.parse_timestamps(df)
        df = self.validator.handle_missing_values(df)
        
        # Standardize attack flag column if present (in BATADAL, 1 = attack, -999 = normal)
        for col in ["ATT_FLAG", "att_flag", "Attack", "ATTACK", "label"]:
            if col in df.columns:
                raw_flags = df[col].astype(int)
                df["ATT_FLAG"] = np.where(raw_flags == 1, 1, 0)
                if col != "ATT_FLAG":
                    df.drop(columns=[col], inplace=True)
                break
                
        return df

    def load_test_dataset(self) -> Optional[pd.DataFrame]:
        """Loads unlabelled test dataset for exploratory evaluation."""
        file_path = self._find_file(["BATADAL_test_dataset.csv", "test_dataset.csv", "test.csv"])
        if not file_path:
            return None

        df = pd.read_csv(file_path)
        df = self.validator.clean_columns(df)
        df, ts_col = self.validator.parse_timestamps(df)
        df = self.validator.handle_missing_values(df)
        return df

    def parse_epanet_topology(self) -> Dict[str, Any]:
        """Parses the C-Town.inp EPANET network model to extract topological connections."""
        inp_path = self._find_file(["C-Town.inp", "ctown.inp", "CTown.inp"])
        
        # If .inp file is present, parse real sections
        if inp_path and inp_path.exists():
            return self._parse_inp_file(inp_path)
        
        # Fallback to verified C-Town EPANET topology constants
        return {
            "source": "verified_ctown_topology",
            "tanks": ["L_T1", "L_T2", "L_T3", "L_T4", "L_T5", "L_T6", "L_T7"],
            "pumps": ["F_PU1", "F_PU2", "F_PU3", "F_PU4", "F_PU5", "F_PU6", "F_PU7", "F_PU8", "F_PU9", "F_PU10", "F_PU11"],
            "valves": ["F_V2"],
            "junctions": ["P_J280", "P_J269", "P_J300", "P_J256", "P_J289", "P_J415", "P_J14", "P_J422"],
            "coupled_relationships": TOPOLOGICAL_COUPLES
        }

    def _parse_inp_file(self, file_path: Path) -> Dict[str, Any]:
        """Reads sections from an EPANET .inp file."""
        sections: Dict[str, List[str]] = {}
        current_section = None
        
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith(";"):
                    continue
                if line.startswith("[") and line.endswith("]"):
                    current_section = line[1:-1].strip().upper()
                    sections[current_section] = []
                elif current_section:
                    sections[current_section].append(line)

        return {
            "source": f"parsed_file:{file_path.name}",
            "sections_found": list(sections.keys()),
            "tanks": [line.split()[0] for line in sections.get("TANKS", []) if line.split()],
            "pumps": [line.split()[0] for line in sections.get("PUMPS", []) if line.split()],
            "valves": [line.split()[0] for line in sections.get("VALVES", []) if line.split()],
            "pipes_count": len(sections.get("PIPES", [])),
            "junctions_count": len(sections.get("JUNCTIONS", [])),
            "coupled_relationships": TOPOLOGICAL_COUPLES
        }

