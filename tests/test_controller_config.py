"""O perfil preserva teclado/dados desconhecidos e não duplica combinações."""
import unittest
from tools.configure_xbox import azahar_values, edit


class TestControllerConfig(unittest.TestCase):
    def test_auto_requires_one_measured_device_and_preserves_running_emulator(self):
        from tools.configure_xbox import connected_profile,auto_profile
        import tempfile
        entry={'id':'x','guid':'a'*32,'sdl_name':'Known'};registry={'controllers':[entry]};pad={'controller':True,'guid':'a'*32,'name':'Known'}
        self.assertEqual(connected_profile(registry,[pad]),entry)
        for pads in ([],[pad,pad],[{**pad,'guid':'b'*32}],[{**pad,'name':'Other'}]):self.assertIsNone(connected_profile(registry,pads))
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(auto_profile(directory,registry,[pad],apply=True,running=lambda:True)['state'],'preservado')

    def test_auto_is_idempotent_and_only_changes_model_bindings(self):
        from tools import configure_xbox as cx
        from unittest.mock import patch
        from pathlib import Path
        import tempfile
        entry={'id':'x','guid':'a'*32,'sdl_name':'Known'};pad={'controller':True,'guid':'a'*32,'name':'Known'}
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory);bindings=home/'GCPadNew.ini';other=home/'video.ini';bindings.write_text('old');other.write_text('keep')
            with patch.object(cx,'planned',return_value={bindings:'new',other:'wrong'}):
                result=cx.auto_profile(home,{'controllers':[entry]},[pad],apply=True,running=lambda:False)
                self.assertEqual(result['changed'],1);self.assertEqual(other.read_text(),'keep')
                self.assertEqual(cx.auto_profile(home,{'controllers':[entry]},[pad],apply=True,running=lambda:False)['changed'],0)
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


class TestAzaharScreens(unittest.TestCase):
    def test_gatilhos_trocam_a_tela_sem_back_e_zl_zr_vao_para_os_analogicos(self):
        controls, ui, _ = azahar_values('0300aa')
        key = lambda name: ui['Shortcuts\\Main%20Window\\' + name + '\\controller_keyseq']
        self.assertIn('axis:4', key('Toggle%20Screen%20Layout'))
        self.assertIn('axis:5', key('Swap%20Screens'))
        self.assertNotIn('||', key('Toggle%20Screen%20Layout') + key('Swap%20Screens'))
        self.assertIn('||', key('Quick%20Save'))
        self.assertNotIn('axis', controls['profiles\\1\\button_zl'] + controls['profiles\\1\\button_zr'])
