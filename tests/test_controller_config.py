"""O perfil preserva teclado/dados desconhecidos e não duplica combinações."""
import unittest
from tools.configure_xbox import edit


class TestControllerConfig(unittest.TestCase):
    def test_multibind_keeps_keyboard_and_unknown_sections_idempotently(self):
        original = '[Pad1]\nCross = Keyboard/K\nOther = keep\n\n[GPU]\nAdapter = keep too\n'
        values = {'Cross': 'SDL-0/FaceSouth'}
        result = edit(original, 'Pad1', values, True)
        self.assertIn('Cross = Keyboard/K\nCross = SDL-0/FaceSouth\n', result)
        self.assertIn('Other = keep', result)
        self.assertTrue(result.endswith('[GPU]\nAdapter = keep too\n'))
        self.assertEqual(edit(result, 'Pad1', values, True), result)

    def test_bom_and_global_cfg_are_preserved(self):
        text = '\ufeff[ControlMapping]\nCross = 10-189\n'
        self.assertEqual(edit(text, 'ControlMapping', {'Cross': '10-189,10-196:10-194'}),
                         '\ufeff[ControlMapping]\nCross = 10-189,10-196:10-194\n')
        self.assertEqual(edit('video = "keep"\ninput_save_state_btn = "4"\n', '', {'input_save_state_btn': '"5"'}),
                         'video = "keep"\ninput_save_state_btn = "5"\n')
