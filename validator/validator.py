import mne
import numpy as np
from scipy.stats import pearsonr


class EEGValidator:

    def __init__(self):
        self.comparison_results = {}

    def compare_with_mne(self, data, sampling_rate, channel_names=None):
        try:
            # Создаём MNE Raw объект
            if channel_names is None:
                channel_names = [f'Ch{i + 1}' for i in range(data.shape[0])]

            info = mne.create_info(
                ch_names=channel_names,
                sfreq=sampling_rate,
                ch_types='eeg'
            )

            raw = mne.io.RawArray(data, info, verbose=False)

            # Применяем фильтрацию MNE
            raw_filtered = raw.copy()
            raw_filtered.filter(l_freq=1.0, h_freq=40.0, verbose=False)

            mne_filtered_data = raw_filtered.get_data()

            return {
                'available': True,
                'mne_data': mne_filtered_data,
                'original_data': data,
                'message': 'Данные обработаны с помощью MNE-Python'
            }

        except Exception as e:
            return {
                'available': False,
                'message': f'Ошибка при работе с MNE: {str(e)}'
            }

    def compare_filtering(self, our_filtered, mne_filtered):
        if our_filtered.shape != mne_filtered.shape:
            return {
                'error': 'Размеры данных не совпадают'
            }

        results = {
            'channels': []
        }

        for ch_idx in range(our_filtered.shape[0]):
            our_ch = our_filtered[ch_idx]
            mne_ch = mne_filtered[ch_idx]

            # Корреляция
            correlation, p_value = pearsonr(our_ch, mne_ch)

            # Среднеквадратичная ошибка
            mse = np.mean((our_ch - mne_ch) ** 2)
            rmse = np.sqrt(mse)

            # Средняя абсолютная ошибка
            mae = np.mean(np.abs(our_ch - mne_ch))

            # Нормализованная относительная ошибка (NRMSE)
            # Нормализуем по диапазону сигнала MNE
            signal_range = np.max(mne_ch) - np.min(mne_ch)
            if signal_range > 0:
                nrmse = (rmse / signal_range) * 100
            else:
                nrmse = 0

            # Коэффициент детерминации (R²)
            ss_res = np.sum((mne_ch - our_ch) ** 2)
            ss_tot = np.sum((mne_ch - np.mean(mne_ch)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            results['channels'].append({
                'channel': ch_idx,
                'correlation': correlation,
                'p_value': p_value,
                'rmse': rmse,
                'mae': mae,
                'nrmse': nrmse,
                'r_squared': r_squared
            })

        # Общая статистика
        results['summary'] = {
            'mean_correlation': np.mean([ch['correlation'] for ch in results['channels']]),
            'mean_rmse': np.mean([ch['rmse'] for ch in results['channels']]),
            'mean_mae': np.mean([ch['mae'] for ch in results['channels']]),
            'mean_nrmse': np.mean([ch['nrmse'] for ch in results['channels']]),
            'mean_r_squared': np.mean([ch['r_squared'] for ch in results['channels']])
        }

        return results

    def compare_psd(self, our_psd, mne_psd, freqs):
        correlation, _ = pearsonr(our_psd.flatten(), mne_psd.flatten())

        mse = np.mean((our_psd - mne_psd) ** 2)
        rmse = np.sqrt(mse)

        return {
            'correlation': correlation,
            'rmse': rmse,
            'mean_diff': np.mean(np.abs(our_psd - mne_psd))
        }

    def validate_rhythm_detection(self, detected_rhythms, ground_truth=None):
        if ground_truth is None:
            return {
                'message': 'Ground truth данные не предоставлены'
            }

        # Сравнение с эталонными данными
        results = {}

        for rhythm_name in detected_rhythms.keys():
            if rhythm_name in ground_truth:
                our_power = detected_rhythms[rhythm_name]['power']
                true_power = ground_truth[rhythm_name]['power']

                error = abs(our_power - true_power)
                relative_error = (error / true_power) * 100 if true_power > 0 else 0

                results[rhythm_name] = {
                    'our_power': our_power,
                    'true_power': true_power,
                    'absolute_error': error,
                    'relative_error': relative_error
                }

        return results

    def generate_comparison_report(self, our_data, mne_data, our_filtered, mne_filtered):
        report = []
        report.append("=" * 70)
        report.append("ОТЧЁТ СРАВНЕНИЯ С MNE-PYTHON")
        report.append("=" * 70)
        report.append("")

        # Сравнение фильтрации
        filter_comparison = self.compare_filtering(our_filtered, mne_filtered)

        report.append("СРАВНЕНИЕ ФИЛЬТРАЦИИ:")
        report.append("-" * 70)
        report.append(f"Средняя корреляция: {filter_comparison['summary']['mean_correlation']:.4f}")
        report.append(f"Средний R²: {filter_comparison['summary']['mean_r_squared']:.4f}")
        report.append(f"Средняя RMSE: {filter_comparison['summary']['mean_rmse']:.6f}")
        report.append(f"Средняя MAE: {filter_comparison['summary']['mean_mae']:.6f}")
        report.append(f"Средняя NRMSE: {filter_comparison['summary']['mean_nrmse']:.2f}%")
        report.append("")

        report.append("ПО КАНАЛАМ:")
        for ch_result in filter_comparison['channels']:
            report.append(f"Канал {ch_result['channel']}:")
            report.append(f"Корреляция: {ch_result['correlation']:.4f}")
            report.append(f"R² (коэфф. детерминации): {ch_result['r_squared']:.4f}")
            report.append(f"RMSE: {ch_result['rmse']:.6f}")
            report.append(f"NRMSE: {ch_result['nrmse']:.2f}%")

        return "\n".join(report)

    def compute_mne_psd(self, data, sampling_rate, channel_names=None):
        if not self.mne_available:
            return None

        try:
            import mne

            if channel_names is None:
                channel_names = [f'Ch{i + 1}' for i in range(data.shape[0])]

            info = mne.create_info(
                ch_names=channel_names,
                sfreq=sampling_rate,
                ch_types='eeg'
            )

            raw = mne.io.RawArray(data, info, verbose=False)
            psd, freqs = raw.compute_psd(fmin=0.5, fmax=50, verbose=False).get_data(return_freqs=True)

            return psd, freqs

        except Exception as e:
            print(f"Ошибка вычисления PSD с MNE: {e}")
            return None
