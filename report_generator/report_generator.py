import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.gridspec import GridSpec
from datetime import datetime
import pandas as pd
from typing import Dict, Any, Optional, Tuple
import matplotlib
import warnings
matplotlib.use('Agg')  # Используем backend без GUI для лучшего качества PDF
warnings.filterwarnings('ignore', message='This figure includes Axes that are not compatible with tight_layout')


class EEGReportGenerator:
    """Генератор PDF-отчетов для анализа ЭЭГ"""
    
    def __init__(self):
        self.report_data = {}
        self.figures = []
        
    def set_data(self, raw_data: np.ndarray, processed_data: np.ndarray, 
                 analysis_results: Dict[str, Any], sampling_rate: float,
                 channel_names: list, recommendations: Dict[str, Any],
                 performance_data: Optional[Dict] = None, 
                 processing_params: Optional[Dict] = None):
        """Установка данных для отчета"""
        self.report_data = {
            'raw_data': raw_data,
            'processed_data': processed_data,
            'analysis_results': analysis_results,
            'sampling_rate': sampling_rate,
            'channel_names': channel_names,
            'recommendations': recommendations,
            'performance_data': performance_data or {},
            'processing_params': processing_params or {},
            'timestamp': datetime.now()
        }
        
    def generate_report(self, output_path: str, patient_info: Optional[Dict] = None) -> bool:
        """Генерация полного PDF-отчета"""
        try:
            with PdfPages(output_path) as pdf:
                # Титульная страница
                self._create_title_page(pdf, patient_info)
                
                # Страница с исходными сигналами
                self._create_raw_signals_page(pdf)
                
                # Страница с обработанными сигналами
                self._create_processed_signals_page(pdf)
                
                # Страница со спектральным анализом
                self._create_spectral_analysis_page(pdf)
                
                # Страница с рекомендациями и выводами
                self._create_recommendations_page(pdf)
                
                # Метаданные PDF
                d = pdf.infodict()
                d['Title'] = 'EEG Analysis Report'
                d['Author'] = 'EEG Analyzer'
                d['Subject'] = 'Electroencephalogram Analysis'
                d['Keywords'] = 'EEG, Brain Activity, Signal Processing'
                d['CreationDate'] = datetime.now()
                
            return True
            
        except Exception as e:
            print(f"Ошибка при создании отчета: {e}")
            return False
    
    def _create_title_page(self, pdf: PdfPages, patient_info: Optional[Dict]):
        """Создание титульной страницы"""
        fig = plt.figure(figsize=(8.27, 11.69), dpi=300)
        fig.patch.set_facecolor('white')
        
        # Очищаем фигуру от осей
        ax = fig.add_subplot(111)
        ax.axis('off')
        
        # Заголовок
        ax.text(0.5, 0.90, 'Отчет по анализу ЭЭГ',
                ha='center', va='center', fontsize=24, fontweight='bold',
                transform=ax.transAxes)
    
        y_pos = 0.75
        if patient_info and patient_info:
            ax.text(0.5, y_pos, 'Данные пацианта',
                    ha='center', va='center', fontsize=16, fontweight='bold',
                    transform=ax.transAxes)
            y_pos -= 0.06
            
            # Создаем таблицу для информации о пациенте
            patient_data = []
            for key, value in patient_info.items():
                if value:  # Только если значение не пустое
                    patient_data.append([f'{key}:', str(value)])
            
            if patient_data:
                for label, value in patient_data:
                    ax.text(0.25, y_pos, label, ha='left', va='center', 
                           fontsize=12, fontweight='bold', transform=ax.transAxes)
                    ax.text(0.75, y_pos, value, ha='right', va='center', 
                           fontsize=12, transform=ax.transAxes)
                    y_pos -= 0.04
        
        # Информация о записи
        y_pos -= 0.06
        ax.text(0.5, y_pos, 'Параметры записи', 
                ha='center', va='center', fontsize=16, fontweight='bold',
                transform=ax.transAxes)
        y_pos -= 0.06
        
        recording_info = [
            ('Дата', self.report_data['timestamp'].strftime('%d.%m.%Y')),
            ('Частота дискретизации', f"{self.report_data['sampling_rate']:.0f} Гц"),
            ('Количество каналов', str(len(self.report_data['channel_names']))),
            ('Длительность записи', f"{self.report_data['raw_data'].shape[1] / self.report_data['sampling_rate']:.1f} сек"),
            ('Каналы', ', '.join(self.report_data['channel_names'][:6]))  # Первые 6 каналов
        ]
        
        for label, value in recording_info:
            ax.text(0.25, y_pos, f'{label}:', ha='left', va='center', 
                   fontsize=12, fontweight='bold', transform=ax.transAxes)
            ax.text(0.75, y_pos, str(value), ha='right', va='center', 
                   fontsize=12, transform=ax.transAxes)
            y_pos -= 0.04
        
        # Устанавливаем пределы для правильного отображения
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        
        pdf.savefig(fig, bbox_inches='tight', dpi=300, facecolor='white')
        plt.close(fig)
    
    def _create_raw_signals_page(self, pdf: PdfPages):
        """Создание страницы с исходными сигналами"""
        fig = plt.figure(figsize=(8.27, 11.69), dpi=300)
        fig.patch.set_facecolor('white')
        
        raw_data = self.report_data['raw_data']
        sampling_rate = self.report_data['sampling_rate']
        channel_names = self.report_data['channel_names']
        
        # Выбираем только каналы A0 и A2, исключаем служебные каналы
        selected_channels = []
        selected_indices = []
        for i, name in enumerate(channel_names):
            # Исключаем каналы с "Время" в названии и выбираем только A0 и A2
            if name in ['A0', 'A2'] and 'Время' not in name and 'время' not in name:
                selected_channels.append(name)
                selected_indices.append(i)
        
        n_channels = len(selected_channels)
        if n_channels == 0:
            # Если A0 и A2 не найдены, используем первые 2 канала (кроме "Время")
            n_channels = 0
            for i, name in enumerate(channel_names):
                if 'Время' not in name and 'время' not in name and n_channels < 2:
                    selected_indices.append(i)
                    selected_channels.append(name)
                    n_channels += 1
        
        # Создаем массив отсчетов (без времени)
        samples = np.arange(raw_data.shape[1])
        
        # Создание субплотов (заголовок + каналы)
        gs = GridSpec(n_channels + 1, 1, figure=fig, 
                     height_ratios=[0.1] + [1] * n_channels,
                     hspace=0.3)
        
        # Заголовок
        title_ax = fig.add_subplot(gs[0, 0])
        title_ax.text(0.5, 0.5, 'Исходные сигналы',
                     ha='center', va='center', fontsize=16, fontweight='bold',
                     transform=title_ax.transAxes)
        title_ax.axis('off')
        
        # Графики сигналов
        for idx, ch_idx in enumerate(selected_indices):
            ax = fig.add_subplot(gs[idx + 1, 0])
            
            # Ограничиваем отображение первыми 5000 отсчетами для лучшей читаемости
            max_samples = min(5000, len(samples))
            display_samples = samples[:max_samples]
            display_data = raw_data[ch_idx][:max_samples]
            
            ax.plot(display_samples, display_data, 'b', linewidth=0.8, alpha=0.9)
            ax.set_ylabel(f'{selected_channels[idx]}', rotation=0, ha='right', va='center', 
                         fontsize=10, fontweight='bold')
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.set_xlim(0, max_samples)
            ax.set_xlabel('Отсчеты', fontsize=9)
            
            # Улучшаем форматирование осей
            ax.tick_params(axis='both', which='major', labelsize=8)
        
        try:
            plt.tight_layout()
        except:
            pass  # Игнорируем предупреждения tight_layout
        pdf.savefig(fig, bbox_inches='tight', dpi=300, facecolor='white')
        plt.close(fig)
    
    def _create_processed_signals_page(self, pdf: PdfPages):
        """Создание страницы с обработанными сигналами"""
        fig = plt.figure(figsize=(8.27, 11.69), dpi=300)
        fig.patch.set_facecolor('white')
        
        processed_data = self.report_data['processed_data']
        sampling_rate = self.report_data['sampling_rate']
        channel_names = self.report_data['channel_names']
        
        # Выбираем только каналы A0 и A2, исключаем служебные каналы
        selected_channels = []
        selected_indices = []
        for i, name in enumerate(channel_names):
            # Исключаем каналы с "Время" в названии и выбираем только A0 и A2
            if name in ['A0', 'A2'] and 'Время' not in name and 'время' not in name:
                selected_channels.append(name)
                selected_indices.append(i)
        
        n_channels = len(selected_channels)
        if n_channels == 0:
            # Если A0 и A2 не найдены, используем первые 2 канала (кроме "Время")
            n_channels = 0
            for i, name in enumerate(channel_names):
                if 'Время' not in name and 'время' not in name and n_channels < 2:
                    selected_indices.append(i)
                    selected_channels.append(name)
                    n_channels += 1
        
        # Создаем массив отсчетов (без времени)
        samples = np.arange(processed_data.shape[1])
        
        # Создание субплотов (заголовок + каналы)
        gs = GridSpec(n_channels + 1, 1, figure=fig, 
                     height_ratios=[0.1] + [1] * n_channels,
                     hspace=0.3)
        
        # Заголовок
        title_ax = fig.add_subplot(gs[0, 0])
        title_ax.text(0.5, 0.5, 'ОБРАБОТАННЫЕ СИГНАЛЫ ЭЭГ', 
                     ha='center', va='center', fontsize=16, fontweight='bold',
                     transform=title_ax.transAxes)
        title_ax.axis('off')
        
        # Графики сигналов
        for idx, ch_idx in enumerate(selected_indices):
            ax = fig.add_subplot(gs[idx + 1, 0])
            
            # Ограничиваем отображение первыми 5000 отсчетами
            max_samples = min(5000, len(samples))
            display_samples = samples[:max_samples]
            display_data = processed_data[ch_idx][:max_samples]
            
            ax.plot(display_samples, display_data, 'g', linewidth=0.8, alpha=0.9)
            ax.set_ylabel(f'{selected_channels[idx]}', rotation=0, ha='right', va='center', 
                         fontsize=10, fontweight='bold')
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.set_xlim(0, max_samples)
            ax.set_xlabel('Отсчеты', fontsize=9)
            
            # Улучшаем форматирование осей
            ax.tick_params(axis='both', which='major', labelsize=8)
        
        try:
            plt.tight_layout()
        except:
            pass  # Игнорируем предупреждения tight_layout
        pdf.savefig(fig, bbox_inches='tight', dpi=300, facecolor='white')
        plt.close(fig)
    
    def _create_spectral_analysis_page(self, pdf: PdfPages):
        """Создание страницы со спектральным анализом"""
        fig = plt.figure(figsize=(8.27, 11.69), dpi=300)
        fig.patch.set_facecolor('white')
        
        analysis_results = self.report_data['analysis_results']
        
        # Создание сетки для графиков с правильными отступами
        gs = GridSpec(4, 2, figure=fig, 
                     height_ratios=[0.1, 1.2, 1, 0.6],
                     hspace=0.4, wspace=0.3)
        
        # Заголовок
        title_ax = fig.add_subplot(gs[0, :])
        title_ax.text(0.5, 0.5, 'СПЕКТРАЛЬНЫЙ АНАЛИЗ', 
                     ha='center', va='center', fontsize=16, fontweight='bold',
                     transform=title_ax.transAxes)
        title_ax.axis('off')
        
        # График спектра мощности
        ax1 = fig.add_subplot(gs[1, :])
        frequencies = analysis_results['frequencies']
        power_spectrum = analysis_results['power_spectrum']
        
        ax1.semilogy(frequencies, power_spectrum, 'r', linewidth=2, alpha=0.8)
        ax1.set_xlabel('Частота (Гц)', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Мощность (мкВ²/Гц)', fontsize=12, fontweight='bold')
        ax1.set_title('Спектр мощности сигнала ЭЭГ', fontsize=14, fontweight='bold', pad=15)
        ax1.grid(True, alpha=0.3, linestyle='--')
        ax1.set_xlim(0, 40)
        
        # Выделение ритмов на спектре с улучшенными цветами
        rhythm_bands = {
            'δ (delta)': (0.5, 4, '#1f77b4'),
            'θ (theta)': (4, 8, '#2ca02c'),
            'α (alpha)': (8, 13, '#d62728'),
            'β (beta)': (13, 30, '#ff7f0e'),
            'γ (gamma)': (30, 40, '#9467bd')
        }
        
        for rhythm, (low, high, color) in rhythm_bands.items():
            ax1.axvspan(low, high, alpha=0.2, color=color, label=rhythm)
        
        ax1.legend(loc='upper right', fontsize=10, framealpha=0.9)
        ax1.tick_params(axis='both', which='major', labelsize=10)
        
        # График относительной мощности ритмов
        ax2 = fig.add_subplot(gs[2, 0])
        rhythms = list(analysis_results['relative_power'].keys())
        powers = list(analysis_results['relative_power'].values())
        colors = ['#1f77b4', '#2ca02c', '#d62728', '#ff7f0e', '#9467bd']
        
        bars = ax2.bar(rhythms, powers, color=colors[:len(rhythms)], alpha=0.8, edgecolor='black', linewidth=0.5)
        ax2.set_ylabel('Относительная мощность', fontsize=11, fontweight='bold')
        ax2.set_title('Распределение мощности по ритмам', fontsize=12, fontweight='bold')
        ax2.set_ylim(0, max(powers) * 1.2 if powers else 1)
        ax2.tick_params(axis='both', which='major', labelsize=9)
        ax2.grid(True, alpha=0.3, axis='y')
        
        # Добавление значений на столбцы
        for bar, power in zip(bars, powers):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(powers) * 0.02,
                    f'{power:.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # Круговая диаграмма ритмов
        ax3 = fig.add_subplot(gs[2, 1])
        if powers and sum(powers) > 0:
            wedges, texts, autotexts = ax3.pie(powers, labels=rhythms, colors=colors[:len(rhythms)],
                                              autopct='%1.1f%%', startangle=90, 
                                              textprops={'fontsize': 9})
            ax3.set_title('Процентное соотношение ритмов', fontsize=12, fontweight='bold')
            
            # Улучшаем читаемость процентов
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
        else:
            ax3.text(0.5, 0.5, 'Нет данных для\nотображения', 
                    ha='center', va='center', transform=ax3.transAxes,
                    fontsize=12, style='italic')
            ax3.set_title('Процентное соотношение ритмов', fontsize=12, fontweight='bold')
        
        # Статистика спектрального анализа
        stats_ax = fig.add_subplot(gs[3, :])
        
        # Формируем текст статистики
        analysis = self.report_data['analysis_results']
        spectral_stats = f"""СТАТИСТИКА СПЕКТРАЛЬНОГО АНАЛИЗА:
        
Доминирующий ритм: {analysis.get('dominant_rhythm', 'N/A')}
Спектральная энтропия: {analysis.get('spectral_entropy', 0):.3f}
Пиковая частота: {analysis.get('peak_frequency', 0):.2f} Гц

Относительная мощность ритмов:"""
        
        if 'relative_power' in analysis:
            for rhythm, power in analysis['relative_power'].items():
                spectral_stats += f"\n  • {rhythm}: {power:.3f} ({power*100:.1f}%)"
        
        stats_ax.text(0.02, 0.95, spectral_stats, transform=stats_ax.transAxes,
                     fontsize=10, verticalalignment='top', fontfamily='monospace',
                     bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", 
                              alpha=0.8, edgecolor='orange', linewidth=1))
        stats_ax.axis('off')
        
        try:
            plt.tight_layout()
        except:
            pass  # Игнорируем предупреждения tight_layout
        pdf.savefig(fig, bbox_inches='tight', dpi=300, facecolor='white')
        plt.close(fig)
    
    def _create_rhythm_analysis_page(self, pdf: PdfPages):
        """Создание страницы с детальным анализом ритмов"""
        fig = plt.figure(figsize=(8.27, 11.69), dpi=300)
        fig.patch.set_facecolor('white')
        
        analysis = self.report_data['analysis_results']
        
        # Заголовок
        ax_title = fig.add_subplot(6, 1, 1)
        ax_title.text(0.5, 0.5, 'ДЕТАЛЬНЫЙ АНАЛИЗ РИТМОВ', 
                     ha='center', va='center', fontsize=16, fontweight='bold',
                     transform=ax_title.transAxes)
        ax_title.axis('off')
        
        # Информация о ритмах
        rhythm_info_ax = fig.add_subplot(6, 1, (2, 6))
        rhythm_info_ax.axis('off')
        
        rhythm_text = "АНАЛИЗ МОЗГОВЫХ РИТМОВ:\n\n"
        
        if 'rhythm_analysis' in analysis:
            for rhythm, data in analysis['rhythm_analysis'].items():
                rhythm_text += f"{rhythm.upper()} ({data['freq_range'][0]}-{data['freq_range'][1]} Гц):\n"
                rhythm_text += f"  • Абсолютная мощность: {data['power']:.6f}\n"
                rhythm_text += f"  • Относительная мощность: {data['relative_power']:.3f} ({data['relative_power']*100:.1f}%)\n"
                rhythm_text += f"  • Пиковая частота: {data['peak_freq']:.2f} Гц\n\n"
        
        rhythm_text += f"\nДОМИНИРУЮЩИЙ РИТМ: {analysis.get('dominant_rhythm', 'N/A')}\n"
        rhythm_text += f"СПЕКТРАЛЬНАЯ ЭНТРОПИЯ: {analysis.get('spectral_entropy', 0):.3f}"
        
        rhythm_info_ax.text(0.1, 0.95, rhythm_text, 
                           ha='left', va='top', fontsize=10,
                           transform=rhythm_info_ax.transAxes, fontfamily='monospace',
                           bbox=dict(boxstyle="round,pad=0.8", facecolor="lightyellow", 
                                    edgecolor="orange", linewidth=1, alpha=0.8))
        
        try:
            plt.tight_layout()
        except:
            pass
        pdf.savefig(fig, bbox_inches='tight', dpi=300, facecolor='white')
        plt.close(fig)
    
    def _create_recommendations_page(self, pdf: PdfPages):
        """Создание страницы с рекомендациями и выводами"""
        fig = plt.figure(figsize=(8.27, 11.69), dpi=300)
        fig.patch.set_facecolor('white')
        
        # Создаем основную ось для размещения текста
        ax = fig.add_subplot(111)
        ax.axis('off')
        
        recommendations = self.report_data['recommendations']
        
        # Заголовок
        ax.text(0.5, 0.95, 'Заключение',
                ha='center', va='top', fontsize=18, fontweight='bold',
                transform=ax.transAxes, color='navy')
        
        # Декоративная линия под заголовком
        line_y = 0.92
        ax.plot([0.1, 0.9], [line_y, line_y], color='navy', linewidth=2, 
               transform=ax.transAxes)
        
        # Основной текст заключения
        recommendations = self.report_data['recommendations']
        analysis = self.report_data['analysis_results']
        
        conclusion_text = f"""Итог:

{recommendations['general'].get('summary', 'Нет данных')}

Доминирующий ритм: {recommendations['general'].get('dominant_rhythm', 'N/A')}
Уровень релаксации: {recommendations['general'].get('relaxation_level', 'N/A')}

ДЕТАЛЬНЫЙ АНАЛИЗ РИТМОВ:
"""
        
        for rhythm, details in recommendations.get('rhythm_details', {}).items():
            conclusion_text += f"\n{rhythm.upper()}:\n"
            conclusion_text += f"  Состояние: {details.get('state', 'N/A')}\n"
            conclusion_text += f"  {details.get('recommendation', 'N/A')}\n"
        
        if 'specific_recommendations' in recommendations:
            conclusion_text += "Рекомендации:\n"
            for rec in recommendations['specific_recommendations']:
                conclusion_text += f"• {rec}\n"
        
        # Размещаем текст в прокручиваемом блоке
        ax.text(0.05, 0.88, conclusion_text, 
                ha='left', va='top', fontsize=9, 
                transform=ax.transAxes, wrap=True,
                bbox=dict(boxstyle="round,pad=0.8", facecolor="#f8f9fa", 
                         edgecolor="navy", linewidth=1.5, alpha=0.9))
      
  
        ax.axis('off')
        
        try:
            plt.tight_layout()
        except:
            pass
        pdf.savefig(fig, bbox_inches='tight', dpi=300, facecolor='white')
        plt.close(fig)
