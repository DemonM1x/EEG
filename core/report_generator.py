from datetime import datetime
from typing import Dict, Any, Optional

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.gridspec import GridSpec

matplotlib.use('Agg')  # Use backend without GUI for better PDF quality


class EEGReportGenerator:

    def __init__(self):
        self.report_data = {}

    def generate_report(self, raw_data: np.ndarray, processed_data: np.ndarray,
                        current_analysis: Dict[str, Any], sampling_rate: float,
                        channel_names: list, output_path: str,
                        config: Optional[Dict] = None) -> bool:
        try:
            # Extract analysis results and generate recommendations
            analysis_results = current_analysis.get('analysis', {})

            # Generate recommendations using existing analyzer logic
            recommendations = self._generate_recommendations_from_analysis(analysis_results)

            # Set data for report
            self.report_data = {
                'raw_data': raw_data,
                'processed_data': processed_data,
                'analysis_results': analysis_results,
                'sampling_rate': sampling_rate,
                'channel_names': channel_names,
                'recommendations': recommendations,
                'timestamp': datetime.now()
            }

            # Generate the actual report
            return self._generate_pdf_report(output_path, config.get('patient_info') if config else None)

        except Exception as e:
            print(f"Error creating report: {e}")
            return False

    def _generate_recommendations_from_analysis(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        recommendations = {
            'general': {},
            'rhythm_details': {},
            'specific_recommendations': []
        }

        # Get rhythm analysis data
        if 'rhythm_analysis' in analysis_results:
            rhythm_analysis = analysis_results['rhythm_analysis']
            dominant_rhythm = analysis_results.get('dominant_rhythm', 'unknown')

            # Generate rhythm details
            for rhythm, data in rhythm_analysis.items():
                relative_power = data.get('relative_power', 0)
                state, recommendation = self._analyze_rhythm_state(rhythm, relative_power)

                recommendations['rhythm_details'][rhythm] = {
                    'state': state,
                    'recommendation': recommendation,
                    'relative_power': relative_power
                }

            # General recommendations
            recommendations['general'] = {
                'summary': f'Dominant rhythm: {dominant_rhythm}',
                'dominant_rhythm': dominant_rhythm,
                'relaxation_level': self._determine_relaxation_level(rhythm_analysis),
                'spectral_entropy': analysis_results.get('spectral_entropy', 0)
            }

            # Specific recommendations
            recommendations['specific_recommendations'] = self._get_specific_recommendations(rhythm_analysis)

        return recommendations

    def _analyze_rhythm_state(self, rhythm: str, relative_power: float) -> tuple:
        normal_ranges = {
            'delta': (0.05, 0.25),
            'theta': (0.05, 0.15),
            'alpha': (0.10, 0.30),
            'beta': (0.15, 0.25),
            'gamma': (0.05, 0.15)
        }

        low, high = normal_ranges.get(rhythm, (0.05, 0.25))

        if relative_power < low:
            return "LOW", f"Low {rhythm} rhythm activity"
        elif relative_power > high:
            return "HIGH", f"High {rhythm} rhythm activity"
        else:
            return "NORMAL", f"Normal {rhythm} rhythm activity"

    def _determine_relaxation_level(self, rhythm_analysis: Dict) -> str:
        alpha_power = rhythm_analysis.get('alpha', {}).get('relative_power', 0)
        beta_power = rhythm_analysis.get('beta', {}).get('relative_power', 0)

        if alpha_power > 0.25:
            return "HIGH"
        elif beta_power > 0.3:
            return "LOW"
        else:
            return "MEDIUM"

    def _get_specific_recommendations(self, rhythm_analysis: Dict) -> list:
        recommendations = []

        alpha_power = rhythm_analysis.get('alpha', {}).get('relative_power', 0)
        beta_power = rhythm_analysis.get('beta', {}).get('relative_power', 0)

        if alpha_power > 0.3:
            recommendations.append("High alpha activity - good state for relaxation")

        if beta_power > 0.35:
            recommendations.append("Elevated beta activity - possible stress or high concentration")

        return recommendations

    def _generate_pdf_report(self, output_path: str, patient_info: Optional[Dict] = None) -> bool:
        try:
            with PdfPages(output_path) as pdf:
                # Title page
                self._create_title_page(pdf, patient_info)

                # Signal analysis page
                self._create_signal_analysis_page(pdf)

                # Spectral analysis page
                self._create_spectral_analysis_page(pdf)

                # Recommendations page
                self._create_recommendations_page(pdf)

                # PDF metadata
                d = pdf.infodict()
                d['Title'] = 'EEG Analysis Report'
                d['Author'] = 'EEG Analyzer'
                d['Subject'] = 'Electroencephalogram Analysis'
                d['Keywords'] = 'EEG, Brain Activity, Signal Processing'
                d['CreationDate'] = datetime.now()

            return True

        except Exception as e:
            print(f"Error creating PDF report: {e}")
            return False

    def _create_title_page(self, pdf: PdfPages, patient_info: Optional[Dict]):
        fig = plt.figure(figsize=(8.27, 11.69), dpi=300)
        fig.patch.set_facecolor('white')

        ax = fig.add_subplot(111)
        ax.axis('off')

        # Title
        ax.text(0.5, 0.90, 'EEG Analysis Report',
                ha='center', va='center', fontsize=24, fontweight='bold',
                transform=ax.transAxes)

        ax.text(0.5, 0.85, 'Electroencephalogram Analysis Report',
                ha='center', va='center', fontsize=16, style='italic',
                transform=ax.transAxes, color='gray')

        # Recording information
        y_pos = 0.70
        ax.text(0.5, y_pos, 'RECORDING PARAMETERS',
                ha='center', va='center', fontsize=16, fontweight='bold',
                transform=ax.transAxes)
        y_pos -= 0.06

        recording_info = [
            ('Analysis date and time', self.report_data['timestamp'].strftime('%d.%m.%Y %H:%M:%S')),
            ('Sampling rate', f"{self.report_data['sampling_rate']:.0f} Hz"),
            ('Number of channels', str(len(self.report_data['channel_names']))),
            ('Recording duration',
             f"{self.report_data['raw_data'].shape[1] / self.report_data['sampling_rate']:.1f} sec"),
            ('Channels', ', '.join(self.report_data['channel_names'][:6]))
        ]

        for label, value in recording_info:
            ax.text(0.25, y_pos, f'{label}:', ha='left', va='center',
                    fontsize=12, fontweight='bold', transform=ax.transAxes)
            ax.text(0.75, y_pos, str(value), ha='right', va='center',
                    fontsize=12, transform=ax.transAxes)
            y_pos -= 0.04

        # Decorative line
        line_y = 0.25
        ax.plot([0.1, 0.9], [line_y, line_y], color='navy', linewidth=2,
                transform=ax.transAxes)

        # Logo
        ax.text(0.5, 0.20, 'EEG ANALYZER',
                ha='center', va='center', fontsize=20, fontweight='bold',
                color='navy', transform=ax.transAxes)

        ax.text(0.5, 0.15, 'Electroencephalogram Analysis System',
                ha='center', va='center', fontsize=12, style='italic',
                transform=ax.transAxes, color='gray')

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        pdf.savefig(fig, bbox_inches='tight', dpi=300, facecolor='white')
        plt.close(fig)

    def _create_signal_analysis_page(self, pdf: PdfPages):
        fig = plt.figure(figsize=(8.27, 11.69), dpi=300)
        fig.patch.set_facecolor('white')

        raw_data = self.report_data['raw_data']
        processed_data = self.report_data['processed_data']
        sampling_rate = self.report_data['sampling_rate']
        channel_names = self.report_data['channel_names']

        # Create subplots
        gs = GridSpec(3, 2, figure=fig,
                      height_ratios=[0.1, 1, 1],
                      hspace=0.4, wspace=0.3)

        # Title
        title_ax = fig.add_subplot(gs[0, :])
        title_ax.text(0.5, 0.5, 'SIGNAL ANALYSIS',
                      ha='center', va='center', fontsize=16, fontweight='bold',
                      transform=title_ax.transAxes)
        title_ax.axis('off')

        # Raw signal plot
        ax1 = fig.add_subplot(gs[1, 0])
        self._plot_signal_sample(ax1, raw_data, sampling_rate, channel_names,
                                 "Raw Signal", 'blue', max_time=10)

        # Processed signal plot
        ax2 = fig.add_subplot(gs[1, 1])
        self._plot_signal_sample(ax2, processed_data, sampling_rate, channel_names,
                                 "Processed Signal", 'green', max_time=10)

        # Statistics
        stats_ax = fig.add_subplot(gs[2, :])
        stats_text = self._get_signal_statistics()
        stats_ax.text(0.02, 0.95, stats_text, transform=stats_ax.transAxes,
                      fontsize=10, verticalalignment='top', fontfamily='monospace',
                      bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue",
                                alpha=0.7, edgecolor='navy', linewidth=1))
        stats_ax.axis('off')

        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight', dpi=300, facecolor='white')
        plt.close(fig)

    def _plot_signal_sample(self, ax, data, sampling_rate, channel_names, title, color, max_time=10):
        try:
            if len(data) > 0:
                # Use first channel for display
                channel_data = data[0] if data.ndim > 1 else data
                time_axis = np.arange(len(channel_data)) / sampling_rate

                # Limit to max_time seconds
                time_mask = time_axis <= max_time
                display_time = time_axis[time_mask]
                display_data = channel_data[time_mask]

                ax.plot(display_time, display_data, color=color, linewidth=0.8, alpha=0.9)
                ax.set_xlabel('Time (s)')
                ax.set_ylabel('Amplitude (μV)')
                ax.set_title(f'{title} - {channel_names[0] if channel_names else "Channel 1"}')
                ax.grid(True, alpha=0.3)
                ax.set_xlim(0, max_time)
            else:
                ax.text(0.5, 0.5, 'No data available',
                        ha='center', va='center', transform=ax.transAxes)
                ax.set_title(title)
        except Exception as e:
            ax.text(0.5, 0.5, f'Error: {str(e)}',
                    ha='center', va='center', transform=ax.transAxes)
            ax.set_title(title)

    def _create_spectral_analysis_page(self, pdf: PdfPages):
        fig = plt.figure(figsize=(8.27, 11.69), dpi=300)
        fig.patch.set_facecolor('white')

        analysis_results = self.report_data['analysis_results']

        # Create grid for plots
        gs = GridSpec(3, 2, figure=fig,
                      height_ratios=[0.1, 1.2, 1],
                      hspace=0.4, wspace=0.3)

        # Title
        title_ax = fig.add_subplot(gs[0, :])
        title_ax.text(0.5, 0.5, 'SPECTRAL ANALYSIS',
                      ha='center', va='center', fontsize=16, fontweight='bold',
                      transform=title_ax.transAxes)
        title_ax.axis('off')

        # Power spectrum plot
        ax1 = fig.add_subplot(gs[1, :])
        self._plot_power_spectrum(ax1, analysis_results)

        # Rhythm power bar chart
        ax2 = fig.add_subplot(gs[2, 0])
        self._plot_rhythm_powers(ax2, analysis_results)

        # Rhythm power pie chart
        ax3 = fig.add_subplot(gs[2, 1])
        self._plot_rhythm_pie(ax3, analysis_results)

        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight', dpi=300, facecolor='white')
        plt.close(fig)

    def _plot_power_spectrum(self, ax, analysis_results):
        try:
            frequencies = analysis_results.get('frequencies', [])
            power_spectrum = analysis_results.get('power_spectrum', [])

            if (len(frequencies) > 0 and len(power_spectrum) > 0 and
                    len(frequencies) == len(power_spectrum)):

                frequencies = np.array(frequencies)
                power_spectrum = np.array(power_spectrum)

                # Filter for 0-50 Hz range
                freq_mask = (frequencies >= 0) & (frequencies <= 50)
                freq_filtered = frequencies[freq_mask]
                power_filtered = power_spectrum[freq_mask]

                if len(freq_filtered) > 0:
                    ax.semilogy(freq_filtered, power_filtered, 'r', linewidth=2, alpha=0.8)

                    # Highlight rhythm bands
                    rhythm_bands = {
                        'δ (delta)': (0.5, 4, '#1f77b4'),
                        'θ (theta)': (4, 8, '#2ca02c'),
                        'α (alpha)': (8, 13, '#d62728'),
                        'β (beta)': (13, 30, '#ff7f0e'),
                        'γ (gamma)': (30, 100, '#9467bd')
                    }

                    for rhythm, (low, high, color) in rhythm_bands.items():
                        ax.axvspan(low, high, alpha=0.2, color=color, label=rhythm)

                    ax.legend(loc='upper right', fontsize=10)
                    ax.set_xlim(0, 50)
                else:
                    ax.text(0.5, 0.5, 'Insufficient data for spectrum display',
                            ha='center', va='center', transform=ax.transAxes)
            else:
                ax.text(0.5, 0.5, 'Spectrum data unavailable',
                        ha='center', va='center', transform=ax.transAxes)

            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Power (μV²/Hz)')
            ax.set_title('EEG Signal Power Spectrum')
            ax.grid(True, alpha=0.3)

        except Exception as e:
            ax.text(0.5, 0.5, f'Error displaying spectrum: {str(e)}',
                    ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Power Spectrum')

    def _plot_rhythm_powers(self, ax, analysis_results):
        try:
            relative_power = analysis_results.get('relative_power', {})

            if relative_power:
                rhythms = list(relative_power.keys())
                powers = list(relative_power.values())
                colors = ['#1f77b4', '#2ca02c', '#d62728', '#ff7f0e', '#9467bd']

                bars = ax.bar(rhythms, powers, color=colors[:len(rhythms)], alpha=0.7)

                # Add value labels
                for bar, power in zip(bars, powers):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width() / 2., height,
                            f'{power:.3f}', ha='center', va='bottom', fontsize=9)

                ax.set_ylabel('Relative Power')
                ax.set_title('Rhythm Power Distribution')
                ax.grid(True, alpha=0.3, axis='y')
            else:
                ax.text(0.5, 0.5, 'Rhythm power data\nunavailable',
                        ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Rhythm Power Distribution')

        except Exception as e:
            ax.text(0.5, 0.5, f'Error: {str(e)}',
                    ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Rhythm Power Distribution')

    def _plot_rhythm_pie(self, ax, analysis_results):
        try:
            relative_power = analysis_results.get('relative_power', {})

            if relative_power and sum(relative_power.values()) > 0:
                rhythms = list(relative_power.keys())
                powers = list(relative_power.values())
                colors = ['#1f77b4', '#2ca02c', '#d62728', '#ff7f0e', '#9467bd']

                wedges, texts, autotexts = ax.pie(powers, labels=rhythms,
                                                  colors=colors[:len(rhythms)],
                                                  autopct='%1.1f%%', startangle=90)

                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
            else:
                ax.text(0.5, 0.5, 'No data for\ndisplay',
                        ha='center', va='center', transform=ax.transAxes)

            ax.set_title('Rhythm Power Percentage')

        except Exception as e:
            ax.text(0.5, 0.5, f'Error: {str(e)}',
                    ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Rhythm Power Percentage')

    def _create_recommendations_page(self, pdf: PdfPages):
        fig = plt.figure(figsize=(8.27, 11.69), dpi=300)
        fig.patch.set_facecolor('white')

        ax = fig.add_subplot(111)
        ax.axis('off')

        recommendations = self.report_data['recommendations']

        # Title
        ax.text(0.5, 0.95, 'Analysis Results and Recommendations',
                ha='center', va='top', fontsize=18, fontweight='bold',
                transform=ax.transAxes, color='navy')

        # Generate conclusion text
        conclusion_text = self._generate_conclusion()

        # Display conclusion
        ax.text(0.05, 0.88, conclusion_text,
                ha='left', va='top', fontsize=10,
                transform=ax.transAxes, wrap=True,
                bbox=dict(boxstyle="round,pad=0.8", facecolor="#f8f9fa",
                          edgecolor="navy", linewidth=1.5, alpha=0.9))

        # Signature and date
        signature_text = f"""
Report generated automatically by EEG Analyzer
Creation date: {datetime.now().strftime("%d.%m.%Y at %H:%M")}

NOTICE: This analysis is for informational purposes only 
and does not replace professional medical consultation."""

        ax.text(0.5, 0.08, signature_text,
                ha='center', va='bottom', fontsize=9, style='italic',
                transform=ax.transAxes, color='gray',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow",
                          alpha=0.7, edgecolor='orange', linewidth=1))

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        pdf.savefig(fig, bbox_inches='tight', dpi=300, facecolor='white')
        plt.close(fig)

    def _generate_conclusion(self) -> str:
        recommendations = self.report_data['recommendations']

        general = recommendations.get('general', {})
        dominant_rhythm = general.get('dominant_rhythm', 'Unknown')
        relaxation_level = general.get('relaxation_level', 'Unknown')
        summary = general.get('summary', 'Data not available')

        conclusion = f"""EEG ANALYSIS RESULTS

GENERAL STATE:
{summary}

DOMINANT RHYTHM: {dominant_rhythm.upper()}

RELAXATION LEVEL: {relaxation_level}

DETAILED RHYTHM ANALYSIS:"""

        # Add rhythm details
        if 'rhythm_details' in recommendations:
            for rhythm, details in recommendations['rhythm_details'].items():
                state_symbol = "🔴" if details['state'] == 'HIGH' else "🔵" if details['state'] == 'LOW' else "🟢"
                conclusion += f"""
{state_symbol} {rhythm.upper()} rhythm:
   Power: {details['relative_power']:.3f} ({details['state']})
   Recommendation: {details['recommendation']}"""

        # Add specific recommendations
        conclusion += f"""

SPECIFIC RECOMMENDATIONS:"""

        if 'specific_recommendations' in recommendations and recommendations['specific_recommendations']:
            for i, rec in enumerate(recommendations['specific_recommendations'], 1):
                conclusion += f"""
{i}. {rec}"""
        else:
            conclusion += """
• No additional specific recommendations required"""

        # Technical information
        conclusion += f"""

TECHNICAL INFORMATION:
• Sampling rate: {self.report_data['sampling_rate']:.0f} Hz
• Number of channels: {len(self.report_data['channel_names'])}
• Recording duration: {self.report_data['raw_data'].shape[1] / self.report_data['sampling_rate']:.1f} sec
• Processing: filtering, artifact removal, normalization"""

        return conclusion

    def _get_signal_statistics(self) -> str:
        raw_data = self.report_data['raw_data']
        processed_data = self.report_data['processed_data']

        stats = f"""SIGNAL STATISTICS:

Raw Signal:
• Mean: {np.mean(raw_data):.2f} μV
• Std Dev: {np.std(raw_data):.2f} μV
• Min/Max: {np.min(raw_data):.2f} / {np.max(raw_data):.2f} μV

Processed Signal:
• Mean: {np.mean(processed_data):.2f} μV
• Std Dev: {np.std(processed_data):.2f} μV
• Min/Max: {np.min(processed_data):.2f} / {np.max(processed_data):.2f} μV

Processing Applied:
• Bandpass filtering (1-40 Hz)
• Notch filter (50 Hz)
• Artifact removal
• DC offset removal"""

        return stats
