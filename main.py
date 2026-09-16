import io
import requests
import xlrd
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView


class ScheduleApp(App):

  def build(self):
    layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

    self.status_label = Label(
        text='Нажмите кнопку для загрузки расписания',
        size_hint_y=None,
        height=40,
    )
    layout.add_widget(self.status_label)

    btn = Button(
        text='Загрузить расписание (БТЕ-0816)', size_hint_y=None, height=50
    )
    btn.bind(on_press=self.load_schedule)
    layout.add_widget(btn)

    self.scroll = ScrollView()
    self.content_layout = BoxLayout(
        orientation='vertical', size_hint_y=None, spacing=5
    )
    self.content_layout.bind(
        minimum_height=self.content_layout.setter('height')
    )
    self.scroll.add_widget(self.content_layout)
    layout.add_widget(self.scroll)

    return layout

  def load_schedule(self, instance):
    self.status_label.text = 'Скачивание расписания...'
    # URL портала ZP Polytechnic
    url = 'https://portal.zp.edu.ua/'  # Укажите прямую ссылку на .xls файл расписания

    try:
      response = requests.get(url, timeout=10)
      if response.status_code == 200:
        # Открываем скачанный .xls прямо из оперативной памяти
        workbook = xlrd.open_workbook(file_contents=response.content)
        sheet = workbook.sheet_by_index(0)

        self.content_layout.clear_widgets()
        for row_idx in range(min(50, sheet.nrows)):
          row_values = [str(cell) for cell in sheet.row_values(row_idx) if cell]
          if row_values:
            text = ' | '.join(row_values)
            lbl = Label(
                text=text,
                size_hint_y=None,
                height=30,
                color=(1, 1, 1, 1),
            )
            self.content_layout.add_widget(lbl)

        self.status_label.text = 'Расписание успешно загружено!'
      else:
        self.status_label.text = (
            f'Ошибка сервера: код {response.status_code}'
        )
    except Exception as e:
      self.status_label.text = f'Ошибка при загрузке: {str(e)}'


if __name__ == '__main__':

  ScheduleApp().run()
