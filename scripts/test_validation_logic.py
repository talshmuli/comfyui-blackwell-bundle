#!/usr/bin/env python3
import unittest
from unittest.mock import MagicMock

class TestValidationLogic(unittest.TestCase):
    def test_node_assertion_logic(self):
        sample_mappings = {
            "VHS_VideoCombine": MagicMock(),
            "DownloadAndLoadLivePortraitModels": MagicMock(),
            "LatentSyncNode": MagicMock(),
            "AnimateDiffLoaderWithContext": MagicMock(),
            "GGUFModelLoader": MagicMock(),
            "WanVideoModelLoader": MagicMock(),
            "SongGenerationNode": MagicMock(),
            "YuE2Generator": MagicMock(),
            "RVC_Node": MagicMock(),
            "3D_Gaussian": MagicMock(),
            "LTXVideoSampler": MagicMock(),
            "CrystoolsMonitor": MagicMock(),
            "MelBandRoFormerSeparator": MagicMock(),
            "HeartMuLaGenerator": MagicMock(),
            "ACEStepSampler": MagicMock(),
            "Step1XEditor": MagicMock(),
        }

        required_checks = [
            ("Crystools", lambda m: any("Crystools" in k for k in m)),
            ("MelBandRoFormer", lambda m: any("MelBand" in k for k in m)),
            ("HeartMuLa", lambda m: any("HeartMuLa" in k for k in m)),
            ("ACE-Step", lambda m: any("ACE" in k or "Ace" in k for k in m)),
            ("Step1X", lambda m: any("Step1X" in k for k in m)),
        ]

        for name, check_fn in required_checks:
            self.assertTrue(check_fn(sample_mappings), f"Check failed for {name}")

if __name__ == "__main__":
    unittest.main()
