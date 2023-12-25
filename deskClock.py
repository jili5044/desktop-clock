import sys
import json
from PyQt5.QtWidgets import (QApplication, QLabel, QMainWindow, QDialog,
                             QVBoxLayout, QPushButton, QColorDialog,
                             QSlider, QComboBox, QMenu, QCheckBox, QSystemTrayIcon, QAction, QFontComboBox)
from PyQt5.QtCore import QTimer, QTime, Qt
from PyQt5.QtGui import QFont, QColor, QIcon


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Font size slider
        self.fontSizeSlider = QSlider(Qt.Horizontal)
        self.fontSizeSlider.setMinimum(10)
        self.fontSizeSlider.setMaximum(50)
        self.fontSizeSlider.setValue(self.parent().fontSize)
        self.fontSizeSlider.valueChanged.connect(self.parent().setFontSize)
        layout.addWidget(self.fontSizeSlider)

        # Color picker button
        self.colorButton = QPushButton('Choose Font Color', self)
        self.colorButton.clicked.connect(self.parent().chooseColor)
        layout.addWidget(self.colorButton)

        # 字体选择下拉框
        self.fontComboBox = QFontComboBox(self)
        self.fontComboBox.setCurrentFont(QFont(self.parent().fontFamily))
        self.fontComboBox.currentFontChanged.connect(self.parent().setFontFamily)
        layout.addWidget(self.fontComboBox)

        # Time format combobox
        self.formatComboBox = QComboBox(self)
        self.formatComboBox.addItems(['hh:mm:ss AP', 'HH:mm:ss'])
        self.formatComboBox.setCurrentIndex(1 if self.parent().is24Hour else 0)
        self.formatComboBox.currentIndexChanged.connect(self.parent().setTimeFormat)
        layout.addWidget(self.formatComboBox)

        # CheckBox for showing seconds
        self.showSecondsCheckBox = QCheckBox("Show Seconds", self)
        self.showSecondsCheckBox.setChecked(self.parent().showSeconds)
        self.showSecondsCheckBox.stateChanged.connect(self.parent().setShowSeconds)
        layout.addWidget(self.showSecondsCheckBox)


class TransparentClock(QMainWindow):
    def __init__(self):
        super(TransparentClock, self).__init__()
        self.fontSize = 25
        self.fontColor = '#00aa7f'
        self.is24Hour = 1
        self.showSeconds = True
        self.isSettingsDialog = False
        self.fontFamily = 'Bahnschrift SemiBold'
        self.createTrayIcon()
        self.initUI()
        self.loadSettings()

    def saveSettings(self):
        settings = {
            'fontSize': self.fontSize,
            'fontColor': self.fontColor,
            'fontFamily': self.fontFamily,
            'is24Hour': self.is24Hour,
            'showSeconds': self.showSeconds,
            'windowPosX': self.x(),
            'windowPosY': self.y()
        }
        with open('settings.json', 'w') as settings_file:
            json.dump(settings, settings_file)

    def loadSettings(self):
        try:
            with open('settings.json', 'r') as settings_file:
                settings = json.load(settings_file)
                self.setFontSize(settings['fontSize'])
                self.setFontColor(settings['fontColor'])
                self.setFontFamily(QFont(settings.get('fontFamily', 'Bahnschrift SemiBold')))
                self.setTimeFormat(settings['is24Hour'])
                self.setShowSeconds(settings.get('showSeconds', True))
                self.move(settings.get('windowPosX', 300), settings.get('windowPosY', 300))

        except (FileNotFoundError, json.JSONDecodeError):
            self.setFontSize(25)
            self.setFontColor('#00aa7f')
            self.setFontFamily(QFont('Bahnschrift SemiBold'))
            self.setTimeFormat(True)
            self.setShowSeconds(True)
            self.move(300, 300)


    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(300, 300, 800, 170)
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        # self.setFontSize(self.fontSize)
        # self.setFontColor(self.fontColor)
        self.label.setFixedSize(700, 120)  # Adjust the size of the QLabel if necessary

        timer = QTimer(self)
        timer.timeout.connect(self.showTime)
        timer.start(1000)
        self.showTime()
        self.trayIcon.show()

    def setShowSeconds(self, state):
        self.showSeconds = bool(state)
        self.showTime()
        self.saveSettings()

    def setFontSize(self, value):
        self.fontSize = value
        self.label.setFont(QFont('Bahnschrift SemiBold', self.fontSize))
        self.saveSettings()

    def chooseColor(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.setFontColor(color.name())

    def setFontColor(self, color):
        self.fontColor = color
        self.label.setStyleSheet(f"QLabel {{ color : {self.fontColor}; }}")
        self.saveSettings()

    def setFontFamily(self, font):
        self.fontFamily = font.family()
        self.label.setFont(QFont(self.fontFamily, self.fontSize))
        self.saveSettings()

    def setTimeFormat(self, index):
        self.is24Hour = 1 if (index == 1) else 0
        self.showTime()
        self.saveSettings()

    def showTime(self):
        if self.showSeconds:
            formatString = 'HH:mm:ss' if self.is24Hour else 'hh:mm:ss AP'
        else:
            formatString = 'HH:mm' if self.is24Hour else 'hh:mm AP'
        currentTime = QTime.currentTime().toString(formatString)
        self.label.setText(currentTime)

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = event.globalPos() - self.oldPos
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

    def showSettingsDialog(self):
        dlg = SettingsDialog(self)
        # 设置对话框的位置
        dlg.move(600, 600)
        # 显示对话框
        dlg.exec_()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        settingsAction = menu.addAction("Settings")
        quitAction = menu.addAction("Quit")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == settingsAction:
            self.isSettingsDialog = True
            try:
                self.showSettingsDialog()
            except Exception as e:
                print(f"An error occurred: {e}")
            self.isSettingsDialog = False
        elif action == quitAction:
            self.saveSettings()
            self.close()

    def createTrayIcon(self):
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(QIcon('clock.png'))  # 设置你的图标路径

        # 创建一个显示时钟的动作
        showAction = QAction("Clock Switch", self)
        showAction.triggered.connect(self.showClock)
        # 创建一个点击退出的动作
        exitAction = QAction("Exit", self)
        exitAction.triggered.connect(self.exitApp)

        # 创建一个右键菜单
        trayMenu = QMenu(self)
        trayMenu.addAction(showAction)
        trayMenu.addAction(exitAction)

        self.trayIcon.setContextMenu(trayMenu)

    def showClock(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()

    def exitApp(self):
        self.saveSettings()
        self.trayIcon.hide()  # 隐藏托盘图标
        QApplication.quit()

    def closeEvent(self, event):
        if not self.isSettingsDialog:
            self.saveSettings()
            event.ignore()
            self.hide()
            self.trayIcon.showMessage('Running', 'Your application is still running.', QSystemTrayIcon.Information, 2000)
        else:
            event.ignore()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    clock = TransparentClock()
    # clock.show()
    clock.hide()
    sys.exit(app.exec_())
