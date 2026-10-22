"""Typography engine tests. Run: python -P -m unittest discover -s typography/tests -v"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import typography as T  # noqa: E402


class Registry(unittest.TestCase):
    def test_seven_distinct_roles(self):
        reg = T.registry()["roles"]
        self.assertEqual(len(reg), 7)
        fams = [r["preferred"]["family"] for r in reg.values()]
        self.assertEqual(len(set(fams)), 7)
        self.assertIn("Garamond", fams)
        self.assertIn("Cormorant Garamond", fams)   # separate entries

    def test_eight_pairings_ten_presets(self):
        self.assertEqual(len(T.pairings()), 8)
        names = set(T.presets())
        self.assertEqual(names, {"CLEAN_TALKING_HEAD", "HELVETICA_GARAMOND_HIGHLIGHT", "VIRAL_IMPACT_HOOK", "ROCKWELL_EDITORIAL",
                                 "LUXURY_CORMORANT", "SNELL_CINEMATIC", "BLACKSWORD_ELEGANT_ACCENT", "IMPACT_ROCKWELL_AD",
                                 "HELVETICA_CORMORANT_PREMIUM", "MULTI_FONT_STORYTELLING"})


class Resolve(unittest.TestCase):
    def spec(self, role):
        return T.registry()["roles"][role]

    def test_fallback_never_reported_as_original(self):
        r = T.resolve_role("clean_caption", self.spec("clean_caption"), faces=[], local={})
        self.assertEqual(r["state"], "FALLBACK_ACTIVE")
        self.assertFalse(r["exact"])
        self.assertEqual(r["resolved"], "Inter")

    def test_exact_system_font(self):
        faces = [{"family": "Impact", "style": "Regular", "full": "Impact", "ps": "Impact", "weight": 400, "italic": False, "path": "x/impact.ttf"}]
        r = T.resolve_role("impact_hook", self.spec("impact_hook"), faces=faces, local={})
        self.assertEqual(r["state"], "EXACT_AVAILABLE")
        self.assertTrue(r["exact"])

    def test_helvetica_neue_is_not_helvetica(self):
        faces = [{"family": "Helvetica Neue", "style": "Regular", "full": "Helvetica Neue", "ps": "HelveticaNeue", "weight": 400, "italic": False, "path": "x"}]
        r = T.resolve_role("clean_caption", self.spec("clean_caption"), faces=faces, local={})
        self.assertNotEqual(r["state"], "EXACT_AVAILABLE")

    def test_blacksword_needs_licence_even_if_installed(self):
        faces = [{"family": "Blacksword", "style": "Regular", "full": "Blacksword", "ps": "Blacksword", "weight": 400, "italic": False, "path": "x"}]
        r = T.resolve_role("expressive_script", self.spec("expressive_script"), faces=faces, local={})
        self.assertEqual(r["state"], "LICENSE_REQUIRED")
        self.assertEqual(r["resolved"], "Italianno")

    def test_cormorant_is_exact_open_source(self):
        r = T.resolve_role("luxury_serif", self.spec("luxury_serif"), faces=[], local={})
        self.assertEqual(r["state"], "OPEN_SOURCE_INSTALLED")
        self.assertTrue(r["exact"])


class Select(unittest.TestCase):
    def test_talking_head_is_helvetica_garamond(self):
        d = T.select({"text": "Your brand deserves better", "video_type": "talking_head", "emphasis": "medium"})
        self.assertEqual((d["primary_font_role"], d["secondary_font_role"], d["pairing"]), ("clean_caption", "classical_highlight", "helvetica_garamond"))

    def test_hook_is_impact(self):
        self.assertEqual(T.select({"text": "STOP SCROLLING", "video_type": "viral", "scene_type": "hook"})["primary_font_role"], "impact_hook")

    def test_price_is_impact(self):
        self.assertEqual(T.select({"text": "ONLY ₹50,000", "video_type": "promo"})["primary_font_role"], "impact_hook")

    def test_luxury_is_cormorant(self):
        self.assertEqual(T.select({"text": "Timeless Elegance", "video_type": "luxury"})["primary_font_role"], "luxury_serif")

    def test_cinematic_is_editorial(self):
        self.assertEqual(T.select({"text": "Every Detail Matters", "video_type": "cinematic"})["primary_font_role"], "editorial_slab")

    def test_emotional_accent_is_script(self):
        self.assertEqual(T.select({"text": "A special moment", "scene_type": "emotional"})["secondary_font_role"], "expressive_script")

    def test_devanagari_gets_script_fallback(self):
        d = T.select({"text": "हर क्रिएटर", "language": "hindi"})
        self.assertEqual(d["script_fallback_role"], "devanagari")
        self.assertEqual(T.detect_script("Har creator ye font use karta hai"), "latin")


class Layout(unittest.TestCase):
    def setUp(self):
        self.font = str(T.OPEN_SOURCE / "Anton" / "Anton-Regular.ttf")
        if not Path(self.font).exists():
            self.skipTest("run setup_fonts.py first")

    def test_measure_grows_with_size(self):
        a, b = T.measure("IMPACT", self.font, 100), T.measure("IMPACT", self.font, 200)
        self.assertAlmostEqual(b["width"], 2 * a["width"], delta=1)

    def test_wrap_respects_width_and_never_splits_words(self):
        lines = T.wrap("THIS CHANGES EVERYTHING FOR CREATORS", self.font, 120, 700, max_lines=4)
        self.assertTrue(all(T.measure(l, self.font, 120)["width"] <= 700 or " " not in l for l in lines))
        self.assertEqual(" ".join(lines), "THIS CHANGES EVERYTHING FOR CREATORS")

    def test_fit_size(self):
        px = T.fit_size("3 FONTS YOU NEED", self.font, 960, 400, 60)
        self.assertLessEqual(T.measure("3 FONTS YOU NEED", self.font, px)["width"], 960)


if __name__ == "__main__":
    unittest.main()
