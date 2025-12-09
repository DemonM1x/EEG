import time

import numpy as np
from PyQt5.QtWidgets import QMessageBox, QFileDialog

from realtime_work.realtime_controller import RealtimeEEGController, RealtimeDataBuffer
from realtime_work.realtime_driver import SerialEEGDriver, SyntheticEEGDriver, EEGSample, EEGSampleBatch
from realtime_work.realtime_recorder import RealtimeEEGRecorder
from report_generator.report_dialog import ReportConfigDialog
from validator.validation_dialog import ValidationDialog
from gui.threads import ProcessingThread, AnalysisThread, SingleRhythmAnalysisThread


class ProcessingMethods:
    def process_data(self):
        if self.raw_data is None:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите данные!")
            return
        self.processing_panel.btn_process.setEnabled(False)
        self.processing_panel.btn_process.setText("ОБРАБОТКА...")
        self.process_thread = ProcessingThread(self.preprocessor, self.raw_data, self.sampling_rate,
                                               self.processing_params)
        self.process_thread.result_signal.connect(self.on_processing_complete)
        self.process_thread.error_signal.connect(self.on_processing_error)
        self.process_thread.info_signal.connect(self.on_processing_info)
        self.process_thread.start()
        self.statusBar().showMessage("Обработка данных...")

    def on_processing_complete(self, processed_data):
        self.processed_data = processed_data
        self.processing_panel.btn_process.setEnabled(True)
        self.processing_panel.btn_process.setText("ОБРАБОТАТЬ СИГНАЛ")
        self.performance_monitor.take_system_snapshot()
        self.update_performance_display()
        self.analysis_panel.btn_analyze.setEnabled(True)
        self.analysis_panel.btn_analyze_single.setEnabled(True)
        self.analysis_panel.btn_validate.setEnabled(True)
        self.update_plots()
        self.update_data_info()
        self.statusBar().showMessage("Обработка завершена! Теперь можно анализировать ритмы.")

    def on_processing_error(self, error_msg):
        self.processing_panel.btn_process.setEnabled(True)
        self.processing_panel.btn_process.setText("ОБРАБОТАТЬ СИГНАЛ")
        QMessageBox.critical(self, "Ошибка обработки", error_msg)
        self.statusBar().showMessage("Ошибка обработки данных")

    def on_processing_info(self, info_msg):
        self.info_panel.info_text.append(info_msg)

    def analyze_rhythms(self):
        if self.processed_data is None:
            QMessageBox.warning(self, "Предупреждение", "Сначала обработайте данные!")
            return
        channel_idx = self.analysis_panel.analysis_channel_combo.currentIndex()
        self.analysis_panel.btn_analyze.setEnabled(False)
        self.analysis_panel.btn_analyze.setText("АНАЛИЗ...")
        self.analysis_panel.btn_analyze_single.setEnabled(False)
        self.analysis_thread = AnalysisThread(self.analyzer, self.processed_data, self.sampling_rate, channel_idx)
        self.analysis_thread.result_signal.connect(self.on_analysis_complete)
        self.analysis_thread.error_signal.connect(self.on_analysis_error)
        self.analysis_thread.info_signal.connect(self.on_analysis_info)
        self.analysis_thread.start()
        self.statusBar().showMessage("Анализ всех ритмов...")

    def analyze_single_rhythm(self):
        if self.processed_data is None:
            QMessageBox.warning(self, "Предупреждение", "Сначала обработайте данные!")
            return
        rhythm_idx = self.analysis_panel.rhythm_combo.currentIndex()
        if rhythm_idx == 0:
            QMessageBox.information(self, "Информация", "Выберите конкретный ритм для анализа")
            return
        rhythm_name = self.analysis_panel.rhythm_combo.currentText()
        channel_idx = self.analysis_panel.analysis_channel_combo.currentIndex()
        self.analysis_panel.btn_analyze_single.setEnabled(False)
        self.analysis_panel.btn_analyze_single.setText("АНАЛИЗ...")
        self.analysis_panel.btn_analyze.setEnabled(False)
        self.single_rhythm_thread = SingleRhythmAnalysisThread(self.analyzer, self.processed_data, self.sampling_rate,
                                                               channel_idx, rhythm_name)
        self.single_rhythm_thread.result_signal.connect(self.on_single_rhythm_complete)
        self.single_rhythm_thread.error_signal.connect(self.on_analysis_error)
        self.single_rhythm_thread.info_signal.connect(self.on_analysis_info)
        self.single_rhythm_thread.start()
        self.statusBar().showMessage(f"Анализ ритма {rhythm_name}...")

    def on_analysis_complete(self, result):
        self.current_analysis = result
        self.analysis_panel.btn_analyze.setEnabled(True)
        self.analysis_panel.btn_analyze.setText("АНАЛИЗИРОВАТЬ ВСЕ РИТМЫ")
        self.analysis_panel.btn_analyze_single.setEnabled(True)
        self.analysis_panel.btn_save_report.setEnabled(True)
        self.update_analysis_plots()

        # Переключаемся на график анализа
        self.plot_control.current_plot_index = 2
        self.plot_control.update_display()

        self.update_recommendations()
        self.update_data_info()
        self.update_performance_display()  # Обновляем отчет о производительности
        self.statusBar().showMessage("Анализ ритмов завершен!")

    def on_single_rhythm_complete(self, result):
        self.analysis_panel.btn_analyze_single.setEnabled(True)
        self.analysis_panel.btn_analyze_single.setText("АНАЛИЗИРОВАТЬ ВЫБРАННЫЙ РИТМ")
        self.analysis_panel.btn_analyze.setEnabled(True)

        # Сохраняем результат для отображения графиков
        self.current_analysis = {
            'analysis': result,
            'channel_idx': self.analysis_panel.analysis_channel_combo.currentIndex()
        }

        # Обновляем графики анализа
        self.update_analysis_plots()

        # Переключаемся на график анализа
        self.plot_control.current_plot_index = 2
        self.plot_control.update_display()

        # Обновляем отчет о производительности
        self.update_performance_display()

        self.display_single_rhythm_results(result)
        self.statusBar().showMessage(f"Анализ ритма {result['rhythm_name']} завершен!")

    def display_single_rhythm_results(self, result):
        rhythm_name = result['rhythm_name']
        power = result['power']
        relative_power = result['relative_power']
        peak_freq = result['peak_freq']
        freq_range = result['freq_range']
        info_text = f"=== АНАЛИЗ РИТМА: {rhythm_name.upper()} ===\n\nДиапазон частот: {freq_range[0]}-{freq_range[1]} Гц\nКанал: {self.channel_names[result['channel_idx']]}\n\nРЕЗУЛЬТАТЫ:\n• Абсолютная мощность: {power:.6f}\n• Относительная мощность: {relative_power:.4f} ({relative_power * 100:.2f}%)\n• Пиковая частота: {peak_freq:.2f} Гц\n\nИНТЕРПРЕТАЦИЯ:\n"
        interpretation = self.get_rhythm_interpretation(rhythm_name, relative_power)
        info_text += interpretation
        self.info_panel.info_text.append(info_text)
        QMessageBox.information(self, f"Результаты анализа: {rhythm_name}", info_text)

    def get_rhythm_interpretation(self, rhythm_name, relative_power):
        interpretations = {
            'дельта': {
                'high': (0.3, "• Высокая активность дельта-ритма (глубокий сон или патология)"),
                'medium': (0.15, "• Умеренная активность дельта-ритма (нормально для сна)"),
                'low': (0, "• Низкая активность дельта-ритма (состояние бодрствования)")
            },
            'тета': {
                'high': (0.25, "• Высокая активность тета-ритма (сонливость, медитация)"),
                'medium': (0.15, "• Умеренная активность тета-ритма (расслабление)"),
                'low': (0, "• Низкая активность тета-ритма (активное бодрствование)")
            },
            'альфа': {
                'high': (0.3, "• Высокая активность альфа-ритма (глубокое расслабление)"),
                'medium': (0.15, "• Умеренная активность альфа-ритма (спокойное бодрствование)"),
                'low': (0, "• Низкая активность альфа-ритма (активная деятельность)")
            },
            'бета': {
                'high': (0.4, "• Высокая активность бета-ритма (активное мышление, стресс)"),
                'medium': (0.2, "• Умеренная активность бета-ритма (нормальное бодрствование)"),
                'low': (0, "• Низкая активность бета-ритма (расслабленное состояние)")
            },
            'гамма': {
                'high': (0.15, "• Высокая активность гамма-ритма (интенсивная когнитивная активность)"),
                'medium': (0.05, "• Умеренная активность гамма-ритма (нормальная обработка информации)"),
                'low': (0, "• Низкая активность гамма-ритма (пониженная когнитивная активность)")
            }
        }
        if rhythm_name in interpretations:
            thresholds = interpretations[rhythm_name]
            if relative_power > thresholds['high'][0]:
                return thresholds['high'][1]
            elif relative_power > thresholds['medium'][0]:
                return thresholds['medium'][1]
            else:
                return thresholds['low'][1]
        return "• Интерпретация недоступна для данного ритма"

    def on_analysis_error(self, error_msg):
        self.analysis_panel.btn_analyze.setEnabled(True)
        self.analysis_panel.btn_analyze.setText("АНАЛИЗИРОВАТЬ ВСЕ РИТМЫ")
        self.analysis_panel.btn_analyze_single.setEnabled(True)
        self.analysis_panel.btn_analyze_single.setText("АНАЛИЗИРОВАТЬ ВЫБРАННЫЙ РИТМ")
        QMessageBox.critical(self, "Ошибка анализа", error_msg)
        self.statusBar().showMessage("Ошибка анализа данных")

    def on_analysis_info(self, info_msg):
        self.info_panel.info_text.append(info_msg)

    def save_report(self):
        if self.current_analysis is None:
            QMessageBox.warning(self, "Предупреждение", "Сначала проведите анализ!")
            return

        if self.raw_data is None:
            QMessageBox.warning(self, "Предупреждение", "Нет исходных данных для отчета!")
            return

        if self.processed_data is None:
            QMessageBox.warning(self, "Предупреждение", "Нет обработанных данных для отчета!")
            return

        try:
            dialog = ReportConfigDialog(self)
            if dialog.exec_() == dialog.Accepted:
                # Получаем конфигурацию отчета
                report_config = dialog.get_report_info()
                output_path = dialog.output_path
                patient_info = dialog.patient_info

                if not output_path:
                    QMessageBox.warning(self, "Ошибка", "Не указан путь для сохранения отчета!")
                    return

                # Создаем генератор отчетов
                from report_generator.report_generator import EEGReportGenerator
                report_generator = EEGReportGenerator()

                # Генерируем отчет используя правильный интерфейс
                success = report_generator.generate_report(
                    output_path=output_path,
                    patient_info=patient_info,
                )

                if success:
                    QMessageBox.information(self, "Успех", f"PDF-отчет успешно сохранен:\n{output_path}")
                    self.statusBar().showMessage(f"Отчет сохранен: {output_path}")

                    # Предлагаем открыть файл
                    reply = QMessageBox.question(
                        self,
                        "Открыть отчет?",
                        "Хотите открыть созданный отчет?",
                        QMessageBox.Yes | QMessageBox.No
                    )

                    if reply == QMessageBox.Yes:
                        try:
                            import os
                            import subprocess
                            import platform

                            if platform.system() == 'Windows':
                                os.startfile(output_path)
                            elif platform.system() == 'Darwin':  # macOS
                                subprocess.run(['open', output_path])
                            else:  # Linux
                                subprocess.run(['xdg-open', output_path])
                        except Exception as open_error:
                            QMessageBox.information(
                                self,
                                "Информация",
                                f"Отчет сохранен, но не удалось открыть файл автоматически:\n{output_path}"
                            )
                else:
                    QMessageBox.critical(self, "Ошибка",
                                         "Не удалось создать PDF-отчет. Проверьте права доступа к файлу.")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения отчета: {e}")
            print(f"Детали ошибки создания отчета: {e}")  # Для отладки

    def validate_with_mne(self):
        if self.processed_data is None:
            QMessageBox.warning(self, "Предупреждение", "Сначала обработайте данные!")
            return

        if self.raw_data is None:
            QMessageBox.warning(self, "Предупреждение", "Нет исходных данных для валидации!")
            return

        try:
            # Передаем правильные параметры в ValidationDialog
            dialog = ValidationDialog(
                validator=self.validator,
                data=self.raw_data,  # Исходные данные для MNE
                sampling_rate=self.sampling_rate,
                channel_names=self.channel_names,
                our_filtered=self.processed_data,  # Наши обработанные данные
                parent=self
            )
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка валидации: {e}")
            print(f"Детали ошибки валидации: {e}")  # Для отладки

    def on_analysis_channel_changed(self):
        if self.current_analysis is not None:
            self.update_analysis_plots()


class RealtimeMethods:
    def start_recording(self):
        try:
            data_source = self.recording_settings_panel.data_source_combo.currentText()
            sample_rate = self.recording_settings_panel.recording_sampling_spin.value()
            self.realtime_buffer = RealtimeDataBuffer(max_duration_seconds=3600, sample_rate=sample_rate)
            if "Serial" in data_source:
                port_text = self.recording_settings_panel.com_port_combo.currentText()
                if not port_text:
                    QMessageBox.warning(self, "Ошибка", "Выберите COM порт")
                    return
                port = port_text.split(' - ')[0]
                baudrate = int(self.recording_settings_panel.baudrate_combo.currentText())
                self.realtime_driver = SerialEEGDriver(port=port, baudrate=baudrate, sample_rate=sample_rate)
            else:
                self.realtime_driver = SyntheticEEGDriver(sample_rate=sample_rate, num_channels=1)
            self.realtime_controller = RealtimeEEGController(driver=self.realtime_driver, buffer=self.realtime_buffer)
            self.realtime_controller.data_received.connect(self._on_realtime_data)
            self.realtime_controller.status_changed.connect(self._on_realtime_status)
            self.realtime_controller.error_occurred.connect(self._on_realtime_error)
            self.realtime_plot_widget.set_buffer(self.realtime_buffer)
            self.realtime_controller.start()
            self.is_recording = True
            self.recording_control_panel.btn_start_recording.setEnabled(False)
            self.recording_control_panel.btn_stop_recording.setEnabled(True)
            self.recording_control_panel.btn_save_recorded.setEnabled(True)
            self.recording_control_panel.btn_use_recorded.setEnabled(False)
            self.recording_status_panel.recording_status.setText("ЗАПИСЬ АКТИВНА - Real-time визуализация")
            self.recording_status_panel.recording_info.append(f"Real-time запись начата: 1 канал, {sample_rate} Гц")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось начать запись: {e}")
            self.recording_status_panel.recording_info.append(f"ОШИБКА: {e}")
            self.stop_recording()

    def stop_recording(self):
        try:
            if self.realtime_controller:
                self.realtime_controller.stop()
                self.realtime_controller = None
            if self.realtime_buffer:
                timestamps, channel_data = self.realtime_buffer.get_data_for_plotting(window_seconds=3600)
                if timestamps and channel_data:
                    self.recorded_data = np.array(channel_data)
                    self.sampling_rate = self.recording_settings_panel.recording_sampling_spin.value()
                    self.channel_names = [f'Channel_{i + 1}' for i in range(len(channel_data))]
                    self.recording_status_panel.recording_info.append(
                        f"Сохранено {len(timestamps)} образцов для анализа")
            self.is_recording = False
            self.recording_control_panel.btn_start_recording.setEnabled(True)
            self.recording_control_panel.btn_stop_recording.setEnabled(False)
            self.recording_control_panel.btn_save_recorded.setEnabled(False)
            self.recording_control_panel.btn_use_recorded.setEnabled(True if self.recorded_data is not None else False)
            self.recording_status_panel.recording_status.setText("Запись остановлена")
            self.recording_status_panel.recording_info.append("Real-time запись завершена")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка остановки записи: {e}")
            self.recording_status_panel.recording_info.append(f"ОШИБКА ОСТАНОВКИ: {e}")

    def save_recorded_data(self):
        if not self.realtime_buffer:
            QMessageBox.warning(self, "Ошибка", "Нет данных для сохранения")
            return
        try:
            file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить запись ЭЭГ",
                                                       f"eeg_recording_{int(time.time())}.csv", "CSV Files (*.csv)")
            if not file_path:
                return
            file_recorder = RealtimeEEGRecorder()
            if file_recorder.start_recording(file_path):
                timestamps, channel_data = self.realtime_buffer.get_data_for_plotting(window_seconds=3600)
                if timestamps and channel_data and channel_data[0]:
                    samples = []
                    for i, timestamp in enumerate(timestamps):
                        amplitude = channel_data[0][i] if i < len(channel_data[0]) else 0.0
                        samples.append(EEGSample(timestamp=timestamp, amplitudes=[amplitude]))
                    batch_size = 100
                    for i in range(0, len(samples), batch_size):
                        batch = EEGSampleBatch(samples=samples[i:i + batch_size])
                        file_recorder.write_batch(batch)
                    file_recorder.stop_recording()
                    QMessageBox.information(self, "Успех",
                                            f"Данные сохранены в файл:\n{file_path}\nЗаписано {len(timestamps)} образцов")
                    self.recording_status_panel.recording_info.append(f"Данные сохранены: {file_path}")
                else:
                    QMessageBox.warning(self, "Ошибка", "Нет данных для сохранения")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось создать файл для записи")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения: {e}")
            self.recording_status_panel.recording_info.append(f"ОШИБКА СОХРАНЕНИЯ: {e}")

    def use_recorded_data(self):
        if self.recorded_data is None:
            QMessageBox.warning(self, "Предупреждение", "Нет записанных данных!")
            return
        self.raw_data = self.recorded_data
        self.sampling_rate = self.recording_settings_panel.recording_sampling_spin.value()
        self.channel_names = [f'Recorded_Ch{i}' for i in range(self.recorded_data.shape[0])]
        self.processed_data = None
        self.current_analysis = None
        self.update_channel_combo()
        self.update_analysis_channel_combo()
        self.update_data_info()
        self.update_plots()
        self.processing_panel.btn_process.setEnabled(True)
        self.analysis_panel.btn_analyze.setEnabled(False)
        self.tabs.setCurrentIndex(0)
        self.statusBar().showMessage("Записанные данные загружены для анализа!")
        QMessageBox.information(self, "Успех",
                                "Записанные данные загружены!\nТеперь вы можете:\n1. Обработать сигнал\n2. Проанализировать ритмы\n3. Получить рекомендации")

    def _on_realtime_data(self, batch):
        try:
            if self.realtime_buffer:
                self.realtime_buffer.add_batch(batch)
            if self.realtime_plot_widget:
                self.realtime_plot_widget.update_plot()
        except Exception as e:
            print(f"Ошибка обработки real-time данных: {e}")
            self.recording_status_panel.recording_info.append(f"Ошибка обработки данных: {e}")

    def _on_realtime_status(self, status):
        self.recording_status_panel.recording_status.setText(f"{status}")

    def _on_realtime_error(self, error):
        self.recording_status_panel.recording_info.append(f"ОШИБКА: {error}")
        QMessageBox.warning(self, "Real-time ошибка", error)
        if self.is_recording:
            self.stop_recording()
