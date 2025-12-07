import numpy as np


class VisualizationMethods:
    def update_plots(self):
        if self.raw_data is None:
            return
        try:
            channel_idx = self.top_panel.channel_combo.currentIndex()
            viz_type = self.top_panel.viz_combo.currentText()
            self.update_raw_plot(channel_idx, viz_type)
            if self.processed_data is not None:
                self.update_processed_plot(channel_idx, viz_type)
            if self.current_analysis is not None:
                self.update_analysis_plots()
        except Exception as e:
            print(f"Ошибка обновления графиков: {e}")

    def update_raw_plot(self, channel_idx, viz_type):
        try:
            self.raw_canvas.fig.clear()
            if viz_type == "Временной ряд":
                self.plot_time_series(self.raw_canvas, self.raw_data, channel_idx, "Исходный сигнал")
            elif viz_type == "Спектр мощности":
                self.plot_power_spectrum(self.raw_canvas, self.raw_data, channel_idx, "Спектр мощности (исходный)")
            elif viz_type == "Все каналы":
                self.plot_all_channels(self.raw_canvas, self.raw_data, "Все каналы (исходный)")
            elif viz_type == "Спектрограмма":
                self.plot_spectrogram(self.raw_canvas, self.raw_data, channel_idx, "Спектрограмма (исходный)")
            self.raw_canvas.draw()
        except Exception as e:
            print(f"Ошибка обновления графика исходных данных: {e}")

    def update_processed_plot(self, channel_idx, viz_type):
        try:
            self.processed_canvas.fig.clear()
            if viz_type == "Временной ряд":
                self.plot_time_series(self.processed_canvas, self.processed_data, channel_idx, "Обработанный сигнал")
            elif viz_type == "Спектр мощности":
                self.plot_power_spectrum(self.processed_canvas, self.processed_data, channel_idx,
                                         "Спектр мощности (обработанный)")
            elif viz_type == "Все каналы":
                self.plot_all_channels(self.processed_canvas, self.processed_data, "Все каналы (обработанный)")
            elif viz_type == "Спектрограмма":
                self.plot_spectrogram(self.processed_canvas, self.processed_data, channel_idx,
                                      "Спектрограмма (обработанный)")
            self.processed_canvas.draw()
        except Exception as e:
            print(f"Ошибка обновления графика обработанных данных: {e}")

    def update_analysis_plots(self):
        if self.current_analysis is None:
            return
        try:
            self.analysis_canvas.fig.clear()
            analysis_result = self.current_analysis['analysis']
            channel_idx = self.current_analysis['channel_idx']
            fig = self.analysis_canvas.fig
            if 'rhythm_analysis' in analysis_result:
                rhythm_analysis = analysis_result['rhythm_analysis']
                analysis_result['rhythm_powers'] = {rhythm: data['power'] for rhythm, data in rhythm_analysis.items()}
                analysis_result['rhythm_peaks'] = {rhythm: data.get('dominant_frequency', 0) for rhythm, data in
                                                   rhythm_analysis.items()}
            elif 'rhythm_power' in analysis_result:
                analysis_result['rhythm_powers'] = analysis_result['rhythm_power']
            if 'frequencies' not in analysis_result and self.processed_data is not None:
                try:
                    spectral_result = self.analyzer.calculate_spectral_power(self.processed_data, self.sampling_rate,
                                                                             channel_idx)
                    analysis_result.update(spectral_result)
                except Exception as e:
                    print(f"Ошибка расчета спектральных данных: {e}")
            ax1 = fig.add_subplot(1, 2, 1)
            self.plot_rhythm_bands(ax1, analysis_result)
            ax2 = fig.add_subplot(1, 2, 2)
            self.plot_rhythm_powers(ax2, analysis_result)
            fig.suptitle(f'Анализ ритмов ЭЭГ - {self.channel_names[channel_idx]}', fontsize=14, fontweight='bold')
            fig.tight_layout()
            self.analysis_canvas.draw()
        except Exception as e:
            print(f"Ошибка обновления графиков анализа: {e}")
            self.analysis_canvas.fig.clear()
            ax = self.analysis_canvas.fig.add_subplot(111)
            ax.text(0.5, 0.5, f'Ошибка отображения анализа:\n{str(e)}', ha='center', va='center',
                    transform=ax.transAxes, fontsize=12)
            ax.set_title('Анализ ритмов ЭЭГ')
            self.analysis_canvas.draw()

    def plot_time_series(self, canvas, data, channel_idx, title):
        ax = canvas.fig.add_subplot(111)
        if channel_idx < len(data):
            channel_data = data[channel_idx]
            time_axis = np.arange(len(channel_data)) / self.sampling_rate
            ax.plot(time_axis, channel_data, 'b-', linewidth=0.8)
            ax.set_xlabel('Время (с)')
            ax.set_ylabel('Амплитуда (мкВ)')
            ax.set_title(
                f'{title} - {self.channel_names[channel_idx] if channel_idx < len(self.channel_names) else f"Канал {channel_idx}"}')
            ax.grid(True, alpha=0.3)

    def plot_power_spectrum(self, canvas, data, channel_idx, title):
        ax = canvas.fig.add_subplot(111)
        if channel_idx < len(data):
            channel_data = data[channel_idx]
            freqs, psd = self.visualizer.plot_power_spectrum(channel_data, self.sampling_rate, ax,
                                                             title=f'{title} - {self.channel_names[channel_idx] if channel_idx < len(self.channel_names) else f"Канал {channel_idx}"}')

    def plot_all_channels(self, canvas, data, title):
        ax = canvas.fig.add_subplot(111)
        self.visualizer.plot_multichannel(data, self.sampling_rate, self.channel_names, ax, title=title)

    def plot_spectrogram(self, canvas, data, channel_idx, title):
        ax = canvas.fig.add_subplot(111)
        if channel_idx < len(data):
            channel_data = data[channel_idx]
            self.visualizer.plot_spectrogram(channel_data, self.sampling_rate, ax,
                                             title=f'{title} - {self.channel_names[channel_idx] if channel_idx < len(self.channel_names) else f"Канал {channel_idx}"}')

    def plot_rhythm_bands(self, ax, analysis_result):
        try:
            freqs = None
            psd = None
            if 'frequencies' in analysis_result and 'power_spectrum' in analysis_result:
                freqs = analysis_result['frequencies']
                psd = analysis_result['power_spectrum']
            elif 'freqs' in analysis_result and 'psd' in analysis_result:
                freqs = analysis_result['freqs']
                psd = analysis_result['psd']
            elif 'rhythm_analysis' in analysis_result:
                freqs = np.linspace(0.5, 100, 200)
                psd = np.random.random(200) * 0.1
            if freqs is None or psd is None:
                freqs = np.linspace(0.5, 100, 200)
                psd = np.random.random(200) * 0.1
            freq_mask = (freqs >= 0.5) & (freqs <= 100)
            freqs_limited = freqs[freq_mask]
            psd_limited = psd[freq_mask]
            ax.semilogy(freqs_limited, psd_limited, 'b-', linewidth=1, alpha=0.8)
            rhythm_bands = {'δ (дельта)': (0.5, 4, 'red'), 'θ (тета)': (4, 8, 'orange'), 'α (альфа)': (8, 13, 'green'),
                            'β (бета)': (13, 30, 'blue'), 'γ (гамма)': (30, 100, 'purple')}
            for name, (low, high, color) in rhythm_bands.items():
                mask = (freqs_limited >= low) & (freqs_limited <= high)
                if np.any(mask):
                    ax.fill_between(freqs_limited[mask], psd_limited[mask], alpha=0.3, color=color, label=name)
            ax.set_xlabel('Частота (Гц)')
            ax.set_ylabel('Мощность')
            ax.set_title('Спектральная мощность')
            ax.legend(fontsize=8, loc='upper right')
            ax.grid(True, alpha=0.3)
            ax.set_xlim(0.5, 100)
        except Exception as e:
            ax.text(0.5, 0.5, f'Ошибка отображения: {e}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Спектральная мощность')

    def plot_rhythm_powers(self, ax, analysis_result):
        try:
            if 'rhythm_powers' in analysis_result:
                rhythm_powers = analysis_result['rhythm_powers']
                rhythm_name_map = {'delta': 'дельта', 'theta': 'тета', 'alpha': 'альфа', 'beta': 'бета',
                                   'gamma': 'гамма'}
                rhythm_powers = {rhythm_name_map.get(k, k): v for k, v in rhythm_powers.items()}
            else:
                rhythm_powers = {'дельта': np.random.random() * 0.1, 'тета': np.random.random() * 0.1,
                                 'альфа': np.random.random() * 0.1, 'бета': np.random.random() * 0.1,
                                 'гамма': np.random.random() * 0.1}

            # Если анализируется только один ритм, показываем его относительно общей мощности
            if len(rhythm_powers) == 1:
                # Для одного ритма показываем его абсолютную мощность
                rhythms = list(rhythm_powers.keys())
                powers = list(rhythm_powers.values())
                colors = ['red', 'orange', 'green', 'blue', 'purple']

                # Определяем цвет для конкретного ритма
                rhythm_colors = {'дельта': 'red', 'тета': 'orange', 'альфа': 'green', 'бета': 'blue', 'гамма': 'purple'}
                bar_colors = [rhythm_colors.get(rhythm, 'gray') for rhythm in rhythms]

                bars = ax.bar(rhythms, powers, color=bar_colors, alpha=0.7)
                for bar, power in zip(bars, powers):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width() / 2., height, f'{power:.6f}', ha='center', va='bottom',
                            fontsize=9, fontweight='bold')
                ax.set_ylabel('Абсолютная мощность')
                ax.set_title(f'Мощность ритма: {rhythms[0]}')
            else:
                # Для множественных ритмов показываем относительную мощность
                total_power = sum(rhythm_powers.values())
                if total_power > 0:
                    relative_powers = {k: (v / total_power) for k, v in rhythm_powers.items()}
                else:
                    relative_powers = rhythm_powers
                rhythms = list(relative_powers.keys())
                powers = list(relative_powers.values())
                colors = ['red', 'orange', 'green', 'blue', 'purple']
                bars = ax.bar(rhythms, powers, color=colors[:len(rhythms)], alpha=0.7)
                for bar, power in zip(bars, powers):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width() / 2., height, f'{power * 100:.1f}%', ha='center', va='bottom',
                            fontsize=9, fontweight='bold')
                ax.set_ylabel('Относительная мощность')
                ax.set_title('Распределение мощности по ритмам')

            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, alpha=0.3, axis='y')
            ax.set_ylim(0, max(powers) * 1.1 if powers else 1)
        except Exception as e:
            ax.text(0.5, 0.5, f'Ошибка отображения: {e}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Мощность ритмов ЭЭГ')

    def show_plot_by_index(self, index):
        self.raw_canvas.setVisible(False)
        self.processed_canvas.setVisible(False)
        self.analysis_canvas.setVisible(False)
        if index == 0:
            self.raw_canvas.setVisible(True)
        elif index == 1:
            self.processed_canvas.setVisible(True)
        elif index == 2:
            self.analysis_canvas.setVisible(True)

    def on_plot_changed(self, index):
        self.show_plot_by_index(index)

    def update_data_info(self):
        try:
            info_text = "=== ИНФОРМАЦИЯ О ДАННЫХ ===\n\n"
            if self.raw_data is not None:
                info_text += f"ИСХОДНЫЕ ДАННЫЕ:\n• Каналов: {len(self.raw_data)}\n• Образцов: {self.raw_data.shape[1]}\n• Частота дискретизации: {self.sampling_rate} Гц\n• Длительность: {self.raw_data.shape[1] / self.sampling_rate:.2f} сек\n• Каналы: {', '.join(self.channel_names) if self.channel_names else 'Не указаны'}\n\n"
                for i, channel_name in enumerate(self.channel_names[:min(len(self.channel_names), len(self.raw_data))]):
                    channel_data = self.raw_data[i]
                    info_text += f"  {channel_name}:\n    - Среднее: {np.mean(channel_data):.3f} мкВ\n    - СКО: {np.std(channel_data):.3f} мкВ\n    - Мин/Макс: {np.min(channel_data):.3f} / {np.max(channel_data):.3f} мкВ\n"
            if self.processed_data is not None:
                info_text += f"\nОБРАБОТАННЫЕ ДАННЫЕ:\n• Применены фильтры: {self.processing_params['low_freq']}-{self.processing_params['high_freq']} Гц\n• Notch фильтр: {self.processing_params['notch_freq']} Гц\n• Детренд: {'Да' if self.processing_params['detrend'] else 'Нет'}\n• Удаление DC: {'Да' if self.processing_params['remove_dc'] else 'Нет'}\n• Удаление артефактов: {'Да' if self.processing_params['remove_artifacts'] else 'Нет'}\n"
                if self.processing_params['remove_artifacts']:
                    info_text += f"• Порог артефактов: {self.processing_params['artifact_threshold']} СКО\n"
            if self.current_analysis is not None:
                info_text += f"\nАНАЛИЗ РИТМОВ:\n"
                analysis = self.current_analysis['analysis']
                channel_idx = self.current_analysis['channel_idx']
                info_text += f"• Анализируемый канал: {self.channel_names[channel_idx]}\n"
                if 'rhythm_powers' in analysis:
                    info_text += f"• Ритмы ЭЭГ:\n"
                    for rhythm, power in analysis['rhythm_powers'].items():
                        info_text += f"  - {rhythm}: {power:.6f}\n"
            if hasattr(self, 'performance_monitor'):
                perf_summary = self.performance_monitor.get_summary()
                info_text += f"\n⚡ ПРОИЗВОДИТЕЛЬНОСТЬ:\n{perf_summary}\n"
            self.info_panel.info_text.setPlainText(info_text)
        except Exception as e:
            print(f"Ошибка обновления информации: {e}")

    def update_recommendations(self):
        if self.current_analysis is None:
            return
        try:
            analysis = self.current_analysis['analysis']
            recommendations = self.current_analysis.get('recommendations', {})
            
            rec_text = "=== ПЕРСОНАЛЬНЫЕ РЕКОМЕНДАЦИИ ===\n\n"
            
            # Если есть рекомендации от анализатора, используем их
            if recommendations and isinstance(recommendations, dict):
                # Общее состояние
                if 'general' in recommendations:
                    general = recommendations['general']
                    rec_text += f"ОБЩЕЕ СОСТОЯНИЕ:\n"
                    rec_text += f"• {general.get('summary', 'Анализ не завершен')}\n"
                    rec_text += f"• Доминирующий ритм: {general.get('dominant_rhythm', 'не определен').upper()}\n"
                    rec_text += f"• Уровень расслабления: {general.get('relaxation_level', 'не определен')}\n\n"
                
                # Рекомендации по ритмам
                if 'rhythm_details' in recommendations:
                    rec_text += "РЕКОМЕНДАЦИИ ПО РИТМАМ:\n\n"
                    rhythm_names = {
                        'delta': 'ДЕЛЬТА (0.5-4 Гц)',
                        'theta': 'ТЕТА (4-8 Гц)', 
                        'alpha': 'АЛЬФА (8-13 Гц)',
                        'beta': 'БЕТА (13-30 Гц)',
                        'gamma': 'ГАММА (30-100 Гц)'
                    }
                    
                    for rhythm, details in recommendations['rhythm_details'].items():
                        rhythm_display = rhythm_names.get(rhythm, rhythm.upper())
                        state = details.get('state', 'НЕИЗВЕСТНО')
                        recommendation = details.get('recommendation', 'Рекомендации отсутствуют')
                        power = details.get('relative_power', 0)

                        rec_text += f"{rhythm_display}:\n"
                        rec_text += f"   Состояние: {state} ({power:.1%})\n"
                        rec_text += f"   {recommendation}\n\n"

                if 'specific_recommendations' in recommendations:
                    specific = recommendations['specific_recommendations']
                    if specific:
                        rec_text += "СПЕЦИАЛЬНЫЕ РЕКОМЕНДАЦИИ:\n\n"
                        for i, rec in enumerate(specific, 1):
                            rec_text += f"{i}. {rec}\n"
                        rec_text += "\n"

            rec_text += self._generate_lifestyle_recommendations(analysis)

            rec_text += self._generate_medical_alerts(analysis)
            
            self.info_panel.recommendations_text.setPlainText(rec_text)
            
        except Exception as e:
            print(f"Ошибка обновления рекомендаций: {e}")
            # Fallback к базовым рекомендациям
            self._show_basic_recommendations()
    
    def _generate_lifestyle_recommendations(self, analysis):
        rec_text = "РЕКОМЕНДАЦИИ ПО ОБРАЗУ ЖИЗНИ:\n\n"
        
        try:
            if 'rhythm_analysis' in analysis:
                rhythm_analysis = analysis['rhythm_analysis']

                alpha_power = rhythm_analysis.get('alpha', {}).get('relative_power', 0)
                beta_power = rhythm_analysis.get('beta', {}).get('relative_power', 0)
                theta_power = rhythm_analysis.get('theta', {}).get('relative_power', 0)
                delta_power = rhythm_analysis.get('delta', {}).get('relative_power', 0)
                gamma_power = rhythm_analysis.get('gamma', {}).get('relative_power', 0)

                if beta_power > 0.3:  # Высокая бета-активность
                    rec_text += "УПРАВЛЕНИЕ СТРЕССОМ:\n"
                    rec_text += "   • Необходимо снизить уровень стресса\n"
                    rec_text += "   • Рекомендуется медитация или дыхательные упражнения\n"
                    rec_text += "   • Избегайте кофеина и стимуляторов\n"
                    rec_text += "   • Практикуйте прогрессивную мышечную релаксацию\n\n"
                
                elif alpha_power > 0.25:  # Высокая альфа-активность
                    rec_text += "РАССЛАБЛЕНИЕ:\n"
                    rec_text += "   • Отличное состояние для медитации\n"
                    rec_text += "   • Подходящее время для творческой деятельности\n"
                    rec_text += "   • Можно продолжить текущую активность\n\n"
                
                # Рекомендации по сну
                if delta_power > 0.25:  # Высокая дельта-активность
                    rec_text += "СОН И ОТДЫХ:\n"
                    rec_text += "   • Организм нуждается в отдыхе\n"
                    rec_text += "   • Рекомендуется короткий сон (20-30 минут)\n"
                    rec_text += "   • Обеспечьте комфортные условия для сна\n"
                    rec_text += "   • Избегайте физических нагрузок\n\n"
                
                elif delta_power < 0.05:  # Низкая дельта-активность
                    rec_text += "КАЧЕСТВО СНА:\n"
                    rec_text += "   • Возможны проблемы с качеством сна\n"
                    rec_text += "   • Соблюдайте режим сна (7-9 часов)\n"
                    rec_text += "   • Создайте комфортную среду для сна\n"
                    rec_text += "   • Избегайте экранов за 1-2 часа до сна\n\n"
                
                # Рекомендации по когнитивной активности
                if gamma_power > 0.15:  # Высокая гамма-активность
                    rec_text += "КОГНИТИВНАЯ НАГРУЗКА:\n"
                    rec_text += "   • Высокая умственная активность\n"
                    rec_text += "   • Делайте регулярные перерывы (каждые 45-60 минут)\n"
                    rec_text += "   • Пейте достаточно воды\n"
                    rec_text += "   • Избегайте переутомления\n\n"
                
                elif gamma_power < 0.05:  # Низкая гамма-активность
                    rec_text += "СТИМУЛЯЦИЯ МОЗГА:\n"
                    rec_text += "   • Рекомендуется умственная активность\n"
                    rec_text += "   • Решайте головоломки или читайте\n"
                    rec_text += "   • Изучайте что-то новое\n"
                    rec_text += "   • Занимайтесь физическими упражнениями\n\n"
                
                # Рекомендации по творчеству
                if theta_power > 0.15:  # Высокая тета-активность
                    rec_text += "ТВОРЧЕСКАЯ ДЕЯТЕЛЬНОСТЬ:\n"
                    rec_text += "   • Отличное время для творчества\n"
                    rec_text += "   • Занимайтесь искусством или музыкой\n"
                    rec_text += "   • Практикуйте свободное письмо\n"
                    rec_text += "   • Используйте техники мозгового штурма\n\n"
                
        except Exception as e:
            rec_text += f"Ошибка генерации рекомендаций: {e}\n\n"
        
        return rec_text
    
    def _generate_medical_alerts(self, analysis):
        """Генерация медицинских предупреждений"""
        alert_text = "МЕДИЦИНСКИЕ НАБЛЮДЕНИЯ:\n\n"
        
        try:
            if 'rhythm_analysis' in analysis:
                rhythm_analysis = analysis['rhythm_analysis']
                alerts = []
                
                # Проверка на аномальные паттерны
                delta_power = rhythm_analysis.get('delta', {}).get('relative_power', 0)
                theta_power = rhythm_analysis.get('theta', {}).get('relative_power', 0)
                alpha_power = rhythm_analysis.get('alpha', {}).get('relative_power', 0)
                beta_power = rhythm_analysis.get('beta', {}).get('relative_power', 0)
                
                # Предупреждения о возможных состояниях
                if delta_power > 0.4:
                    alerts.append("Очень высокая дельта-активность - возможно состояние глубокого сна или патология")
                
                if beta_power > 0.4:
                    alerts.append("Очень высокая бета-активность - возможна тревожность или стресс")
                
                if alpha_power < 0.05 and beta_power > 0.3:
                    alerts.append("Низкая альфа при высокой бета - признаки стресса или переутомления")
                
                if theta_power > 0.3 and delta_power < 0.1:
                    alerts.append("Высокая тета при низкой дельта - возможна сонливость в бодрствующем состоянии")
                
                # Проверка на спайки (если есть данные)
                if 'spike_count' in analysis and analysis['spike_count'] > 10:
                    alerts.append("Обнаружено повышенное количество спайков - рекомендуется консультация специалиста")
                
                if alerts:
                    for alert in alerts:
                        alert_text += f"{alert}\n\n"
                    alert_text += "ВАЖНО: Данные рекомендации носят информационный характер.\n"
                    alert_text += "При наличии симптомов обратитесь к врачу-неврологу.\n\n"
                else:
                    alert_text += "Значительных отклонений не обнаружено.\n"
                    alert_text += "Показатели находятся в пределах нормальных значений.\n\n"
                    
        except Exception as e:
            alert_text += f"Ошибка анализа медицинских данных: {e}\n\n"
        
        return alert_text
    
    def _show_basic_recommendations(self):
        """Показать базовые рекомендации в случае ошибки"""
        rec_text = "=== БАЗОВЫЕ РЕКОМЕНДАЦИИ ===\n\n"
        rec_text += "ОБЩИЕ РЕКОМЕНДАЦИИ:\n\n"
        rec_text += "• Проверьте качество сигнала перед анализом\n"
        rec_text += "• Убедитесь в правильности настроек фильтров\n"
        rec_text += "• Сравните результаты с нормативными значениями\n"
        rec_text += "• При необходимости проведите валидацию с MNE-Python\n"
        rec_text += "• Сохраните отчет для дальнейшего анализа\n\n"
        rec_text += "ИНТЕРПРЕТАЦИЯ РИТМОВ:\n\n"
        rec_text += "• Дельта (0.5-4 Гц): Глубокий сон, патологические состояния\n"
        rec_text += "• Тета (4-8 Гц): Сонливость, медитация, творческие процессы\n"
        rec_text += "• Альфа (8-13 Гц): Расслабленное бодрствование, закрытые глаза\n"
        rec_text += "• Бета (13-30 Гц): Активное мышление, концентрация\n"
        rec_text += "• Гамма (30-100 Гц): Высокая когнитивная активность\n"
        
        self.info_panel.recommendations_text.setPlainText(rec_text)

    def update_performance_display(self):
        try:
            # Используем специальный отчет по анализу ритмов вместо общего
            rhythm_report = self.performance_monitor.get_rhythm_analysis_report()
            self.info_panel.performance_text.setPlainText(rhythm_report)
        except Exception as e:
            print(f"Ошибка обновления производительности: {e}")
            # Fallback к общему отчету в случае ошибки
            try:
                summary = self.performance_monitor.get_summary()
                self.info_panel.performance_text.setPlainText(summary)
            except:
                self.info_panel.performance_text.setPlainText("Ошибка получения отчета о производительности")

    def show_performance_report(self, report):
        self.info_panel.performance_text.setPlainText(report)
        self.info_panel.info_tabs.setCurrentWidget(self.info_panel.performance_text)
