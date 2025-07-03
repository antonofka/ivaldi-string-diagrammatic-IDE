import tkinter
import unittest
from unittest.mock import patch

import constants as const
from MVP.refactored.backend.diagram_callback import Receiver
from MVP.refactored.frontend.canvas_objects.box import Box
from MVP.refactored.frontend.canvas_objects.connection import Connection
from MVP.refactored.frontend.canvas_objects.spider import Spider
from MVP.refactored.frontend.canvas_objects.types.connection_type import ConnectionType
from MVP.refactored.frontend.canvas_objects.wire import Wire
from MVP.refactored.frontend.windows.main_diagram import MainDiagram


class TestCustomCanvas(unittest.TestCase):

    async def _start_app(self):
        self.main_diagram.mainloop()

    def setUp(self):
        self.main_diagram = MainDiagram(Receiver())
        self.custom_canvas = self.main_diagram.custom_canvas
        self._start_app()

    def tearDown(self):
        self.main_diagram.destroy()


class Tests(TestCustomCanvas):
    def test__init__no_objects_at_start(self):
        self.assertListEqual([], self.custom_canvas.boxes)
        self.assertListEqual([], self.custom_canvas.outputs)
        self.assertListEqual([], self.custom_canvas.inputs)
        self.assertListEqual([], self.custom_canvas.spiders)
        self.assertListEqual([], self.custom_canvas.wires)

    def test__init__other_values(self):
        self.assertIsNone(self.custom_canvas.temp_wire)
        self.assertIsNone(self.custom_canvas.temp_end_connection)
        self.assertFalse(self.custom_canvas.pulling_wire)
        self.assertFalse(self.custom_canvas.quick_pull)
        self.assertIsNone(self.custom_canvas.current_wire_start)
        self.assertFalse(self.custom_canvas.draw_wire_mode)
        self.assertIsNone(self.custom_canvas.select_box)
        self.assertFalse(self.custom_canvas.selecting)

    def test__init__default_box_shape(self):
        expected = const.RECTANGLE
        actual = self.custom_canvas.box_shape
        self.assertEqual(expected, actual)

    def test__init__zoom_values(self):
        expected_total_scale = 1.0
        expected_delta = 0.75
        expected_prev_scale = 1.0

        actual_total_scale = self.custom_canvas.total_scale
        actual_delta = self.custom_canvas.delta
        actual_prev_scale = self.custom_canvas.prev_scale

        self.assertEqual(expected_total_scale, actual_total_scale)
        self.assertEqual(expected_delta, actual_delta)
        self.assertEqual(expected_prev_scale, actual_prev_scale)

    def test__init__pan_value(self):
        expected_speed = 20

        actual_speed = self.custom_canvas.pan_speed
        self.assertEqual(expected_speed, actual_speed)

    def test__init__corners_at_canvas_edges(self):
        self.assertEqual(4, len(self.custom_canvas.corners))

        top_left = self.custom_canvas.corners[0]
        self.assertEqual(top_left.location,
                         [
                             0,
                             0
                         ])

        bottom_left = self.custom_canvas.corners[1]
        self.assertEqual(bottom_left.location,
                         [
                             0,
                             self.custom_canvas.canvasy(self.custom_canvas.winfo_height())
                         ])

        top_right = self.custom_canvas.corners[2]
        self.assertEqual(top_right.location,
                         [
                             self.custom_canvas.canvasx(self.custom_canvas.winfo_width()),
                             0
                         ])

        bottom_right = self.custom_canvas.corners[3]
        self.assertEqual(bottom_right.location,
                         [
                             self.custom_canvas.canvasx(self.custom_canvas.winfo_width()),
                             self.custom_canvas.canvasy(self.custom_canvas.winfo_height())
                         ])

    def test__on_hover__changes_hover_item_to_what_was_given(self):
        self.custom_canvas.on_hover("TEST")

        self.assertEqual("TEST", self.custom_canvas.hover_item)

    def test__on_leave_hover__changes_hover_item_to_none(self):
        self.custom_canvas.on_hover("TEST")
        self.assertEqual("TEST", self.custom_canvas.hover_item)

        self.custom_canvas.on_leave_hover()
        self.assertIsNone(self.custom_canvas.hover_item)

    @patch('MVP.refactored.frontend.canvas_objects.spider.Spider.on_resize_scroll')
    def test__scale_item__calls_method_on_hover_item(self, resize_mock):
        spider = Spider((100, 100), self.custom_canvas)
        self.custom_canvas.hover_item = spider

        self.custom_canvas.scale_item(tkinter.Event())

        self.assertEqual(1, resize_mock.call_count)

    @patch('tkinter.Place.place')
    @patch('tkinter.Place.place_forget')
    def test__toggle_search_results_button__places_if_search_active(self, forget_mock, place_mock):
        self.main_diagram.is_search_active = True

        self.custom_canvas.toggle_search_results_button()
        self.assertEqual(1, place_mock.call_count)
        self.assertEqual(0, forget_mock.call_count)

    @patch('tkinter.Place.place')
    @patch('tkinter.Place.place_forget')
    def test__toggle_search_results_button__place_forget_if_no_search_active(self, forget_mock, place_mock):
        self.main_diagram.is_search_active = False

        self.custom_canvas.toggle_search_results_button()
        self.assertEqual(1, forget_mock.call_count)
        self.assertEqual(0, place_mock.call_count)

    @patch('tkinter.Place.place')
    @patch('tkinter.Place.place_forget')
    def test__update_search_results_button__resets_place_if_active_search(self, forget_mock, place_mock):
        self.main_diagram.is_search_active = True

        self.custom_canvas.update_search_results_button()
        self.assertEqual(1, forget_mock.call_count)
        self.assertEqual(1, place_mock.call_count)

    @patch('tkinter.Place.place')
    @patch('tkinter.Place.place_forget')
    def test__update_search_results_button__does_nothing_if_no_active_search(self, forget_mock, place_mock):
        self.main_diagram.is_search_active = False

        self.custom_canvas.update_search_results_button()
        self.assertEqual(0, forget_mock.call_count)
        self.assertEqual(0, place_mock.call_count)

    @patch('MVP.refactored.frontend.canvas_objects.spider.Spider.deselect')
    @patch('MVP.refactored.frontend.canvas_objects.box.Box.deselect')
    def test__remove_search_highlights__deselects_items_in_search_result_highlights(self,
                                                                                    spider_deselect_mock,
                                                                                    box_deselect_mock):
        spider = Spider((100, 100), self.custom_canvas)
        box = Box(self.custom_canvas, 100, 200)

        self.custom_canvas.search_result_highlights.append(box)
        self.custom_canvas.search_result_highlights.append(spider)

        self.custom_canvas.remove_search_highlights()

        self.assertEqual(1, spider_deselect_mock.call_count)
        self.assertEqual(1, box_deselect_mock.call_count)

    def test__remove_search_highlights__removes_items_in_search_result_highlights(self):
        spider = Spider((100, 100), self.custom_canvas)
        box = Box(self.custom_canvas, 100, 200)

        self.custom_canvas.search_result_highlights.append(box)
        self.custom_canvas.search_result_highlights.append(spider)

        self.custom_canvas.remove_search_highlights()

        self.assertListEqual([], self.custom_canvas.search_result_highlights)

    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.toggle_search_results_button')
    def test__remove_search_highlights__calls_toggle_search_results_button(self, toggle_mock):
        self.custom_canvas.remove_search_highlights()

        self.assertEqual(1, toggle_mock.call_count)

    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.__select_start__')
    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.__select_motion__')
    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.__select_release__')
    def test__select_all__callouts_if_currently_opened_canvas(self, start_mock, motion_mock, release_mock):
        self.main_diagram.custom_canvas = self.custom_canvas

        self.custom_canvas.select_all()

        self.assertEqual(1, start_mock.call_count)
        self.assertEqual(1, motion_mock.call_count)
        self.assertEqual(1, release_mock.call_count)

    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.__select_start__')
    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.__select_motion__')
    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.__select_release__')
    def test__select_all__adds_canvas_elements_to_selector_if_not_opened_and_does_not_call_functions(self,
                                                                                                     start_mock,
                                                                                                     motion_mock,
                                                                                                     release_mock):
        self.main_diagram.custom_canvas = None
        self.custom_canvas.boxes = ["box"]
        self.custom_canvas.spiders = ["spider"]
        self.custom_canvas.wires = ["wire"]

        self.custom_canvas.select_all()

        self.assertEqual(0, start_mock.call_count)
        self.assertEqual(0, motion_mock.call_count)
        self.assertEqual(0, release_mock.call_count)

        self.assertListEqual(self.custom_canvas.spiders, self.custom_canvas.selector.selected_spiders)
        self.assertListEqual(self.custom_canvas.boxes, self.custom_canvas.selector.selected_boxes)
        self.assertListEqual(self.custom_canvas.wires, self.custom_canvas.selector.selected_wires)

        expected = self.custom_canvas.boxes + self.custom_canvas.spiders + self.custom_canvas.wires
        self.assertListEqual(expected, self.custom_canvas.selector.selected_items)

    def test__update_prev_winfo_size__updates_prev_measurements(self):
        self.custom_canvas.prev_height_max, self.custom_canvas.prev_width_max = 0, 0
        self.custom_canvas.prev_height_min, self.custom_canvas.prev_width_min = 0, 0

        self.custom_canvas.update_prev_winfo_size()

        self.assertEqual(self.custom_canvas.winfo_width(), self.custom_canvas.prev_width_max)
        self.assertEqual(0, self.custom_canvas.prev_width_min)
        self.assertEqual(self.custom_canvas.winfo_height(), self.custom_canvas.prev_height_max)
        self.assertEqual(0, self.custom_canvas.prev_height_min)

    @patch('MVP.refactored.frontend.canvas_objects.wire.Wire.update')
    @patch('MVP.refactored.frontend.canvas_objects.box.Box.update_size')
    def test__move_boxes_spiders__callouts(self, box_mock, wire_mock):
        box = Box(self.custom_canvas, 100, 200)
        spider = Spider((100, 100), self.custom_canvas)
        spider2 = Spider((200, 100), self.custom_canvas)
        wire = Wire(self.custom_canvas, spider, spider2)

        self.custom_canvas.boxes = [box]
        self.custom_canvas.spiders = [spider, spider2]
        self.custom_canvas.wires = [wire]

        box_mock.call_count = 0
        wire_mock.call_count = 0

        self.custom_canvas.move_boxes_spiders("x", 1)

        self.assertEqual(1, box_mock.call_count)
        self.assertEqual(1, wire_mock.call_count)

    @patch('MVP.refactored.frontend.canvas_objects.wire.Wire.update')
    def test__move_boxes_spiders__updates_temp_wire_if_pulling_wire(self, wire_mock):
        wire = Wire(self.custom_canvas, None, None, is_temporary=True)

        wire_mock.call_count = 0

        self.custom_canvas.move_boxes_spiders("x", 1)

        self.assertEqual(0, wire_mock.call_count)

        self.custom_canvas.pulling_wire = True
        self.custom_canvas.temp_wire = wire

        self.custom_canvas.move_boxes_spiders("x", 1)

        self.assertEqual(1, wire_mock.call_count)

    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.show_context_menu')
    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.cancel_wire_pulling')
    @patch('MVP.refactored.frontend.util.selector.Selector.finish_selection')
    def test__handle_right_click__finishes_selection_if_selecting(self, selection_mock, cancel_mock, context_menu_mock):
        self.custom_canvas.selector.selecting = True

        self.custom_canvas.handle_right_click(None)

        self.assertEqual(1, selection_mock.call_count)
        self.assertEqual(0, cancel_mock.call_count)
        self.assertEqual(1, context_menu_mock.call_count)

    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.show_context_menu')
    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.cancel_wire_pulling')
    @patch('MVP.refactored.frontend.util.selector.Selector.finish_selection')
    def test__handle_right_click__does_not_finish_selection_if_not_selecting(self, selection_mock,
                                                                             cancel_mock, context_menu_mock):
        self.custom_canvas.selector.selecting = False

        self.custom_canvas.handle_right_click(None)

        self.assertEqual(0, selection_mock.call_count)
        self.assertEqual(0, cancel_mock.call_count)
        self.assertEqual(1, context_menu_mock.call_count)

    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.show_context_menu')
    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.cancel_wire_pulling')
    @patch('MVP.refactored.frontend.util.selector.Selector.finish_selection')
    def test__handle_right_click__cancels_wire_pulling_if_in_draw_wire_mode(self, selection_mock,
                                                                            cancel_mock, context_menu_mock):
        self.custom_canvas.draw_wire_mode = True

        self.custom_canvas.handle_right_click(None)

        self.assertEqual(0, selection_mock.call_count)
        self.assertEqual(1, cancel_mock.call_count)
        self.assertEqual(0, context_menu_mock.call_count)

    @patch('MVP.refactored.frontend.components.toolbar.Toolbar.update_canvas_label')
    def test__set_name__changes_variable_and_calls_update(self, update_mock):
        self.custom_canvas.name_text = None

        self.custom_canvas.set_name("new name")

        self.assertEqual("new name", self.custom_canvas.name_text)
        self.assertEqual(1, update_mock.call_count)

    def test__get_connection_from_location__returns_none_if_not_draw_wire_mode(self):
        self.custom_canvas.draw_wire_mode = False

        self.assertIsNone(self.custom_canvas.get_connection_from_location(None))

    def test__get_connection_from_location__returns_none_if_not_quick_pull(self):
        self.custom_canvas.quick_pull = False

        self.assertIsNone(self.custom_canvas.get_connection_from_location(None))

    def test__get_connection_from_location__returns_connection_on_location(self):
        self.custom_canvas.draw_wire_mode = True
        connection = Connection(None, 1, const.LEFT, (100, 100), self.custom_canvas)
        connection2 = Connection(None, 2, const.LEFT, (200, 200), self.custom_canvas)

        self.custom_canvas.outputs = [connection2]
        self.custom_canvas.inputs = [connection]

        event = tkinter.Event()
        event.x, event.y = 100, 100

        actual = self.custom_canvas.get_connection_from_location(event)

        self.assertEqual(connection, actual)

    def test__start_pulling_wire__creates_temp_wire_and_connection(self):
        self.custom_canvas.draw_wire_mode = True
        self.custom_canvas.pulling_wire = True

        self.custom_canvas.temp_wire = None
        self.custom_canvas.temp_end_connection = Connection(None, None, None,
                                                            (101, 100), self.custom_canvas)
        self.custom_canvas.current_wire_start = Connection(None, None, None,
                                                           (101, 100), self.custom_canvas)

        event = tkinter.Event()
        event.x, event.y = 100, 100

        self.custom_canvas.start_pulling_wire(event)

        self.assertIsNotNone(self.custom_canvas.temp_wire)
        self.assertIsNotNone(self.custom_canvas.temp_end_connection)

    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.nullify_wire_start')
    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.cancel_wire_pulling')
    def test__end_wire_to_connection__callouts_if_connection_is_start_connection(self, cancel_mock, nullify_mock):
        connection = Connection(None, 1, const.LEFT, (100, 100), self.custom_canvas)
        self.custom_canvas.current_wire_start = connection
        self.custom_canvas.end_wire_to_connection(connection)

        self.assertEqual(1, nullify_mock.call_count)
        self.assertEqual(1, cancel_mock.call_count)

    @patch('MVP.refactored.frontend.canvas_objects.wire.Wire.delete')
    @patch('MVP.refactored.frontend.canvas_objects.connection.Connection.delete')
    def test__cancel_wire_pulling__resets_variables(self, _, __):
        self.custom_canvas.temp_wire = Wire(self.custom_canvas, None, None, is_temporary=True)
        self.custom_canvas.temp_end_connection = Connection(None, 1, const.LEFT, (100, 100), self.custom_canvas)
        self.custom_canvas.pulling_wire = True
        self.custom_canvas.draw_wire_mode = True
        self.custom_canvas.quick_pull = True

        self.custom_canvas.cancel_wire_pulling()

        self.assertIsNone(self.custom_canvas.temp_wire)
        self.assertIsNone(self.custom_canvas.temp_end_connection)
        self.assertFalse(self.custom_canvas.pulling_wire)
        self.assertFalse(self.custom_canvas.draw_wire_mode)
        self.assertFalse(self.custom_canvas.quick_pull)

    @patch('MVP.refactored.frontend.canvas_objects.connection.Connection.deselect')
    def test__nullify_wire_start__deselects_and_turns_to_none(self, deselect_mock):
        self.custom_canvas.current_wire_start = Connection(None, 1, const.LEFT, (100, 100), self.custom_canvas)

        self.custom_canvas.nullify_wire_start()

        self.assertEqual(1, deselect_mock.call_count)
        self.assertIsNone(self.custom_canvas.current_wire_start)

    def test__add_box__adds_box_to_boxes(self):
        self.assertListEqual([], self.custom_canvas.boxes)

        self.custom_canvas.add_box()

        self.assertEqual(1, len(self.custom_canvas.boxes))
        self.assertTrue(isinstance(self.custom_canvas.boxes[0], Box))

    def test__add_box__creates_box_at_given_location(self):
        self.custom_canvas.add_box(loc=(150, 200))

        box = self.custom_canvas.boxes[0]

        self.assertListEqual([150, 200], [box.x, box.y])

    def test__add_box__create_box_with_given_size(self):
        self.custom_canvas.add_box(size=(100, 200))

        box = self.custom_canvas.boxes[0]

        self.assertListEqual([100, 200], box.size)

    def test__add_box__creates_box_with_given_style(self):
        self.custom_canvas.add_box(style=const.TRIANGLE)

        box = self.custom_canvas.boxes[0]

        self.assertEqual(const.TRIANGLE, box.style)

    def test__add_box__uses_default_style_if_not_specified(self):
        self.custom_canvas.box_shape = const.TRIANGLE

        self.custom_canvas.add_box()

        box = self.custom_canvas.boxes[0]

        self.assertEqual(const.TRIANGLE, box.style)

    def test__add_box__returns_box_object(self):
        self.assertTrue(isinstance(self.custom_canvas.add_box(), Box))

    def test__get_box_by_id__returns_box_with_given_id(self):
        self.custom_canvas.add_box(id_=10)
        self.custom_canvas.add_box(id_=11)
        expected = self.custom_canvas.boxes[0]

        actual = self.custom_canvas.get_box_by_id(10)

        self.assertEqual(expected, actual)

    def test__get_box_by_id__returns_none_if_no_id(self):
        self.custom_canvas.add_box(id_=1)

        expected = None
        actual = self.custom_canvas.get_box_by_id(2)

        self.assertEqual(expected, actual)

    def test__add_spider__adds_spider(self):
        self.assertListEqual([], self.custom_canvas.spiders)

        self.custom_canvas.add_spider()

        self.assertEqual(1, len(self.custom_canvas.spiders))
        self.assertTrue(isinstance(self.custom_canvas.spiders[0], Spider))

    def test__add_spider__creates_spider_at_given_location(self):
        self.custom_canvas.add_spider(loc=(150, 200))
        spider = self.custom_canvas.spiders[0]

        expected = [150, 200]

        self.assertListEqual(expected, [spider.x, spider.y])
        self.assertListEqual(expected, spider.location)

    def test__add_spider__creates_spider_with_given_type(self):
        self.custom_canvas.add_spider(connection_type=ConnectionType.NINTH)

        expected = ConnectionType.NINTH
        actual = self.custom_canvas.spiders[0].type

        self.assertEqual(expected, actual)

    def test__add_spider__returns_spider_object(self):
        self.assertTrue(isinstance(self.custom_canvas.add_spider(), Spider))

    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.reset_zoom')
    @patch('tkinter.filedialog.asksaveasfilename', return_value="file name")
    @patch('MVP.refactored.frontend.windows.main_diagram.MainDiagram.generate_png')
    def test__save_as_png__callouts_generates_if_file_name_chosen(self, generate_mock, asksaveasfilename_mock,
                                                                  reset_zoom_mock):
        self.custom_canvas.save_as_png()

        self.assertEqual(1, reset_zoom_mock.call_count)
        self.assertEqual(1, asksaveasfilename_mock.call_count)
        self.assertEqual(1, generate_mock.call_count)

    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.reset_zoom')
    @patch('tkinter.filedialog.asksaveasfilename', return_value=None)
    @patch('MVP.refactored.frontend.windows.main_diagram.MainDiagram.generate_png')
    def test__save_as_png__callouts_no_generation_no_filename(self, generate_mock, asksaveasfilename_mock,
                                                              reset_zoom_mock):
        self.custom_canvas.save_as_png()

        self.assertEqual(1, reset_zoom_mock.call_count)
        self.assertEqual(1, asksaveasfilename_mock.call_count)
        self.assertEqual(0, generate_mock.call_count)

    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.reset_zoom')
    def test__open_tikz_generator__resets_zoom(self, reset_zoom_mock):
        self.custom_canvas.open_tikz_generator()

        self.assertEqual(1, reset_zoom_mock.call_count)

    @patch('MVP.refactored.frontend.windows.tikz_window.TikzWindow.__init__', return_value=None)
    def test__open_tikz_generator__opens_tikz_window(self, init_mock):
        self.custom_canvas.open_tikz_generator()

        self.assertEqual(1, init_mock.call_count)

    def test__toggle_draw_wire_mode__toggles_draw_wire_mode_value(self):
        self.custom_canvas.draw_wire_mode = False

        self.custom_canvas.toggle_draw_wire_mode()
        self.assertTrue(self.custom_canvas.draw_wire_mode)

        self.custom_canvas.toggle_draw_wire_mode()
        self.assertFalse(self.custom_canvas.draw_wire_mode)

    def test__toggle_draw_wire_mode__toggling_on_turns_button_style_to_success(self):
        self.custom_canvas.draw_wire_mode = False

        self.custom_canvas.toggle_draw_wire_mode()

        expected = "success.TButton"
        actual = self.main_diagram.draw_wire_button.configure("bootstyle")

        self.assertEqual(expected, actual)

    def test__toggle_draw_wire_mode__toggling_on_turns_button_style_to_primary_outline(self):
        self.custom_canvas.draw_wire_mode = True

        self.custom_canvas.toggle_draw_wire_mode()

        expected = "primary.Outline.TButton"
        actual = self.main_diagram.draw_wire_button.configure("bootstyle")

        self.assertEqual(expected, actual)

    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.update_corners')
    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.init_corners')
    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.update_inputs_outputs')
    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.update_prev_winfo_size')
    @patch('MVP.refactored.frontend.components.toolbar.Toolbar.update_canvas_label')
    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.__on_configure_move__')
    def test__on_canvas_resize__callouts_if_no_zoom(self, configure_move_mock, update_label_mock, update_size_mock,
                                                    update_io_mock, init_corner_mock, update_corners_mock):
        configure_move_mock.call_count = 0
        update_label_mock.call_count = 0
        update_size_mock.call_count = 0
        update_io_mock.call_count = 0
        init_corner_mock.call_count = 0

        self.custom_canvas.on_canvas_resize(None)

        self.assertEqual(1, configure_move_mock.call_count)
        self.assertEqual(1, update_label_mock.call_count)
        self.assertEqual(1, update_size_mock.call_count)
        self.assertEqual(1, update_io_mock.call_count)
        self.assertEqual(1, init_corner_mock.call_count)
        self.assertEqual(0, update_corners_mock.call_count)

    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.update_corners')
    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.init_corners')
    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.update_inputs_outputs')
    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.update_prev_winfo_size')
    @patch('MVP.refactored.frontend.components.toolbar.Toolbar.update_canvas_label')
    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.__on_configure_move__')
    def test__on_canvas_resize__callouts_if_zoomed(self, configure_move_mock, update_label_mock, update_size_mock,
                                                   update_io_mock, init_corner_mock, update_corners_mock):
        self.custom_canvas.total_scale = 3
        configure_move_mock.call_count = 0
        update_label_mock.call_count = 0
        update_size_mock.call_count = 0
        update_io_mock.call_count = 0
        init_corner_mock.call_count = 0

        self.custom_canvas.on_canvas_resize(None)

        self.assertEqual(1, configure_move_mock.call_count)
        self.assertEqual(1, update_label_mock.call_count)
        self.assertEqual(1, update_size_mock.call_count)
        self.assertEqual(1, update_io_mock.call_count)
        self.assertEqual(0, init_corner_mock.call_count)
        self.assertEqual(1, update_corners_mock.call_count)

    @patch('MVP.refactored.frontend.canvas_objects.corner.Corner.move_to')
    @patch('MVP.refactored.frontend.components.custom_canvas.CustomCanvas.update_inputs_outputs')
    def test__init_corners__callouts(self, update_mock, move_mock):
        self.custom_canvas.init_corners()

        self.assertEqual(4, move_mock.call_count)
        self.assertEqual(1, update_mock.call_count)

    def test__delete_everything__clears_lists_and_active_types(self):
        self.custom_canvas.add_box()
        self.custom_canvas.add_box()
        self.custom_canvas.add_box()
        self.custom_canvas.add_spider()
        self.custom_canvas.add_spider()
        Connection.active_types = 4

        self.assertEqual(5, len(self.custom_canvas.boxes + self.custom_canvas.spiders))
        self.assertEqual(4, Connection.active_types)

        self.custom_canvas.delete_everything()

        self.assertEqual(0, len(self.custom_canvas.boxes + self.custom_canvas.spiders))
        self.assertEqual(1, Connection.active_types)

    def test__set_box_shape__sets_shape(self):
        self.custom_canvas.box_shape = "old shape"

        self.custom_canvas.set_box_shape("new shape")

        self.assertEqual("new shape", self.custom_canvas.box_shape)
