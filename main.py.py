from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.slider import Slider
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.logger import Logger
from kivy.utils import platform
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
# Import untuk Bluetooth Android
print(platform)
if platform == 'android':
    from android.permissions import request_permissions, Permission
    from jnius import autoclass, cast
    # request_permissions(
    #     [
    #         Permission.READ_EXTERNAL_STORAGE,
    #         Permission.WRITE_EXTERNAL_STORAGE,
    #         Permission.BLUETOOTH_CONNECT,
    #         Permission.Permission.BLUETOOTH_SCAN
    #     ]
    # )
    
    # Java classes untuk Bluetooth Android
    BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
    BluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')
    BluetoothSocket = autoclass('android.bluetooth.BluetoothSocket')
    UUID = autoclass('java.util.UUID')
    InputStream = autoclass('java.io.InputStream')
    OutputStream = autoclass('java.io.OutputStream')
    Intent = autoclass('android.content.Intent')
    Activity = autoclass('org.kivy.android.PythonActivity').mActivity
    
else:
    # Untuk testing di desktop
    import serial
    import threading
    import time

class MicrobitDashboard(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(10)
        
        # Header
        header = BoxLayout(size_hint=(1, 0.12))
        header_label = Label(
            text='SMART CLASSROOM\nSMAN 4 HALBAR',
            font_size='18sp',
            bold=True,
            color=(0.9, 0.9, 0.9, 1),  # Warna teks diubah menjadi terang
            halign='center',
            valign='middle'
        )
        header_label.bind(size=header_label.setter('text_size'))
        header.add_widget(header_label)
        self.add_widget(header)
        
        # Status koneksi
        self.connection_status = Label(
            text='Status: Tidak Terhubung',
            size_hint=(1, 0.08),
            font_size='14sp',
            color=(1, 0.5, 0.5, 1)  # Warna diubah untuk kontras dengan latar hitam
        )
        self.add_widget(self.connection_status)
        
        # ScrollView untuk konten utama
        scroll = ScrollView(size_hint=(1, 0.8))
        main_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        main_layout.bind(minimum_height=main_layout.setter('height'))
        
        # Panel utama dengan grid layout
        main_grid = GridLayout(cols=1, rows=4, spacing=dp(15), size_hint_y=None)
        main_grid.bind(minimum_height=main_grid.setter('height'))
        
        # Panel Suhu
        temp_panel = BoxLayout(orientation='vertical', spacing=dp(5), size_hint_y=None, height=dp(180))
        temp_panel.add_widget(Label(text='SUHU RUANGAN', font_size='16sp', bold=True, size_hint_y=0.2, color=(0.9, 0.9, 0.9, 1)))
        
        self.temp_value = Label(text='0.0°C', font_size='28sp', color=(1, 0.5, 0.5, 1), size_hint_y=0.3)
        temp_panel.add_widget(self.temp_value)
        
        temp_panel.add_widget(Label(text='Threshold Suhu:', font_size='14sp', size_hint_y=0.15, color=(0.9, 0.9, 0.9, 1)))
        
        threshold_layout = BoxLayout(orientation='horizontal', size_hint_y=0.2)
        self.threshold_slider = Slider(min=18, max=35, value=22, step=1, size_hint_x=0.7)
        self.threshold_slider.bind(value=self.on_threshold_change)
        threshold_layout.add_widget(self.threshold_slider)
        
        self.threshold_label = Label(text='22°C', size_hint_x=0.3, color=(0.9, 0.9, 0.9, 1))
        threshold_layout.add_widget(self.threshold_label)
        
        temp_panel.add_widget(threshold_layout)
        main_grid.add_widget(temp_panel)
        
        # Panel Keberadaan Siswa
        presence_panel = BoxLayout(orientation='vertical', spacing=dp(5), size_hint_y=None, height=dp(150))
        presence_panel.add_widget(Label(text='KEBERADAAN SISWA', font_size='16sp', bold=True, size_hint_y=0.3, color=(0.9, 0.9, 0.9, 1)))
        
        presence_content = BoxLayout(orientation='horizontal', size_hint_y=0.7)
        self.presence_icon = Label(text='❌', font_size='40sp')
        presence_content.add_widget(self.presence_icon)
        
        presence_text_layout = BoxLayout(orientation='vertical')
        self.presence_text = Label(text='Tidak Ada', font_size='16sp', color=(1, 0.5, 0.5, 1))
        presence_text_layout.add_widget(self.presence_text)
        presence_content.add_widget(presence_text_layout)
        
        presence_panel.add_widget(presence_content)
        main_grid.add_widget(presence_panel)
        
        # Panel Pencahayaan
        light_panel = BoxLayout(orientation='vertical', spacing=dp(5), size_hint_y=None, height=dp(180))
        light_panel.add_widget(Label(text='PENCAHAYAAN', font_size='16sp', bold=True, size_hint_y=0.2, color=(0.9, 0.9, 0.9, 1)))
        
        self.light_value = Label(text='0', font_size='28sp', color=(0.5, 1, 0.5, 1), size_hint_y=0.2)
        light_panel.add_widget(self.light_value)
        
        self.light_bar = ProgressBar(max=1023, value=0, size_hint_y=0.2)
        light_panel.add_widget(self.light_bar)
        
        # Status perangkat
        status_layout = GridLayout(cols=2, rows=1, size_hint_y=0.4)
        
        # Status Lampu
        light_status_panel = BoxLayout(orientation='vertical')
        light_status_panel.add_widget(Label(text='Lampu:', font_size='14sp', color=(0.9, 0.9, 0.9, 1)))
        self.light_status = Label(text='MATI', font_size='14sp', color=(1, 0.5, 0.5, 1))
        light_status_panel.add_widget(self.light_status)
        status_layout.add_widget(light_status_panel)
        
        # Status Kipas
        fan_status_panel = BoxLayout(orientation='vertical')
        fan_status_panel.add_widget(Label(text='Kipas:', font_size='14sp', color=(0.9, 0.9, 0.9, 1)))
        self.fan_status = Label(text='MATI', font_size='14sp', color=(1, 0.5, 0.5, 1))
        fan_status_panel.add_widget(self.fan_status)
        status_layout.add_widget(fan_status_panel)
        
        light_panel.add_widget(status_layout)
        main_grid.add_widget(light_panel)
        
        # Panel Kontrol
        control_panel = BoxLayout(orientation='vertical', spacing=dp(5), size_hint_y=None, height=dp(180))
        control_panel.add_widget(Label(text='KONTROL KELAS', font_size='16sp', bold=True, size_hint_y=0.2, color=(0.9, 0.9, 0.9, 1)))
        
        # Tombol koneksi Bluetooth
        self.connect_btn = ToggleButton(
            text='Sambungkan ke Micro:bit',
            font_size='14sp',
            size_hint_y=0.3,
            background_color=(0.3, 0.3, 0.3, 1),
            color=(0.9, 0.9, 0.9, 1)
        )
        self.connect_btn.bind(on_press=self.toggle_connection)
        control_panel.add_widget(self.connect_btn)
        
        # Tombol kontrol manual
        manual_ctrl = GridLayout(cols=2, rows=1, size_hint_y=0.5, spacing=dp(10))
        self.light_btn = ToggleButton(text='Manual\nLampu', font_size='12sp', background_color=(0.3, 0.3, 0.3, 1), color=(0.9, 0.9, 0.9, 1))
        self.light_btn.bind(on_press=self.toggle_light)
        manual_ctrl.add_widget(self.light_btn)
        
        self.fan_btn = ToggleButton(text='Manual\nKipas', font_size='12sp', background_color=(0.3, 0.3, 0.3, 1), color=(0.9, 0.9, 0.9, 1))
        self.fan_btn.bind(on_press=self.toggle_fan)
        manual_ctrl.add_widget(self.fan_btn)
        
        control_panel.add_widget(manual_ctrl)
        main_grid.add_widget(control_panel)
        
        main_layout.add_widget(main_grid)
        scroll.add_widget(main_layout)
        self.add_widget(scroll)
        
        # Variabel untuk koneksi Bluetooth
        self.bluetooth_adapter = None
        self.bluetooth_socket = None
        self.input_stream = None
        self.output_stream = None
        self.connected = False
        self.running = False
        
        # Data dari Micro:bit
        self.light_data = 0
        self.temperature_data = 0
        self.teachable_machine_data = "kosong"
        self.temperature_threshold = 22
        
        # Request permissions untuk Android
        if platform == 'android':
            self.request_android_permissions()
        
        # Jadwalkan pembaruan UI
        Clock.schedule_interval(self.update_ui, 0.5)
        
        # Set latar belakang hitam untuk semua panel
        self.set_background_color()
        
    def set_background_color(self):
        """Mengatur warna latar belakang hitam untuk semua komponen"""
        # Set warna latar belakang utama
        Window.clearcolor = (0, 0, 0, 1)  # Hitam
        
        # Set warna latar untuk panel utama
        self.background_color = (0.1, 0.1, 0.1, 1)
        
    def request_android_permissions(self):
        """Request permissions Bluetooth untuk Android"""
        def callback(permissions, results):
            if all(results):
                Logger.info("Bluetooth: Semua permissions diberikan")
                self.setup_bluetooth()
            else:
                Logger.error("Bluetooth: Permissions ditolak")
                self.show_error("Izin Bluetooth diperlukan untuk aplikasi ini")
        
        request_permissions([Permission.ACCESS_COARSE_LOCATION, 
                           Permission.ACCESS_FINE_LOCATION,
                           Permission.BLUETOOTH,
                           Permission.BLUETOOTH_ADMIN], callback)
    
    def setup_bluetooth(self):
        """Setup Bluetooth adapter di Android"""
        try:
            self.bluetooth_adapter = BluetoothAdapter.getDefaultAdapter()
            if self.bluetooth_adapter is None:
                self.show_error("Perangkat tidak mendukung Bluetooth")
                return
            
            if not self.bluetooth_adapter.isEnabled():
                # Minta user untuk mengaktifkan Bluetooth
                enable_intent = Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE)
                Activity.startActivityForResult(enable_intent, 0)
                Logger.info("Bluetooth: Meminta user mengaktifkan Bluetooth")
                
        except Exception as e:
            Logger.error(f"Bluetooth: Error setup: {str(e)}")
            self.show_error(f"Error setup Bluetooth: {str(e)}")
    
    def toggle_connection(self, instance):
        if instance.state == 'down':
            self.connect_to_microbit()
        else:
            self.disconnect_from_microbit()
    
    def connect_to_microbit(self):
        """Connect ke Micro:bit via Bluetooth"""
        try:
            if platform == 'android':
                # Untuk Android - connect via Bluetooth
                microbit_name = "BBC micro:bit"  # Nama default Micro:bit
                
                # Cari perangkat Micro:bit
                paired_devices = self.bluetooth_adapter.getBondedDevices()
                microbit_device = None
                
                for device in paired_devices:
                    if microbit_name in device.getName():
                        microbit_device = device
                        break
                
                if microbit_device is None:
                    self.show_error("Micro:bit tidak ditemukan. Pastikan sudah dipaired.")
                    self.connect_btn.state = 'normal'
                    return
                
                # UUID untuk UART service di Micro:bit
                uuid = UUID.fromString("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
                self.bluetooth_socket = microbit_device.createRfcommSocketToServiceRecord(uuid)
                self.bluetooth_socket.connect()
                
                self.input_stream = self.bluetooth_socket.getInputStream()
                self.output_stream = self.bluetooth_socket.getOutputStream()
                
                self.running = True
                # Start thread untuk membaca data
                from threading import Thread
                self.read_thread = Thread(target=self.read_bluetooth_data)
                self.read_thread.daemon = True
                self.read_thread.start()
                
                self.connected = True
                self.connection_status.text = "Status: Terhubung ke Micro:bit"
                self.connection_status.color = (0.5, 1, 0.5, 1)
                self.connect_btn.text = "Putuskan Koneksi"
                
            else:
                # Untuk desktop - menggunakan serial (hanya untuk testing)
                self.serial_connection = serial.Serial('COM3', 115200, timeout=1)
                self.running = True
                import threading
                self.serial_thread = threading.Thread(target=self.read_serial_data)
                self.serial_thread.daemon = True
                self.serial_thread.start()
                
                self.connected = True
                self.connection_status.text = "Status: Terhubung (Serial)"
                self.connection_status.color = (0.5, 1, 0.5, 1)
                self.connect_btn.text = "Putuskan Koneksi"
                
        except Exception as e:
            Logger.error(f"Koneksi gagal: {str(e)}")
            self.show_error(f"Koneksi gagal: {str(e)}")
            self.connect_btn.state = 'normal'
    
    def read_bluetooth_data(self):
        """Membaca data dari Bluetooth socket (Android)"""
        buffer = bytearray(1024)
        while self.running:
            try:
                if self.input_stream and self.input_stream.available() > 0:
                    bytes_read = self.input_stream.read(buffer)
                    if bytes_read > 0:
                        line = buffer[:bytes_read].decode('utf-8').strip()
                        self.process_received_data(line)
            except Exception as e:
                Logger.error(f"Error membaca Bluetooth: {str(e)}")
                Clock.schedule_once(lambda dt: self.disconnect_from_microbit())
                break
    
    def read_serial_data(self):
        """Membaca data dari serial (desktop only)"""
        while self.running:
            try:
                if self.serial_connection and self.serial_connection.in_waiting > 0:
                    line = self.serial_connection.readline().decode('utf-8').strip()
                    self.process_received_data(line)
            except Exception as e:
                Logger.error(f"Error membaca serial: {str(e)}")
                import time
                time.sleep(0.1)
    
    def process_received_data(self, line):
        """Memproses data yang diterima dari Micro:bit"""
        Logger.info(f"Data diterima: {line}")
        
        if line.startswith("lightData:"):
            try:
                self.light_data = int(line.split(":")[1].strip())
            except:
                pass
        elif line.startswith("temperatureData:"):
            try:
                self.temperature_data = float(line.split(":")[1].strip())
            except:
                pass
        elif line.startswith("teachableMachineData:"):
            try:
                self.teachable_machine_data = line.split(":")[1].strip()
            except:
                pass
        elif line.startswith("threshold:"):
            try:
                self.temperature_threshold = int(line.split(":")[1].strip())
                # Update UI di main thread
                Clock.schedule_once(lambda dt: self.update_threshold_ui())
            except:
                pass
    
    def update_threshold_ui(self):
        """Update UI threshold di main thread"""
        self.threshold_slider.value = self.temperature_threshold
        self.threshold_label.text = f"{self.temperature_threshold}°C"
    
    def disconnect_from_microbit(self):
        """Disconnect dari Micro:bit"""
        try:
            self.running = False
            if platform == 'android':
                if self.bluetooth_socket:
                    self.bluetooth_socket.close()
            else:
                if self.serial_connection:
                    self.serial_connection.close()
                    
            self.connected = False
            self.connection_status.text = "Status: Tidak Terhubung"
            self.connection_status.color = (1, 0.5, 0.5, 1)
            self.connect_btn.text = "Sambungkan ke Micro:bit"
            self.connect_btn.state = 'normal'
            
        except Exception as e:
            Logger.error(f"Error saat memutuskan: {str(e)}")
            self.show_error(f"Error saat memutuskan: {str(e)}")
    
    def send_command(self, command):
        """Mengirim perintah ke Micro:bit"""
        try:
            if platform == 'android' and self.output_stream:
                self.output_stream.write(f"{command}\n".encode('utf-8'))
                self.output_stream.flush()
            elif not platform == 'android' and self.serial_connection:
                self.serial_connection.write(f"{command}\n".encode('utf-8'))
        except Exception as e:
            Logger.error(f"Error mengirim perintah: {str(e)}")
    
    def toggle_light(self, instance):
        if instance.state == 'down':
            self.send_command("LIGHT_ON")
            self.light_status.text = "NYALA (Manual)"
            self.light_status.color = (0.5, 1, 0.5, 1)
        else:
            self.send_command("LIGHT_OFF")
            self.light_status.text = "MATI (Manual)"
            self.light_status.color = (1, 0.5, 0.5, 1)
    
    def toggle_fan(self, instance):
        if instance.state == 'down':
            self.send_command("FAN_ON")
            self.fan_status.text = "NYALA (Manual)"
            self.fan_status.color = (0.5, 1, 0.5, 1)
        else:
            self.send_command("FAN_OFF")
            self.fan_status.text = "MATI (Manual)"
            self.fan_status.color = (1, 0.5, 0.5, 1)
    
    def on_threshold_change(self, instance, value):
        self.threshold_label.text = f"{int(value)}°C"
        self.send_command(f"THRESHOLD:{int(value)}")
    
    def update_ui(self, dt):
        # Update temperature
        self.temp_value.text = f"{self.temperature_data:.1f}°C"
        
        # Update presence status
        if self.teachable_machine_data == "ada":
            self.presence_icon.text = '✅'
            self.presence_text.text = 'Ada Siswa'
            self.presence_text.color = (0.5, 1, 0.5, 1)
        else:
            self.presence_icon.text = '❌'
            self.presence_text.text = 'Tidak Ada'
            self.presence_text.color = (1, 0.5, 0.5, 1)
        
        # Update light level
        self.light_value.text = f"{self.light_data}"
        self.light_bar.value = self.light_data
        
        # Update lampu status (auto mode)
        if self.teachable_machine_data == "ada" and self.light_data < 400:
            if self.light_btn.state != 'down':  # Only update if not in manual mode
                self.light_status.text = "NYALA (Auto)"
                self.light_status.color = (0.5, 1, 0.5, 1)
        else:
            if self.light_btn.state != 'down':  # Only update if not in manual mode
                self.light_status.text = "MATI (Auto)"
                self.light_status.color = (1, 0.5, 0.5, 1)
                
        # Update kipas status (auto mode)
        if self.teachable_machine_data == "ada" and self.temperature_data > self.temperature_threshold:
            if self.fan_btn.state != 'down':  # Only update if not in manual mode
                self.fan_status.text = "NYALA (Auto)"
                self.fan_status.color = (0.5, 1, 0.5, 1)
        else:
            if self.fan_btn.state != 'down':  # Only update if not in manual mode
                self.fan_status.text = "MATI (Auto)"
                self.fan_status.color = (1, 0.5, 0.5, 1)
    
    def show_error(self, message):
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        content.add_widget(Label(text=message, size_hint_y=0.6, color=(0, 0, 0, 1)))
        btn = Button(text='Tutup', size_hint_y=0.4)
        content.add_widget(btn)
        
        popup = Popup(title='Error', content=content, size_hint=(0.8, 0.4))
        btn.bind(on_press=popup.dismiss)
        popup.open()

class SmartClassroomApp(App):
    def build(self):
        Window.clearcolor = (0, 0, 0, 1)  # Latar belakang hitam
        return MicrobitDashboard()

if __name__ == '__main__':
    SmartClassroomApp().run()