from kivy.config import Config

Config.read("./gui/config.ini")

from random import random
from threading import Thread
import time
from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

import backend

USE_BACKEND = True  # if False, won't connect backend, run simulation data instead


class MainLayout(Widget):
    CENTIMETER_PER_PIXEL = 1.5  # how many centimeters a kivy pixel represents

    FIRST_FLOOR_CELLING_HEIGHT = (
        1.5  # h >= FIRST_FLOOR_CELLING_HEIGHT: 2F, h < FIRST_FLOOR_CELLING_HEIGHT: 1F
    )
    FLOOR_COLORS = {
        "default": (0.9, 0.1, 0.1, 0.9),
        "1": (101 / 255, 9 / 255, 179 / 255, 1),
        "2": (0 / 255, 166 / 255, 66 / 255, 1),
    }
    path_dot_color = None  # color of the dot used to draw the path

    aoi_corners = []
    aoi_edges = {
        "normal": {},
        "closing line": {},
    }  # {edge_name: edge_object} e.g., {1-2: <edge object xxxx>}

    draw_path_has_started = False
    draw_path_event = None

    PATH_DOT_DIAMETER_IN_PIXEL = 20
    # REVERSE_XY = True  # reverse x-y axis
    CLOCK_SCHEDULE_INTERVAL = 0.2
    alive_path_dot_list = []  # stores a list of (color, circle) tuples
    PATH_DOT_LIFETIME = 6  # (unit: update time) each path dot's life time, old dots will gradually fade out and be removed from the alive_path_dot_list lise

    backend_thread = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.tagPos = [-1, -1, -1]
        self.tagBaseDist = [-1, -1, -1, -1]

        self.start_backend()
        Clock.schedule_interval(
            lambda dt: self.update_tag_data(), self.CLOCK_SCHEDULE_INTERVAL
        )

    def start_backend(self):

        base_a_coor = (0, 5.86, 2.0)
        base_b_coor = (8.535, 5.86, 2.0)
        base_c_coor = (8.535, 0, 2.0)
        base_d_coor = (0.0, 0, 2.355)
        self._draw_a_circle(
            self._meter_to_pixel(base_a_coor[0]),
            self._meter_to_pixel(base_a_coor[1]),
            10,
            (0.1, 0.1, 0.9, 1),
        )
        self._draw_a_circle(
            self._meter_to_pixel(base_b_coor[0]),
            self._meter_to_pixel(base_b_coor[1]),
            10,
            (0.1, 0.1, 0.9, 1),
        )
        self._draw_a_circle(
            self._meter_to_pixel(base_c_coor[0]),
            self._meter_to_pixel(base_c_coor[1]),
            10,
            (0.1, 0.1, 0.9, 1),
        )
        self._draw_a_circle(
            self._meter_to_pixel(base_d_coor[0]),
            self._meter_to_pixel(base_d_coor[1]),
            10,
            (0.1, 0.1, 0.9, 1),
        )

        if not USE_BACKEND:
            self.tagPos = [2, 2, 2]
            self.tagBaseDist = [7.777, 7.777, 7.777, 7.777]

            def simulate_data_loop():
                while 1:
                    gen_simulate_data()

            def gen_simulate_data():
                # simulate tagPos change
                for i in range(50000000):
                    pass
                xy_delta = 1
                z_delta = 1
                self.tagPos[0] += random() * xy_delta - xy_delta / 2
                self.tagPos[1] += random() * xy_delta - xy_delta / 2
                self.tagPos[2] += random() * z_delta - z_delta / 2

                # simulate tagBaseDist change
                dist_delta = 1
                for i in range(len(self.tagBaseDist)):
                    self.tagBaseDist[i] += random() * dist_delta - dist_delta / 2

                print("[{:.1f}] Generate simulate data.".format(time.time() % 10000))

            # Clock.schedule_interval(
            #     lambda dt: gen_simulate_data(), self.CLOCK_SCHEDULE_INTERVAL
            # )
            self.backend_thread = Thread(
                target=simulate_data_loop, name="BackendThread"
            )
            self.backend_thread.daemon = True  # thread dies when app is closed
            self.backend_thread.start()

        else:
            lt = backend.lighTagAlgo()
            lt.wifiConnect()
            # # x: A-D, y: A-B
            # lt.setBaseACoor(0, 0, 2.0)
            # lt.setBaseBCoor(0, 8.535, 2.0)
            # lt.setBaseCCoor(5.86, 8.535, 2.0)
            # lt.setBaseDCoor(5.86, 0.0, 2.355)
            lt.setBaseACoor(*base_a_coor)
            lt.setBaseBCoor(*base_b_coor)
            lt.setBaseCCoor(*base_c_coor)
            lt.setBaseDCoor(*base_d_coor)

            def backend_loop():
                while 1:
                    time.sleep(0.1)
                    print(lt.run())

            # Clock.schedule_interval(lambda dt: lt.run(), self.CLOCK_SCHEDULE_INTERVAL)
            self.backend_thread = Thread(target=backend_loop, name="BackendThread")
            self.backend_thread.daemon = True
            self.backend_thread.start()

            self.lt = lt
        print("Starting backend")

    def update_tag_data(self):
        """Update text of tag-base distances label on the window."""
        if not USE_BACKEND:
            # haven't connected to backend, simulate tag's data
            pass
        else:
            # get data from backend
            self.tagBaseDist = self.lt.getDistance()
            self.tagPos = self.lt.getCoor()

        # update tag_distance label
        x, y, z = self.tagPos
        if z is None:
            z = -1
        self.ids.tag_distance.text = "Tag info (m)   Tag location:\nbase1:  {:.2f}        x: {:.1f},\nbase2:  {:.2f}        y: {:.1f},\nbase3:  {:.2f}        z: {:.1f}\nbase4:  {:.2f}".format(
            self.tagBaseDist[0],
            x,
            self.tagBaseDist[1],
            y,
            self.tagBaseDist[2],
            z,
            self.tagBaseDist[3],
        )

        # update floor label
        if self.tagPos[2] is None:
            floor = "N/A"
        elif self.tagPos[2] < self.FIRST_FLOOR_CELLING_HEIGHT:
            floor = "1"
        else:
            floor = "2"
        self.ids.floor_label.text = f"Floor: {floor} L"

        # update colors of floor label & path dots
        self.path_dot_color = self._get_floor_color(floor)
        self.ids.floor_label.color = self._get_floor_color(floor)

        # check whether in the target area
        if len(self.aoi_corners) < 3:
            return
        if self.is_in_the_area(
            (
                self._get_tag_pixel_pos()[0],
                self._get_tag_pixel_pos()[1] + self.ids.control_panel.height,
            ),
            self._get_all_aoi_corners_pos(),
        ):
            self._indicate_tag_in_AOI()
        else:
            self._cancle_tag_in_AOI_indication()

    def _indicate_tag_in_AOI(self):
        """Indicate that tag is within AOI by changing debug button background color."""
        indication_widget = self.ids.debug_btn
        indication_widget.background_color = (79 / 255, 255 / 255, 77 / 255, 1)
        indication_widget.color = (0, 0, 0, 1)
        indication_widget.text = "Target inside the area!"

    def _cancle_tag_in_AOI_indication(self):
        """Cancle the indication that tag is within AOI by changing debug button background color back."""
        indication_widget = self.ids.debug_btn
        indication_widget.background_color = (255 / 255, 13 / 255, 77 / 255, 1)
        indication_widget.color = (1, 1, 1, 1)
        indication_widget.text = "Target outside the area."

    def _get_floor_color(self, floor: str):
        """Get the floor color according to the floor layer."""
        if floor in self.FLOOR_COLORS.keys():
            return self.FLOOR_COLORS[floor]
        else:
            return self.FLOOR_COLORS["default"]

    def _on_settings_pressed(self):
        """Not used yet."""
        # self.ids.settings_btn.background_color = (0, 0, 0, 0)
        self.ids.settings_img.source = "imgs/settings-outline-pressed.png"

    def on_settings_released(self):
        """Not used yet."""
        self.ids.settings_img.source = "imgs/settings-outline.png"

    def add_AOI_corner(self):
        """Callback function for adding a base button to the canvas."""
        corner_id = len(self.aoi_corners) + 1
        new_corner = Button(
            text=str(corner_id),
            font_size=13,
            size_hint=(None, None),
            size=(17, 17),
            pos=(
                0,
                self.ids.control_panel.height,
            ),  # pos of left-bottom corner of the button
            on_release=self._on_base_released,
        )
        self.aoi_corners.append(new_corner)
        self.ids.canvas.add_widget(new_corner)  # add widget to the canvas widget

        # connect the 2 most recent added corners
        if len(self.aoi_corners) >= 2:
            self._create_edge(-1, -2)

        # connect the last corner with the first corner
        if len(self.aoi_corners) >= 3:
            assert (
                len(self.aoi_edges["closing line"]) <= 1
                and len(self.aoi_edges["closing line"]) >= 0
            )

            # remove last closing line
            if len(self.aoi_edges["closing line"]) == 1:
                old_closing_line = list(self.aoi_edges["closing line"].values())[0]
                self.remove_instance_from_canvas(old_closing_line)
                self.aoi_edges["closing line"].clear()

            # create a new closing line
            self._create_edge(0, -1, "closing line")

    def _get_all_aoi_corners_pos(self):
        """Return position of all corners of AOI. e.g., [(330, 220), (220, 330), (0, 250)]"""
        all_corners_pos = []
        for corner in self.aoi_corners:
            all_corners_pos.append(corner.pos)
        return all_corners_pos

    def remove_instance_from_canvas(self, inst):
        self.ids.canvas.canvas.remove(inst)

    def _create_edge(self, start_corner_idx, end_corner_idx, edge_type: str = "normal"):
        """
        Create a edge between the corners of AOI (Area of Interests).
        #Params
        start_corner_idx: index (for 'aoi_corners' array) of the AOI cornor where the edge starts from.
        end_corner_idx: index (for 'aoi_corners' array) of the AOI cornor where the edge ends to.
        edge_type: type of this edge, whether a edge created automatically to close the AOI.
        """
        if edge_type != "normal" and edge_type != "closing line":
            raise ValueError("Edge type can only be 'normal' or 'closing line'.")
        start_corner = self.aoi_corners[start_corner_idx]
        end_corner = self.aoi_corners[end_corner_idx]
        new_edge_name = "{}-{}".format(start_corner.text, end_corner.text)
        new_edge = self._draw_a_line(start_corner.pos, end_corner.pos)
        self.aoi_edges[edge_type][new_edge_name] = new_edge
        return new_edge

    def _draw_a_line(self, start_pos, end_pos):
        color = Color(1, 0, 0, 0.7)
        line = Line(
            points=[*start_pos, *end_pos],
            width=2,
            joint="round",
        )
        self.ids.canvas.canvas.add(color)
        self.ids.canvas.canvas.add(line)

        return line

    def update_edges(self, corner_id):
        """Update all the edges of the AOI (area of interests). Called when path dots' position are changed."""
        for edge_type in self.aoi_edges.keys():
            for edge_name in self.aoi_edges[edge_type].keys():
                curr_edge = self.aoi_edges[edge_type][edge_name]
                curr_corner = self.aoi_corners[int(corner_id) - 1]
                start_corner_id, end_corner_id = self._get_corners_by_edge_name(
                    edge_name
                )
                start_corner_points, end_corner_points = (
                    curr_edge.points[0:2],
                    curr_edge.points[2:4],
                )
                # update the new position of corners
                if start_corner_id == str(corner_id):
                    start_corner_points = curr_corner.pos
                elif end_corner_id == str(corner_id):
                    end_corner_points = curr_corner.pos
                # no update needed, skip the current loop
                else:
                    continue

                # update the edge's position
                curr_edge.points = [*start_corner_points, *end_corner_points]

    def _get_corners_by_edge_name(self, edge_name):
        """Returns if the id of the corners where the edge starts and ends. e.g., ((200, 10), (330, 220))"""
        start_corner_id, end_corner_id = edge_name.split("-")
        return start_corner_id, end_corner_id

    def is_in_the_area(self, target_dot, area_corners) -> bool:
        """
        Return True if the target position is inside the area.

        #Params
        target_dot: (x, y) position of the target dot.
        area_corners: a list of (x, y) position tuple of all the corners of the area. e.g., [(1,2), (2,4), (4,3)]
        """

        def ray_method(xt, yt, x1, y1, x2, y2) -> bool:
            """
            Whether the ray starts from (xt, yt) will cross the line segment with
            endpoints of (x1, y1) & (x2, y2).

            #Param:
            xt, yt: endpoint of the ray.
            x1, y1, x2, y2: the two endpoints of the line segment.

            #Return:
            True if ray crossed the line segment (exclude the lower endpoint).
            """
            # if (xt, yt) on line segment, crossed
            if min(x1, x2) <= xt <= max(x1, x2):
                if y1 == y2:
                    if yt == y1:
                        return True
                else:
                    if xt == (yt - y2) * (x1 - x2) / (y1 - y2) + x2:
                        return True

            # ignore horizontal line segment
            if y1 == y2:
                return False

            # find whether crossing
            # - exclude the situation where crossing on the extension of the line
            #   segment
            if yt < min(y1, y2) or yt > max(y1, y2):
                return False
            xp = (yt - y2) * (x1 - x2) / (y1 - y2) + x2
            # - lower endpoint doesn't count
            lower_endpoint = (x1, y1) if y1 < y2 else (x2, y2)
            if xp == lower_endpoint[0] and yt == lower_endpoint[1]:
                return False

            # - crossed in the middle of the line segment
            return xp >= xt

        cross_times = 0
        for i in range(len(area_corners)):
            x1, y1 = area_corners[i]
            x2, y2 = area_corners[(i + 1) % len(area_corners)]
            if ray_method(*target_dot, x1, y1, x2, y2):
                cross_times += 1
        return (cross_times % 2) == 1

    def _on_base_released(self, base_btn):
        """Callback function for when the base button is released. A popup window will be created."""

        def popup_confirm(confirm_btn):
            """Callback function of confirm button in the base popup window."""
            x = y = z = 0
            if base_x.text.isdigit():
                x = float(base_x.text)
            if base_y.text.isdigit():
                y = float(base_y.text)
            if base_z.text.isdigit():
                z = float(base_z.text)
            # print(x, y, z)
            if x < 0:
                x = 0
            elif x > self.ids.canvas_temp_label.size[0] - 17:
                x = self.ids.canvas_temp_label.size[0] - 17
            if y < 0:
                y = 0
            elif y > self.ids.canvas_temp_label.size[1] - 17:
                y = self.ids.canvas_temp_label.size[1] - 17
            base_btn.pos = [x, y + self.ids.control_panel.height]
            self.ids.canvas.remove_widget(popup)

            # update all edges related to this moved button
            self.update_edges(base_btn.text)

        def delete_base(delete_btn):
            """Callback function of delete button in the base popup window."""
            # def confirm_delete_base(confirm_delete_btn):
            #     self.ids.canvas.remove_widget(doubleCheckPopup)

            # def cancel_delete_base(cancel_delete_btn):
            #     self.ids.canvas.remove_widget(doubleCheckPopup)

            # doubleCheckLayout = BoxLayout(orientation="vertical")
            # doubleCheckLayout.add_widget(
            #     Label(text="Are you sure to delete this base?", font_size=20)
            # )
            # doubleCheckLayout.add_widget(
            #     Button(text="Yes", size_hint=(1, 0.4), on_release=confirm_delete_base)
            # )
            # doubleCheckLayout.add_widget(
            #     Button(text="Cancel", size_hint=(1, 0.4), on_release=cancel_delete_base)
            # )
            # doubleCheckPopup = Popup(
            #     title="Settings",
            #     content=doubleCheckLayout,
            #     size_hint=(None, None),
            #     size=(200, 150),
            #     pos_hint={
            #         "center_x": 0.5,
            #         "center_y": 0.500,
            #     },
            # )
            # self.ids.canvas.add_widget(doubleCheckPopup)
            pass

        # main layout of the popup window
        mainLayout = BoxLayout(orientation="vertical")

        # layout which holds all the position information
        posLayout = GridLayout(cols=2)

        base_x = TextInput(multiline=False, text="0", font_size=10)
        base_y = TextInput(multiline=False, text="0", font_size=10)
        base_z = TextInput(multiline=False, text="0", font_size=10)

        posLayout.add_widget(Label(text="x:"))
        posLayout.add_widget(base_x)
        posLayout.add_widget(Label(text="y:"))
        posLayout.add_widget(base_y)
        posLayout.add_widget(Label(text="z:"))
        posLayout.add_widget(base_z)

        mainLayout.add_widget(posLayout)

        # add confirm button
        mainLayout.add_widget(
            Button(text="Confirm", size_hint=(1, 0.45), on_release=popup_confirm)
        )

        # add delete button
        mainLayout.add_widget(
            Button(
                text="Delete",
                size_hint=(1, 0.45),
                color=(1, 30 / 255, 30 / 255, 1),
                on_release=delete_base,
                disabled=True,
            )
        )

        # add main layout to the popup window
        popup = Popup(
            title="Settings",
            content=mainLayout,
            size_hint=(None, None),
            size=(250, 200),
            pos_hint={"center_x": 0.5, "center_y": 0.5},  # center of father widget
        )

        # add popup to the canvas
        self.ids.canvas.add_widget(popup)

    def debug(self):
        """Print some debug info."""
        # print global positions of all the bases
        print("========= DEBUG messages =========")
        print("Base details:")
        if len(self.aoi_corners) <= 0:
            print("\tNo base yet.")
        else:
            for i in range(len(self.aoi_corners)):
                print(
                    "\t[base {}] pos on window: {}]".format(i, self.aoi_corners[i].pos)
                )
        print()

        # print all drawed circles
        print("Canvas instructions details:")
        for color, circle in self.alive_path_dot_list:
            print("\t{}\n\t{}\n".format(color, circle))
        print()

        # print AOI corners
        print("All AOI corners:")
        for corner in self.aoi_corners:
            print("\t", corner.pos)

        # print target point
        print("Target point:")
        print("\t", self._get_tag_pixel_pos())

    def get_all_AOI_edges(self):
        all_edges = []
        for edge_type in self.aoi_edges.keys():
            for edge in self.aoi_edges[edge_type].values():
                all_edges.append(edge)
        return all_edges

    def on_plot_path_released(self):
        """Callback function of 'plot path' button."""

        def draw_path_callback():
            # draw a circle on the canvas
            new_path_dot_color, new_path_dot = self._draw_a_circle(
                *self._get_tag_pixel_pos()[:2],
                self.PATH_DOT_DIAMETER_IN_PIXEL,
                self.path_dot_color,
            )
            # add circle to alive path dot list
            self.alive_path_dot_list.append((new_path_dot_color, new_path_dot))
            self.update_old_path_dots()

        # IS drawing path, will stop drawing
        if self.draw_path_has_started:
            if self.draw_path_event is None:
                raise ValueError(
                    "draw_path_event is supposed to be a event but None value is detected."
                )
            self.draw_path_event.cancel()
            self.draw_path_has_started = False
            # print("-- Draw path event has been cancelled")
            self.ids.start_plotting_path_btn.text = "START plotting path"
        # is NOT drawing path, will start drawing
        else:
            self.draw_path_event = Clock.schedule_interval(
                lambda dt: draw_path_callback(), 1
            )
            self.draw_path_has_started = True
            # print("-- Draw path event has started")
            self.ids.start_plotting_path_btn.text = "STOP plotting path"

    def _draw_a_circle(self, x, y, d, color=(1, 1, 1, 1)):
        """
        Plot a circle on the canvas.
        #Param
        x: x-coords of the circle on the canvas
        y: y-coords of the circle on the canvas
        d: diameter of the circle
        color: color of the circle
        #Return
        Color of the circle and the circle instance.
        """
        # canvas add new color and circle
        circle_color = Color(*color)
        circle_instance = Ellipse(
            pos=(x, y + self.ids.control_panel.height),
            size=(d, d),
        )
        self.ids.canvas.canvas.add(circle_color)
        self.ids.canvas.canvas.add(circle_instance)

        return circle_color, circle_instance

    def update_old_path_dots(self):
        """Update exists path dots: decrease the opacity of all dots and remove dots with opacity of 0 from alive_path_dot_list."""
        to_be_deleted_dot_idx_list = []
        for i in range(len(self.alive_path_dot_list)):
            curr_circle_color = self.alive_path_dot_list[i][0]
            if curr_circle_color.a <= 0:
                to_be_deleted_dot_idx_list.append(i)
            else:
                curr_circle_color.a -= 1 / self.PATH_DOT_LIFETIME

        for dot_idx in to_be_deleted_dot_idx_list:
            del self.alive_path_dot_list[dot_idx]

    def _get_tag_pixel_pos(self):
        """Get tag position in pixel (unit: meter -> pixel)."""
        pixel_pos = self.tagPos.copy()

        # fix cross borders problem
        for i in range(len(pixel_pos)):
            if pixel_pos[i] is None:
                continue
            if pixel_pos[i] < 0:
                pixel_pos[i] = 0

        for i in range(len(pixel_pos)):
            if pixel_pos[i] is None:
                pixel_pos[i] = -1
            pixel_pos[i] = (
                pixel_pos[i] * 100 / self.CENTIMETER_PER_PIXEL
            )  # m * cm/m / cm/px
        return pixel_pos

    def _meter_to_pixel(self, x):
        return x * 100 / self.CENTIMETER_PER_PIXEL


class UIApp(App):
    def build(self):
        return MainLayout()


if __name__ == "__main__":
    UIApp().run()
