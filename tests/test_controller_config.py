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

    def test_core_options_unchanged_keep_their_order(self):
        # 22/10/2026: cada simulação reordenava o NDS.opt do melonDS sem mudar valor nenhum.
        text = 'melonds_screen_layout = "Hybrid Top"\nmelonds_console_mode = "DS"\nmelonds_touch_mode = "Mouse"\n'
        values = {'melonds_touch_mode': '"Mouse"', 'melonds_screen_layout': '"Hybrid Top"'}
        self.assertEqual(edit(text, '', values), text)
        changed = edit(text, '', {'melonds_touch_mode': '"Joystick"'})
        self.assertEqual(changed, text.replace('"Mouse"', '"Joystick"'), 'troca de valor fica no mesmo lugar')


class TestControllerRegistry(unittest.TestCase):
    def setUp(self):
        from tools import configure_xbox as cx
        self.cx = cx
        self.registry = cx.load_registry()

    def test_primary_is_xbox_one_and_all_requested_controllers_are_listed(self):
        self.assertEqual(self.registry['primary'], 'xbox-one')
        self.assertEqual({c['id'] for c in self.registry['controllers']},
                         {'xbox-one', 'xbox-series-s', 'galileo-g8', 'wgp16-nova-ii'})
        self.assertEqual(self.cx.dolphin_device(self.cx.pick_controller(self.registry)), 'SDL/0/Xbox One S Controller')

    def test_unmeasured_controller_refuses_instead_of_guessing_a_device_name(self):
        with self.assertRaises(SystemExit):
            self.cx.dolphin_device(self.cx.pick_controller(self.registry, 'galileo-g8'))
        with self.assertRaises(SystemExit):
            self.cx.pick_controller(self.registry, 'nao-existe')

    def test_learn_needs_exactly_one_pad_and_records_name_and_guid(self):
        pad = lambda i, name, guid='a' * 32: {'index': i, 'name': name, 'guid': guid, 'controller': True}
        with self.assertRaises(SystemExit):
            self.cx.learn(self.registry, 'galileo-g8', [pad(0, 'A'), pad(1, 'B')], '2026-10-28')
        entry = self.cx.learn(self.registry, 'galileo-g8', [pad(0, 'Galileo X')], '2026-10-28')
        self.assertEqual((entry['sdl_name'], entry['guid'], entry['measured']), ('Galileo X', 'a' * 32, '2026-10-28'))
        self.assertEqual(self.cx.dolphin_device(entry), 'SDL/0/Galileo X')

    def test_choose_pad_prefers_the_measured_name_over_other_pads(self):
        pads = [{'index': 0, 'name': 'Sony Wireless', 'guid': 'b' * 32, 'controller': True},
                {'index': 1, 'name': 'Xbox One S Controller', 'guid': 'c' * 32, 'controller': True}]
        self.assertEqual(self.cx.choose_pad(pads, {'sdl_name': 'Xbox One S Controller'}), 'c' * 32)
        self.assertEqual(self.cx.choose_pad(pads, {}), 'c' * 32)
        self.assertIsNone(self.cx.choose_pad(pads, {'sdl_name': 'Outro'}))
