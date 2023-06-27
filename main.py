import cv2
import matplotlib.pyplot as plt
import numpy as np
from kivy import platform
from kivy.core.window import Window
from kivy.garden.matplotlib import FigureCanvasKivyAgg
from kivy.lang import Builder
from kivy.storage.jsonstore import JsonStore
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.app import MDApp
from kivymd.toast import toast
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.list import IRightBodyTouch, OneLineAvatarIconListItem
from kivymd.uix.selectioncontrol import MDSwitch
# Window.minimum_height = 360
# Window.minimum_width = 360
switchValue = False

# OpenCV 4.5.5
# Kivy 2.0.0
# KivyMD 0.104.2
# MatplotLib 3.4.2
# print("OpenCV "+cv2.__version__)
# print("Kivy "+kivy.__version__)
# print("KivyMD "+kivymd.__version__)
# print("MatplotLib "+matplotlib.__version__)
blood = [False, False, False, False]
q = 1
f = 0
v = 0
p1 = ''
p2 = ''
p3 = ''
p4 = ''
imgPath = ''


class MainActivity(Screen):
    processClicked = 0
    selected_path = ''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(on_keyboard=self.events)
        self.choose_selected = int()
        self.manager_open = False
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            ext=[".png", ".jpeg", ".jpg"],
            # preview=True,
        )

    def file_manager_open(self, choose_selected):
        if platform == "android":
            from android.storage import primary_external_storage_path
            primary_ext_storage = primary_external_storage_path()
            self.file_manager.show(primary_ext_storage)
        else:
            self.file_manager.show("/")  # output manager to the screen
        self.manager_open = True
        self.choose_selected = choose_selected

    def select_path(self, path):
        global p1, p2, p3, p4
        self.exit_manager()
        toast(path)
        # self.set_path(path)
        if self.choose_selected == 1:
            p1 = path
            self.image1()
        elif self.choose_selected == 2:
            p2 = path
            self.image2()
        elif self.choose_selected == 3:
            p3 = path
            self.image3()
        else:
            p4 = path
            self.image4()

    def exit_manager(self, *args):
        self.manager_open = False
        self.file_manager.close()

    def events(self, instance, keyboard, keycode, text, modifiers):
        if keyboard in (1001, 27):
            if self.manager_open:
                self.file_manager.back()
        return True

    def image1(self):
        global v
        self.ids.reagAnti_A.source = p1
        if v == 3:
            self.ids.processBtn.disabled = False

    def image2(self):
        global v
        v += 1
        self.ids.reagAnti_B.source = p2
        if v == 3:
            self.ids.processBtn.disabled = False

    def image3(self):
        global v
        v += 1
        self.ids.reagAnti_D.source = p3
        if v == 3:
            self.ids.processBtn.disabled = False

    def image4(self):
        global v
        v += 1
        self.ids.ctrl.source = p4
        if v == 3:
            self.ids.processBtn.disabled = False

    def start(self, p, r):
        global blood
        self.process1(p, r)
        self.process2(p, r)
        self.process3(p, r)
        self.process4(r)
        self.process5(r)
        self.qualification()
        a = self.process7(r)
        print(a, " - ", r)
        if a == 1:
            if r == "Anti A":
                blood[0] = True
            elif r == "Anti B":
                blood[1] = True
            elif r == "Anti D":
                blood[2] = True
            elif r == "Control":
                blood[3] = True

    def process1(self, p, r):  # Extracting the Green plane
        img = cv2.imread(p)
        gi = img[:, :, 1]
        cv2.imwrite("p1" + r + ".png", gi)
        return gi

    def process2(self, p, r):  # Obtaining the threshold
        gi = self.process1(p, r)
        _, th = cv2.threshold(gi, 0, 255, cv2.THRESH_OTSU)
        cv2.imwrite("p2" + r + ".png", th)

    def process3(self, p, r):  # Obtaining Ni black image
        img = cv2.imread('p2' + r + '.png', 0)
        th4 = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 14)
        cv2.imwrite("p3" + r + ".png", th4)

    def process4(self, r):  # Morphology: fill holes
        gi = cv2.imread('p3' + r + '.png', cv2.IMREAD_GRAYSCALE)
        th, gi_th = cv2.threshold(gi, 220, 255, cv2.THRESH_BINARY_INV)
        gi_floodFill = gi_th.copy()
        h, w = gi_th.shape[:2]
        mask = np.zeros((h + 2, w + 2), np.uint8)
        cv2.floodFill(gi_floodFill, mask, (0, 0), 255)
        gi_floodFill_inv = cv2.bitwise_not(gi_floodFill)
        gi_out = gi_th | gi_floodFill_inv
        cv2.imwrite('p4' + r + '.png', gi_out)

    def process5(self, r):  # Morphing To eliminate small objects
        img = cv2.imread('p4' + r + '.png')
        kernel = np.ones((5, 5), np.uint8)
        open = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
        close = cv2.morphologyEx(open, cv2.MORPH_CLOSE, kernel)
        cv2.imwrite('p5' + r + '.png', close)

    def process7(self, r):  # Histogram
        img = cv2.imread('p5' + r + '.png', 10)
        img2 = cv2.imread('p1' + r + '.png', 0)
        mask = np.ones(img.shape[:2], np.uint8)
        hist = cv2.calcHist([img2], [0], mask, [256], [0, 256])
        min = 1000
        max = 0
        n = 0
        s = 0
        ss = 0
        for x, y in enumerate(hist):
            if y > max:
                max = y
            if y < min:
                min = y
            s += y
            n += 1

        mean = s / n
        for x, y in enumerate(hist):
            ss += (y - mean) ** 2
        ss /= n
        sd = abs(ss) ** 0.5
        print(r, "-", sd, "\n")
        if sd < 580:
            return 1
        else:
            return 0

    def start1(self):
        self.start(p1, "Anti A")
        self.start2()

    def start2(self):
        self.start(p2, "Anti B")
        self.start3()

    def start3(self):
        self.start(p3, "Anti D")
        self.start4()
        # self.check()

    def start4(self):
        self.start(p4, "Control")
        self.check()

    dialog = None

    def blood_group_dialog(self, group):
        if not self.dialog:
            self.dialog = MDDialog(
                title="Identified Blood Group! - " + group,
                text=group,
                buttons=[
                    MDRaisedButton(text="Ok!", on_release=self.close_blood_group_dialog)
                ]

            )
        self.dialog.open()

    def close_blood_group_dialog(self, *args):
        self.dialog.dismiss(force=True)

    def check(self):
        if blood[3] == True:
            self.blood_group_dialog("Invalid")
        elif blood[0] is False and blood[1] is False and blood[2] is True and blood[3] is False:
            self.blood_group_dialog("O+")
        elif blood[0] is False and blood[1] is False and blood[2] is False and blood[3] is False:
            self.blood_group_dialog("O-")
        elif blood[0] is True and blood[1] is False and blood[2] is True and blood[3] is False:
            self.blood_group_dialog("A+")
        elif blood[0] is True and blood[1] is False and blood[2] is False and blood[3] is False:
            self.blood_group_dialog("A-")
        elif blood[0] is False and blood[1] is True and blood[2] is True and blood[3] is False:
            self.blood_group_dialog("B+")
        elif blood[0] is False and blood[1] is True and blood[2] is False and blood[3] is False:
            self.blood_group_dialog("B-")
        elif blood[0] is True and blood[1] is True and blood[2] is True and blood[3] is False:
            self.blood_group_dialog("AB+")
        elif blood[0] is True and blood[1] is True and blood[2] is False and blood[3] is False:
            self.blood_group_dialog("AB-")

    def qualification(self):
        global p1, p2, p3, p4
        print(p1 + "\n" + p2 + "\n" + p3 + "\n" + p4)
        img1 = cv2.imread(p1)
        hsv1 = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV)
        cv2.imwrite('p7Anti A.png', hsv1)
        img2 = cv2.imread(p2)
        hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)
        cv2.imwrite('p7Anti B.png', hsv2)
        img3 = cv2.imread(p3)
        hsv3 = cv2.cvtColor(img3, cv2.COLOR_BGR2HSV)
        cv2.imwrite('p7Anti D.png', hsv3)
        img4 = cv2.imread(p4)
        hsv4 = cv2.cvtColor(img4, cv2.COLOR_BGR2HSV)
        cv2.imwrite('p7Control.png', hsv4)


class Process1Activity(Screen):
    def on_enter(self, *args):
        self.ids.p1Anti_A.source = "p1Anti A.png"
        self.ids.p1Anti_B.source = "p1Anti B.png"
        self.ids.p1Anti_D.source = "p1Anti D.png"
        self.ids.p1Control.source = "p1Control.png"


class Process2Activity(Screen):
    def on_enter(self, *args):
        self.ids.p2Anti_A.source = "p2Anti A.png"
        self.ids.p2Anti_B.source = "p2Anti B.png"
        self.ids.p2Anti_D.source = "p2Anti D.png"
        self.ids.p2Control.source = "p2Control.png"


class Process3Activity(Screen):
    def on_enter(self, *args):
        self.ids.p3Anti_A.source = "p3Anti A.png"
        self.ids.p3Anti_B.source = "p3Anti B.png"
        self.ids.p3Anti_D.source = "p3Anti D.png"
        self.ids.p3Control.source = "p3Control.png"


class Process4Activity(Screen):
    def on_enter(self, *args):
        self.ids.p4Anti_A.source = "p4Anti A.png"
        self.ids.p4Anti_B.source = "p4Anti B.png"
        self.ids.p4Anti_D.source = "p4Anti D.png"
        self.ids.p4Control.source = "p4Control.png"


class Process5Activity(Screen):
    def on_enter(self, *args):
        self.ids.p5Anti_A.source = "p5Anti A.png"
        self.ids.p5Anti_B.source = "p5Anti B.png"
        self.ids.p5Anti_D.source = "p5Anti D.png"
        self.ids.p5Control.source = "p5Control.png"


class Process6Activity(Screen):
    def on_enter(self, *args):
        img1 = cv2.imread('p5Anti A.png')
        img2 = cv2.imread('p5Anti B.png')
        img3 = cv2.imread('p5Anti D.png')
        img4 = cv2.imread('p5Control.png')
        color = ('b', 'g', 'r')
        fig, ax = plt.subplots(2, 2)
        for i, col in enumerate(color):
            his1 = cv2.calcHist([img1], [i], None, [256], [0, 256])
            his2 = cv2.calcHist([img2], [i], None, [256], [0, 256])
            his3 = cv2.calcHist([img3], [i], None, [256], [0, 256])
            his4 = cv2.calcHist([img4], [i], None, [256], [0, 256])
            ax[0, 0].plot(his1, color=col)
            ax[0, 1].plot(his2, color=col)
            ax[1, 0].plot(his3, color=col)
            ax[1, 1].plot(his4, color=col)
            plt.xlim([0, 256])
        self.ids.histogram.add_widget(FigureCanvasKivyAgg(plt.gcf()))


class Process7Activity(Screen):

    def on_enter(self, *args):
        self.ids.p7Anti_A.source = "p7Anti A.png"
        self.ids.p7Anti_B.source = "p7Anti B.png"
        self.ids.p7Anti_D.source = "p7Anti D.png"
        self.ids.p7Control.source = "p7Control.png"


class ContentNavigationDrawer(BoxLayout):
    pass


class DarkModeItem(OneLineAvatarIconListItem):
    pass


# ['Red', 'Pink', 'Purple', 'DeepPurple', 'Indigo', 'Blue', 'LightBlue', 'Cyan', 'Teal', 'Green', 'LightGreen',
# 'Lime', 'Yellow', 'Amber', 'Orange', 'DeepOrange', 'Brown', 'Gray', 'BlueGray']

class DarkModeItemContent(IRightBodyTouch, MDSwitch):
    global switchValue

    def changeTheme(self, switchObject, switchValue):
        store = JsonStore("ThemeState.json")
        if not switchValue:
            print(switchValue)
            self.theme_cls.theme_style = "Dark"
            if store.exists('themeState'):
                store.delete('themeState')
                store.put('themeState', switchValue=switchValue)
            else:
                store.put('themeState', switchValue=switchValue)
        else:
            print(switchValue)
            self.theme_cls.theme_style = "Light"
            if store.exists('themeState'):
                store.delete('themeState')
                store.put('themeState', switchValue=switchValue)
            else:
                store.put('themeState', switchValue=switchValue)


class BloodGroup(MDApp):
    manager = ScreenManager()
    dialog = None

    def dialogBox(self):
        if not self.dialog:
            self.dialog = MDDialog(
                title="Confirm Exit?",
                text="This operation will close your application!",
                buttons=[
                    MDFlatButton(text="Cancel", on_release=self.close_dialogBox),
                    MDRaisedButton(text="Confirm", on_release=MDApp.get_running_app().stop)
                ]

            )
        self.dialog.open()

    def close_dialogBox(self, *args):
        self.dialog.dismiss(force=True)

    def build(self):

        return Builder.load_file("main.kv")

    def on_start(self):
        global switchValue
        # print(store.get('themeState')['switchValue'])Purple"
        self.theme_cls.primary_palette = "DeepPurple"
        store = JsonStore("ThemeState.json")
        try:
            switchValue = store.get('themeState')['switchValue']
            print(switchValue)

            if store.get('themeState')['switchValue']:
                self.theme_cls.theme_style = "Dark"
            else:
                self.theme_cls.theme_style = "Light"
        except Exception:
            self.theme_cls.theme_style = "Light"

        if platform == "android":
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])

    def switchCheck(self):
        global switchValue
        store = JsonStore("ThemeState.json")
        try:
            switchValue = store.get('themeState')['switchValue']
        except Exception as e:
            print(e)
        return switchValue

    def on_stop(self):
        global switchValue
        store = JsonStore("ThemeState.json")
        if store.exists('themeState'):
            store.delete('themeState')
        store.put('themeState', switchValue=switchValue)


BloodGroup().run()
