class FilterValidator:

    @staticmethod
    def validate_bandpass_params(low_freq, high_freq, sampling_rate):

        warnings = []
        nyquist = sampling_rate / 2

        orig_low = low_freq
        orig_high = high_freq

        if low_freq <= 0:
            low_freq = 0.1
            warnings.append(f"Нижняя частота была меньше или равна 0, установлена в {low_freq} Гц")

        if high_freq <= 0:
            high_freq = 40.0
            warnings.append(f"Верхняя частота была меньше или равна 0, установлена в {high_freq} Гц")

        if low_freq >= high_freq:
            if orig_low > orig_high:
                low_freq, high_freq = high_freq, low_freq
                warnings.append(f"Частоты были переставлены местами: {orig_low} <-> {orig_high}")
            else:
                low_freq = 1.0
                high_freq = 40.0
                warnings.append(
                    f"Некорректный диапазон частот, установлены значения по умолчанию: {low_freq}-{high_freq} Гц")

        if high_freq >= nyquist:
            high_freq = nyquist * 0.95
            warnings.append(f"Верхняя частота превышала частоту Найквиста, установлена в {high_freq:.2f} Гц")

        min_separation = 0.5  # Hz
        if (high_freq - low_freq) < min_separation:
            center = (low_freq + high_freq) / 2
            low_freq = max(0.1, center - min_separation / 2)
            high_freq = min(nyquist * 0.95, center + min_separation / 2)
            warnings.append(f"Слишком узкий диапазон частот, расширен до {low_freq:.2f}-{high_freq:.2f} Гц")

        low_norm = low_freq / nyquist
        high_norm = high_freq / nyquist

        if low_norm < 0.001:
            low_freq = nyquist * 0.001
            warnings.append(f"Нормализованная нижняя частота слишком мала, установлена в {low_freq:.3f} Гц")

        if high_norm > 0.999:
            high_freq = nyquist * 0.999
            warnings.append(f"Нормализованная верхняя частота слишком велика, установлена в {high_freq:.3f} Гц")

        return low_freq, high_freq, warnings

    @staticmethod
    def validate_notch_params(notch_freq, sampling_rate):

        warnings = []
        nyquist = sampling_rate / 2

        if notch_freq <= 0:
            notch_freq = 50.0
            warnings.append(f"Частота notch фильтра была меньше или равна 0, установлена в {notch_freq} Гц")

        if notch_freq >= nyquist:
            notch_freq = nyquist * 0.8
            warnings.append(f"Частота notch фильтра превышала частоту Найквиста, установлена в {notch_freq:.2f} Гц")

        freq_norm = notch_freq / nyquist

        if freq_norm < 0.001:
            notch_freq = nyquist * 0.001
            warnings.append(f"Нормализованная частота notch фильтра слишком мала, установлена в {notch_freq:.3f} Гц")

        if freq_norm > 0.999:
            notch_freq = nyquist * 0.999
            warnings.append(f"Нормализованная частота notch фильтра слишком велика, установлена в {notch_freq:.3f} Гц")

        return notch_freq, warnings

    @staticmethod
    def validate_rhythm_bands(rhythm_bands, sampling_rate):

        warnings = []
        corrected_bands = {}
        nyquist = sampling_rate / 2

        for rhythm, (low, high) in rhythm_bands.items():
            orig_low, orig_high = low, high

            low, high, band_warnings = FilterValidator.validate_bandpass_params(
                low, high, sampling_rate
            )

            for warning in band_warnings:
                warnings.append(f"{rhythm.capitalize()}: {warning}")

            corrected_bands[rhythm] = (low, high)

        return corrected_bands, warnings

    @staticmethod
    def get_safe_filter_params(sampling_rate):

        nyquist = sampling_rate / 2

        safe_params = {
            'low_freq': max(0.5, nyquist * 0.002),  # At least 0.5 Hz or 0.2% of Nyquist
            'high_freq': min(40.0, nyquist * 0.8),  # At most 40 Hz or 80% of Nyquist
            'notch_freq': min(50.0, nyquist * 0.4)  # At most 50 Hz or 40% of Nyquist
        }

        if (safe_params['high_freq'] - safe_params['low_freq']) < 1.0:
            center = (safe_params['low_freq'] + safe_params['high_freq']) / 2
            safe_params['low_freq'] = max(0.1, center - 0.5)
            safe_params['high_freq'] = min(nyquist * 0.95, center + 0.5)

        return safe_params

    @staticmethod
    def check_sampling_rate_adequacy(max_freq, sampling_rate, min_ratio=2.5):

        required_rate = max_freq * min_ratio
        is_adequate = sampling_rate >= required_rate

        if not is_adequate:
            warning = (f"Частота дискретизации {sampling_rate} Гц недостаточна для анализа частот до {max_freq} Гц. "
                       f"Рекомендуется минимум {required_rate:.0f} Гц.")
            return False, required_rate, warning

        return True, sampling_rate, None


def apply_safe_filter_params(preprocessor_instance, sampling_rate):
    validator = FilterValidator()
    safe_params = validator.get_safe_filter_params(sampling_rate)

    print(f"Применение безопасных параметров фильтра для частоты дискретизации {sampling_rate} Гц:")
    print(f"  Полосовой фильтр: {safe_params['low_freq']:.2f} - {safe_params['high_freq']:.2f} Гц")
    print(f"  Notch фильтр: {safe_params['notch_freq']:.2f} Гц")

    return safe_params
