import unittest
from unittest.mock import patch

import ui


class ScrollInputTests(unittest.TestCase):
    def test_windows_and_trackpad_wheel_directions(self):
        self.assertEqual(ui.scroll_units(120), -1)
        self.assertEqual(ui.scroll_units(-120), 1)
        self.assertEqual(ui.scroll_units(960), -3)
        self.assertEqual(ui.scroll_units(-960), 3)

    def test_screen_clear_preserves_accessibility_overlays(self):
        class Widget:
            def __init__(self, persistent=False):
                self._edupy_persistent = persistent
                self.destroyed = False
            def destroy(self): self.destroyed = True
        class Root:
            def __init__(self): self.regular=Widget();self.ruler=Widget(True)
            def winfo_children(self): return [self.regular,self.ruler]
            def attributes(self,*_): pass
        root=Root()
        with patch.object(ui,"REDUCED_MOTION",True):ui.clear(root)
        self.assertTrue(root.regular.destroyed)
        self.assertFalse(root.ruler.destroyed)

    def test_linux_wheel_buttons(self):
        self.assertEqual(ui.scroll_units(button_number=4), -3)
        self.assertEqual(ui.scroll_units(button_number=5), 3)
        self.assertEqual(ui.scroll_units(), 0)


if __name__ == "__main__":
    unittest.main()
