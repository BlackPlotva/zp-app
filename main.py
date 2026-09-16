import datetime
import urllib.request
import urllib.parse
import threading
import os
import xlrd

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock

TARGET_URL = "https://portal.zp.edu.ua/time-table/student?type=0"
LOCAL_FILE = "student-time-table.xls"

FORM_DATA = {
    'TimeTableForm[facultyId]': '79',
    'TimeTableForm[course]': '1',
    'TimeTableForm[groupId]': '4746',
    'TimeTableForm[studentId]': '35746'
}

class AutoScheduleApp(App):
    def build(self):
        Window.clearcolor = (0.95, 0.96, 0.98, 1)
        self.main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)

        self.status_label = Label(
            text="🔄 Подключение к portal.zp.edu.ua...",
            font_size='12sp', color=(0.4, 0.4, 0.4, 1),
            size_hint_y=None, height=20
        )
        self.main_layout.add_widget(self.status_label)

        self.header = Label(
            text="🎓 Розклад занять\n[size=14]Кунах К. А. | БТЕ-0816[/size]",
            markup=True, font_size='20sp', bold=True,
            color=(0.15, 0.38, 0.92, 1), size_hint_y=None, height=70, halign='center'
        )
        self.main_layout.add_widget(self.header)

        self.scroll = ScrollView(size_hint=(1, 1))
        self.content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=15)
        self.content.bind(minimum_height=self.content.setter('height'))
        self.scroll.add_widget(self.content)
        self.main_layout.add_widget(self.scroll)

        if os.path.exists(LOCAL_FILE):
            self.parse_and_display()

        threading.Thread(target=self.fetch_from_portal, daemon=True).start()
        return self.main_layout

    def fetch_from_portal(self):
        try:
            encoded_data = urllib.parse.urlencode(FORM_DATA).encode('utf-8')
            req = urllib.request.Request(
                TARGET_URL,
                data=encoded_data,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    with open(LOCAL_FILE, 'wb') as f:
                        f.write(response.read())
                    Clock.schedule_once(lambda dt: self.on_success())
        except Exception:
            Clock.schedule_once(lambda dt: self.on_error())

    def on_success(self):
        self.status_label.text = "✅ Синхронизировано с порталом НУ «ЗП»"
        self.parse_and_display()

    def on_error(self):
        if os.path.exists(LOCAL_FILE):
            self.status_label.text = "📡 Офлайн-режим (сохраненная копия)"
        else:
            self.status_label.text = "❌ Ошибка подключения к порталу"

    def parse_and_display(self):
        try:
            book = xlrd.open_workbook(LOCAL_FILE, ignore_workbook_corruption=True)
            sheet = book.sheet_by_index(0)
            
            parsed_days = []
            current_day = None

            for i in range(sheet.nrows):
                row = [str(sheet.cell_value(i, j)).strip() for j in range(sheet.ncols)]
                if row[0] in ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб']:
                    current_day = {"day": row[0], "dates": row[1:], "lessons": []}
                    parsed_days.append(current_day)
                elif current_day and 'пара' in row[0]:
                    time_part = row[0].split('\n')[-1] if '\n' in row[0] else row[0]
                    current_day["lessons"].append((time_part, row[1:]))

            self.render_ui(parsed_days)
        except Exception:
            self.status_label.text = "⚠️ Ошибка обработки файла расписания"

    def render_ui(self, schedule_data):
        self.content.clear_widgets()
        today_str = datetime.datetime.now().strftime("%d.%m.%Y")

        for day_info in schedule_data:
            day_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
            day_box.bind(minimum_height=day_box.setter('height'))

            day_title = Label(
                text=f"📅 {day_info['day']}", font_size='16sp', bold=True,
                color=(0.1, 0.1, 0.1, 1), size_hint_y=None, height=35, halign='left'
            )
            day_title.bind(size=day_title.setter('text_size'))
            day_box.add_widget(day_title)

            week_idx = 0
            for idx, d_str in enumerate(day_info['dates']):
                if d_str == today_str:
                    week_idx = idx
                    break

            for time_str, lesson_options in day_info['lessons']:
                lesson_text = lesson_options[week_idx] if week_idx < len(lesson_options) else ""
                if lesson_text:
                    card = BoxLayout(orientation='vertical', size_hint_y=None, height=75, padding=8)
                    time_lbl = Label(
                        text=f"⏰ {time_str}", font_size='12sp', bold=True,
                        color=(0.15, 0.38, 0.92, 1), size_hint_y=None, height=20, halign='left'
                    )
                    time_lbl.bind(size=time_lbl.setter('text_size'))
                    
                    details_lbl = Label(
                        text=lesson_text, font_size='12sp', color=(0.2, 0.2, 0.2, 1),
                        size_hint_y=None, height=45, halign='left'
                    )
                    details_lbl.bind(size=details_lbl.setter('text_size'))

                    card.add_widget(time_lbl)
                    card.add_widget(details_lbl)
                    day_box.add_widget(card)

            self.content.add_widget(day_box)

if __name__ == '__main__':
    AutoScheduleApp().run()