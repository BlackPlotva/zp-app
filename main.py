import os
import re
from kivy.app import App
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
import xlrd


class CustomCard(BoxLayout):

  def __init__(self, bg_color=(0.12, 0.15, 0.23, 1), radius=10, **kwargs):
    super().__init__(**kwargs)
    self.bg_color = bg_color
    self.radius = radius
    with self.canvas.before:
      Color(*self.bg_color)
      self.rect = RoundedRectangle(
          pos=self.pos, size=self.size, radius=[self.radius]
      )
    self.bind(pos=self._update_rect, size=self._update_rect)

  def _update_rect(self, instance, value):
    self.rect.pos = instance.pos
    self.rect.size = instance.size


def parse_schedule_xls(file_path):
  """Парсит XLS файл расписания Запорожской Политехники"""
  if not os.path.exists(file_path):
    return {}, []

  wb_raw = open(file_path, 'rb').read()
  cd = xlrd.compdoc.CompDoc(wb_raw)

  # Извлекаем поток Workbook в обход битых секторов OLE
  def extract_stream(cd_obj, entry):
    sectors = []
    s = entry.first_SID
    sat = cd_obj.SAT
    while 0 <= s < len(sat):
      sectors.append(s)
      s = sat[s]
      if sectors.count(s) > 1:
        break
    data = b''.join(
        cd_obj.mem[512 + sec * cd_obj.sec_size : 512 + (sec + 1) * cd_obj.sec_size]
        for sec in sectors
    )
    return data[: entry.tot_size]

  wb_entry = [d for d in cd.dirlist if d.name == 'Workbook'][0]
  wb_bytes = extract_stream(cd, wb_entry)

  book = xlrd.open_workbook(file_contents=wb_bytes)
  sheet = book.sheet_by_index(0)

  weeks_data = {}  # date_str -> { day_name, slots }
  all_dates = []

  current_day = None
  dates_map = {}

  for r in range(sheet.nrows):
    row = [str(sheet.cell_value(r, c)).strip() for c in range(sheet.ncols)]
    if not any(row):
      continue

    day_code = row[0]
    if day_code in ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд']:
      current_day = day_code
      dates_map = {}
      for c in range(1, len(row)):
        d_val = row[c]
        if d_val:
          dates_map[c] = d_val
          if d_val not in weeks_data:
            weeks_data[d_val] = {'day': day_code, 'slots': []}
            all_dates.append(d_val)

    elif current_day and 'пара' in day_code:
      time_slot = day_code.replace('\n', ' ')
      for c in range(1, len(row)):
        cell_text = row[c]
        if cell_text and c in dates_map:
          target_date = dates_map[c]
          weeks_data[target_date]['slots'].append(
              {'time': time_slot, 'text': cell_text}
          )

  return weeks_data, all_dates


class ScheduleApp(App):

  def build(self):
    self.schedule_data, self.all_dates = parse_schedule_xls(
        'student-time-table (2).xls'
    )
    self.selected_date = self.all_dates[0] if self.all_dates else None

    main_layout = BoxLayout(
        orientation='vertical',
        padding=10,
        spacing=8,
        background_color=(0.07, 0.09, 0.15, 1),
    )

    # Шапка
    header = Label(
        text='🎓 НУ «Запорізька політехніка»',
        font_size='18sp',
        bold=True,
        size_hint_y=None,
        height=35,
        color=(1, 1, 1, 1),
    )
    main_layout.add_widget(header)

    # Панель дат (горизонтальный скролл)
    dates_scroll = ScrollView(
        size_hint_y=None, height=45, do_scroll_x=True, do_scroll_y=False
    )
    self.dates_box = BoxLayout(
        orientation='horizontal', spacing=6, size_hint_x=None
    )
    self.dates_box.bind(minimum_width=self.dates_box.setter('width'))

    self.date_buttons = {}
    for date_str in self.all_dates:
      day_name = self.schedule_data[date_str]['day']
      btn = Button(
          text=f'{day_name}\n{date_str[:5]}',
          size_hint_x=None,
          width=80,
          background_color=(
              (0.2, 0.5, 1, 1)
              if date_str == self.selected_date
              else (0.15, 0.18, 0.26, 1)
          ),
          color=(1, 1, 1, 1),
          font_size='11sp',
      )
      btn.bind(on_release=lambda instance, d=date_str: self.select_date(d))
      self.dates_box.add_widget(btn)
      self.date_buttons[date_str] = btn

    dates_scroll.add_widget(self.dates_box)
    main_layout.add_widget(dates_scroll)

    # Контейнер пар
    self.cards_scroll = ScrollView()
    self.cards_box = BoxLayout(
        orientation='vertical', padding=5, spacing=8, size_hint_y=None
    )
    self.cards_box.bind(minimum_height=self.cards_box.setter('height'))
    self.cards_scroll.add_widget(self.cards_box)
    main_layout.add_widget(self.cards_scroll)

    self.render_lessons()
    return main_layout

  def select_date(self, date_str):
    self.selected_date = date_str
    for d, btn in self.date_buttons.items():
      btn.background_color = (
          (0.2, 0.5, 1, 1) if d == date_str else (0.15, 0.18, 0.26, 1)
      )
    self.render_lessons()

  def render_lessons(self):
    self.cards_box.clear_widgets()

    if not self.selected_date or self.selected_date not in self.schedule_data:
      self.cards_box.add_widget(
          Label(text='Немає пар', color=(0.5, 0.6, 0.7, 1))
      )
      return

    day_info = self.schedule_data[self.selected_date]
    slots = day_info['slots']

    if not slots:
      empty_card = CustomCard(
          orientation='vertical', padding=15, size_hint_y=None, height=60
      )
      empty_card.add_widget(
          Label(
              text='🎉 В цей день пар немає!',
              color=(0.4, 0.8, 0.5, 1),
              bold=True,
          )
      )
      self.cards_box.add_widget(empty_card)
      return

    for slot in slots:
      lines = [l.strip() for l in slot['text'].split('\n') if l.strip()]
      title = lines[0] if len(lines) > 0 else ''
      aud = lines[1] if len(lines) > 1 else ''
      teacher = lines[2] if len(lines) > 2 else ''

      card = CustomCard(
          orientation='horizontal',
          padding=10,
          spacing=10,
          size_hint_y=None,
          height=90,
      )

      # Время
      left = BoxLayout(orientation='vertical', size_hint_x=None, width=90)
      time_parts = slot['time'].split(' ')
      left.add_widget(
          Label(
              text=time_parts[0] if len(time_parts) > 0 else '',
              font_size='11sp',
              color=(0.5, 0.6, 0.7, 1),
          )
      )
      left.add_widget(
          Label(
              text=time_parts[1] if len(time_parts) > 1 else '',
              font_size='12sp',
              bold=True,
              color=(0.3, 0.7, 1, 1),
          )
      )
      card.add_widget(left)

      # Предмет и ауд
      center = BoxLayout(orientation='vertical')
      center.add_widget(
          Label(
              text=title,
              font_size='13sp',
              bold=True,
              halign='left',
              valign='middle',
              text_size=(300, None),
          )
      )
      center.add_widget(
          Label(
              text=f'📍 {aud}   👤 {teacher}',
              font_size='11sp',
              color=(0.7, 0.8, 0.9, 1),
              halign='left',
              valign='middle',
              text_size=(300, None),
          )
      )
      card.add_widget(center)

      self.cards_box.add_widget(card)


if __name__ == '__main__':
  ScheduleApp().run()
