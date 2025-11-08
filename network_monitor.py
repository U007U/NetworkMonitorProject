import tkinter as tk
from tkinter import ttk, messagebox
import psutil
import threading
import time
import json
import os
from datetime import datetime
import requests
import subprocess
import sys

# Импорт speedtest с правильной обработкой ошибок
SPEEDTEST_AVAILABLE = False
try:
    import speedtest

    SPEEDTEST_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ speedtest-cli не установлен: {e}")
except Exception as e:
    print(f"⚠️ Ошибка загрузки speedtest: {e}")


class ModernNetworkMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("🌐 Network Pulse Pro")
        self.root.geometry("1000x700")
        self.root.configure(bg='#1e1e1e')

        # Центрируем окно
        self.center_window()

        # Пытаемся установить иконку
        self.set_window_icon()

        # Цветовая схема
        self.colors = {
            'bg': '#1e1e1e',
            'card_bg': '#2d2d2d',
            'accent': '#00ff88',
            'accent_hover': '#00cc6a',
            'text_primary': '#ffffff',
            'text_secondary': '#b0b0b0',
            'success': '#00ff88',
            'warning': '#ffaa00',
            'error': '#ff4444',
            'online': '#00ff88',
            'offline': '#ff4444'
        }

        self.setup_styles()
        self.setup_ui()
        self.is_monitoring = False

        # Создаем папку для данных
        self.data_dir = os.path.join(os.path.dirname(__file__), 'network_data')
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def center_window(self):
        """Центрирует окно на экране"""
        self.root.update_idletasks()
        width = 1000
        height = 700
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def set_window_icon(self):
        """Устанавливает иконку окна"""
        icon_paths = [
            'network_icon.ico',
            os.path.join(os.path.dirname(__file__), 'network_icon.ico'),
            'icon.ico'
        ]

        for icon_path in icon_paths:
            try:
                if os.path.exists(icon_path):
                    self.root.iconbitmap(icon_path)
                    return
            except:
                continue

    def setup_styles(self):
        """Настраиваем стили для темной темы"""
        style = ttk.Style()
        style.theme_use('clam')

        # Настраиваем цвета для виджетов
        style.configure('TFrame', background=self.colors['bg'])
        style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['text_primary'])
        style.configure('TButton', background=self.colors['accent'], foreground='black')
        style.map('TButton', background=[('active', self.colors['accent_hover'])])

    def setup_ui(self):
        # Главный контейнер
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Заголовок
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill='x', pady=(0, 20))

        title_label = tk.Label(header_frame, text="🌐 NETWORK PULSE PRO",
                               font=('Arial', 24, 'bold'),
                               bg=self.colors['bg'],
                               fg=self.colors['accent'])
        title_label.pack(side='left')

        subtitle_label = tk.Label(header_frame, text="Монитор интернет-соединения",
                                  font=('Arial', 12),
                                  bg=self.colors['bg'],
                                  fg=self.colors['text_secondary'])
        subtitle_label.pack(side='left', padx=(10, 0))

        # Карточка статуса
        self.status_card = self.create_card(main_frame, "📊 ТЕКУЩИЙ СТАТУС")

        # Статус соединения
        status_frame = tk.Frame(self.status_card, bg=self.colors['card_bg'])
        status_frame.pack(fill='x', pady=10)

        self.status_indicator = tk.Label(status_frame, text="●", font=('Arial', 24),
                                         bg=self.colors['card_bg'], fg=self.colors['warning'])
        self.status_indicator.pack(side='left', padx=(0, 10))

        self.status_label = tk.Label(status_frame, text="Проверка соединения...",
                                     font=('Arial', 14, 'bold'),
                                     bg=self.colors['card_bg'],
                                     fg=self.colors['text_primary'])
        self.status_label.pack(side='left')

        # Метрики в сетке
        metrics_frame = tk.Frame(self.status_card, bg=self.colors['card_bg'])
        metrics_frame.pack(fill='x', pady=20)

        # Задержка
        self.ping_widget = self.create_metric(metrics_frame, "⏱️ ЗАДЕРЖКА", "-- мс", 0)

        # Скорость загрузки
        self.download_widget = self.create_metric(metrics_frame, "⬇️ СКАЧИВАНИЕ", "-- Мбит/с", 1)

        # Скорость отдачи
        self.upload_widget = self.create_metric(metrics_frame, "⬆️ ОТПРАВКА", "-- Мбит/с", 2)

        # Использование трафика
        self.usage_widget = self.create_metric(metrics_frame, "📊 ТРАФИК", "-- МБ", 3)

        # Кнопки действий
        buttons_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        buttons_frame.pack(fill='x', pady=20)

        self.monitor_btn = self.create_modern_button(buttons_frame, "🎯 НАЧАТЬ МОНИТОРИНГ",
                                                     self.toggle_monitoring, 0)

        self.speed_btn = self.create_modern_button(buttons_frame, "🚀 ТЕСТ СКОРОСТИ",
                                                   self.run_speed_test, 1)

        self.diagnose_btn = self.create_modern_button(buttons_frame, "🔧 ДИАГНОСТИКА",
                                                      self.run_diagnostics, 2)

        # Предупреждение если speedtest недоступен
        if not SPEEDTEST_AVAILABLE:
            warning_frame = tk.Frame(main_frame, bg=self.colors['bg'])
            warning_frame.pack(fill='x', pady=5)
            warning_label = tk.Label(warning_frame,
                                     text="⚠️ Тест скорости недоступен. Установите: pip install speedtest-cli",
                                     font=('Arial', 10), bg=self.colors['bg'], fg=self.colors['warning'])
            warning_label.pack()

        # Журнал событий
        log_card = self.create_card(main_frame, "📝 ЖУРНАЛ СОБЫТИЙ")

        # Создаем текстовое поле с прокруткой
        log_frame = tk.Frame(log_card, bg=self.colors['card_bg'])
        log_frame.pack(fill='both', expand=True)

        self.log_text = tk.Text(log_frame, height=10, bg='#1a1a1a', fg=self.colors['text_primary'],
                                font=('Consolas', 10), insertbackground=self.colors['text_primary'],
                                relief='flat', borderwidth=0)

        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.pack(side='left', fill='both', expand=True, padx=(0, 5))
        scrollbar.pack(side='right', fill='y')

        # Запускаем обновление статуса
        self.update_network_info()
        self.log_message("✅ Программа запущена", "success")

    def create_card(self, parent, title):
        """Создает карточку с заголовком"""
        card = tk.Frame(parent, bg=self.colors['card_bg'], relief='raised', bd=1)
        card.pack(fill='x', pady=10)

        # Заголовок карточки
        title_label = tk.Label(card, text=title, font=('Arial', 12, 'bold'),
                               bg=self.colors['card_bg'], fg=self.colors['accent'])
        title_label.pack(anchor='w', padx=15, pady=10)

        return card

    def create_metric(self, parent, title, value, column):
        """Создает виджет метрики"""
        frame = tk.Frame(parent, bg=self.colors['card_bg'])
        frame.grid(row=0, column=column, padx=20, sticky='w')

        title_label = tk.Label(frame, text=title, font=('Arial', 10),
                               bg=self.colors['card_bg'], fg=self.colors['text_secondary'])
        title_label.pack(anchor='w')

        value_label = tk.Label(frame, text=value, font=('Arial', 16, 'bold'),
                               bg=self.colors['card_bg'], fg=self.colors['text_primary'])
        value_label.pack(anchor='w')

        return value_label

    def create_modern_button(self, parent, text, command, column):
        """Создает современную кнопку"""
        btn = tk.Button(parent, text=text, command=command,
                        bg=self.colors['accent'], fg='black',
                        font=('Arial', 11, 'bold'),
                        relief='flat', bd=0,
                        padx=20, pady=12,
                        cursor='hand2')
        btn.grid(row=0, column=column, padx=10)

        # Эффект при наведении
        def on_enter(e):
            btn['bg'] = self.colors['accent_hover']

        def on_leave(e):
            btn['bg'] = self.colors['accent']

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

        return btn

    def log_message(self, message, type="info"):
        """Добавляет сообщение в журнал с цветом"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        colors = {
            "success": self.colors['success'],
            "error": self.colors['error'],
            "warning": self.colors['warning'],
            "info": self.colors['text_secondary']
        }

        # Сохраняем текущее состояние
        self.log_text.config(state='normal')

        # Вставляем timestamp
        self.log_text.insert('end', f"[{timestamp}] ", 'timestamp')
        self.log_text.tag_config('timestamp', foreground=self.colors['text_secondary'])

        # Вставляем сообщение с цветом
        self.log_text.insert('end', f"{message}\n", type)
        self.log_text.tag_config(type, foreground=colors.get(type, self.colors['text_primary']))

        # Прокручиваем вниз
        self.log_text.see('end')
        self.log_text.config(state='disabled')

    def update_network_info(self):
        """Обновляет информацию о сети"""
        try:
            # Проверка интернет-соединения
            online = self.check_internet_connection()

            if online:
                self.status_indicator.config(fg=self.colors['online'])
                self.status_label.config(text="СОЕДИНЕНИЕ АКТИВНО ✓", fg=self.colors['online'])
            else:
                self.status_indicator.config(fg=self.colors['offline'])
                self.status_label.config(text="НЕТ СОЕДИНЕНИЯ ✗", fg=self.colors['offline'])

            # Обновляем статистику трафика
            net_io = psutil.net_io_counters()
            bytes_sent = net_io.bytes_sent / (1024 * 1024)
            bytes_recv = net_io.bytes_recv / (1024 * 1024)

            self.usage_widget.config(text=f"↓{bytes_recv:.0f} ↑{bytes_sent:.0f} МБ")

        except Exception as e:
            self.log_message(f"Ошибка обновления: {str(e)}", "error")

        # Планируем следующее обновление
        self.root.after(10000, self.update_network_info)

    def check_internet_connection(self):
        """Проверяет интернет-соединение"""
        try:
            # Пробуем разные методы
            methods = [
                lambda: requests.get("http://www.google.com", timeout=5).status_code == 200,
                lambda: subprocess.run(['ping', '-n', '1', '8.8.8.8'],
                                       capture_output=True, timeout=3).returncode == 0,
                lambda: subprocess.run(['ping', '-n', '1', '1.1.1.1'],
                                       capture_output=True, timeout=3).returncode == 0
            ]

            for method in methods:
                try:
                    if method():
                        return True
                except:
                    continue

            return False
        except:
            return False

    def toggle_monitoring(self):
        """Включает/выключает мониторинг ping"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_btn.config(text="⏸️ ОСТАНОВИТЬ", bg=self.colors['error'])
            self.log_message("Мониторинг ping запущен", "success")
            threading.Thread(target=self.monitor_ping, daemon=True).start()
        else:
            self.is_monitoring = False
            self.monitor_btn.config(text="🎯 НАЧАТЬ МОНИТОРИНГ", bg=self.colors['accent'])
            self.log_message("Мониторинг ping остановлен", "warning")

    def monitor_ping(self):
        """Мониторит ping в реальном времени"""
        while self.is_monitoring:
            try:
                start_time = time.time()
                result = subprocess.run(['ping', '-n', '1', '8.8.8.8'],
                                        capture_output=True, timeout=5)
                ping_time = (time.time() - start_time) * 1000

                if result.returncode == 0:
                    # Определяем цвет по качеству связи
                    if ping_time < 50:
                        color = self.colors['success']
                    elif ping_time < 100:
                        color = self.colors['success']
                    elif ping_time < 200:
                        color = self.colors['warning']
                    else:
                        color = self.colors['error']

                    self.ping_widget.config(text=f"{ping_time:.0f} мс", fg=color)
                else:
                    self.ping_widget.config(text="ТАЙМАУТ", fg=self.colors['error'])

            except Exception as e:
                self.ping_widget.config(text="ОШИБКА", fg=self.colors['error'])

            time.sleep(5)

    def run_speed_test(self):
        """Запускает тест скорости интернета"""
        if not SPEEDTEST_AVAILABLE:
            messagebox.showerror("Ошибка",
                                 "speedtest-cli не установлен!\n\n"
                                 "Установите командой:\n"
                                 "pip install speedtest-cli\n\n"
                                 "Или запустите install.bat для автоматической установки")
            return

        def test():
            try:
                self.speed_btn.config(state='disabled', text="📊 ТЕСТИРУЕМ...")
                self.log_message("Запуск теста скорости...", "info")

                # Сбрасываем показатели
                self.download_widget.config(text="...", fg=self.colors['warning'])
                self.upload_widget.config(text="...", fg=self.colors['warning'])

                st = speedtest.Speedtest()

                self.log_message("Поиск серверов...", "info")
                st.get_servers()

                self.log_message("Выбор лучшего сервера...", "info")
                best = st.get_best_server()
                self.log_message(f"Сервер: {best['name']} ({best['country']})", "success")

                self.log_message("Измерение скорости скачивания...", "info")
                download_speed = st.download() / 1_000_000

                # Оценка скорости скачивания
                if download_speed > 50:
                    dl_color = self.colors['success']
                elif download_speed > 20:
                    dl_color = self.colors['success']
                elif download_speed > 5:
                    dl_color = self.colors['warning']
                else:
                    dl_color = self.colors['error']

                self.download_widget.config(text=f"{download_speed:.1f} Мбит/с", fg=dl_color)

                self.log_message("Измерение скорости отправки...", "info")
                upload_speed = st.upload() / 1_000_000

                # Оценка скорости отправки
                if upload_speed > 10:
                    ul_color = self.colors['success']
                elif upload_speed > 5:
                    ul_color = self.colors['success']
                elif upload_speed > 2:
                    ul_color = self.colors['warning']
                else:
                    ul_color = self.colors['error']

                self.upload_widget.config(text=f"{upload_speed:.1f} Мбит/с", fg=ul_color)

                ping = st.results.ping
                self.ping_widget.config(text=f"{ping:.0f} мс",
                                        fg=self.colors['success'] if ping < 100 else self.colors['warning'])

                # Общая оценка
                overall = "Отличное" if download_speed > 50 and upload_speed > 10 and ping < 50 else \
                    "Хорошее" if download_speed > 20 and upload_speed > 5 and ping < 100 else \
                        "Удовлетворительное" if download_speed > 5 else "Плохое"

                self.log_message(f"Тест завершен! Общая оценка: {overall}", "success")
                self.log_message(
                    f"Результаты: ↓{download_speed:.1f} Мбит/с ↑{upload_speed:.1f} Мбит/с Ping:{ping:.0f}мс", "success")

                # Сохраняем результаты
                self.save_test_result(download_speed, upload_speed, ping, overall)

            except Exception as e:
                error_msg = str(e)
                self.log_message(f"Ошибка теста скорости: {error_msg}", "error")
                self.download_widget.config(text="ОШИБКА", fg=self.colors['error'])
                self.upload_widget.config(text="ОШИБКА", fg=self.colors['error'])
                messagebox.showerror("Ошибка", f"Не удалось выполнить тест скорости:\n{error_msg}")

            finally:
                self.speed_btn.config(state='normal', text="🚀 ТЕСТ СКОРОСТИ")

        threading.Thread(target=test, daemon=True).start()

    def run_diagnostics(self):
        """Запускает полную диагностику сети"""

        def diagnose():
            try:
                self.diagnose_btn.config(state='disabled', text="🔍 ПРОВЕРЯЕМ...")
                self.log_message("Запуск полной диагностики сети...", "info")

                # Проверка основных серверов
                servers = [
                    ('Google DNS', '8.8.8.8'),
                    ('Cloudflare', '1.1.1.1'),
                    ('Yandex DNS', '77.88.8.8'),
                    ('Google', 'google.com'),
                    ('Cloudflare DNS', '1.0.0.1')
                ]

                working_servers = 0
                for name, address in servers:
                    try:
                        start_time = time.time()
                        result = subprocess.run(['ping', '-n', '2', address],
                                                capture_output=True, timeout=5)
                        ping_time = (time.time() - start_time) * 1000

                        if result.returncode == 0:
                            self.log_message(f"{name}: {ping_time:.0f} мс ✓", "success")
                            working_servers += 1
                        else:
                            self.log_message(f"{name}: Таймаут ✗", "error")
                    except:
                        self.log_message(f"{name}: Ошибка ✗", "error")

                # Результаты диагностики
                success_rate = (working_servers / len(servers)) * 100
                if success_rate > 80:
                    conclusion = "Отличное качество связи"
                    color = "success"
                elif success_rate > 50:
                    conclusion = "Удовлетворительное качество связи"
                    color = "warning"
                else:
                    conclusion = "Проблемы с соединением"
                    color = "error"

                self.log_message(f"Диагностика завершена: {working_servers}/{len(servers)} серверов доступно", color)
                self.log_message(f"Заключение: {conclusion}", color)

            except Exception as e:
                self.log_message(f"Ошибка диагностики: {str(e)}", "error")
            finally:
                self.diagnose_btn.config(state='normal', text="🔧 ДИАГНОСТИКА")

        threading.Thread(target=diagnose, daemon=True).start()

    def save_test_result(self, download, upload, ping, quality):
        """Сохраняет результаты теста"""
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'download': download,
                'upload': upload,
                'ping': ping,
                'quality': quality
            }

            filename = os.path.join(self.data_dir, f"speedtest_{datetime.now().strftime('%Y%m%d')}.json")

            # Загружаем существующие данные
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            else:
                existing_data = []

            existing_data.append(data)

            # Сохраняем только последние 50 результатов
            if len(existing_data) > 50:
                existing_data = existing_data[-50:]

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)

            self.log_message(f"Результаты сохранены", "success")

        except Exception as e:
            self.log_message(f"Ошибка сохранения: {str(e)}", "error")


if __name__ == "__main__":
    # Проверяем необходимые библиотеки
    try:
        import psutil
        import requests
    except ImportError as e:
        print("Установите необходимые библиотеки:")
        print("pip install psutil requests")
        input("Нажмите Enter для выхода...")
        sys.exit(1)

    # Создаем и запускаем приложение
    root = tk.Tk()
    app = ModernNetworkMonitor(root)
    root.mainloop()
