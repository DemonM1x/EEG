#!/usr/bin/env python3
"""
Тестовый скрипт для проверки core real-time функциональности без GUI
"""

import os
import sys
import time

# Добавляем родительскую директорию в Python path для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_imports():
    """Тест импортов модулей"""
    print("=== ТЕСТ ИМПОРТОВ ===")

    try:
        from core.realtime_driver import SyntheticEEGDriver, SerialEEGDriver, EEGSample, EEGSampleBatch
        print("✓ realtime_driver импортирован")

        from core.realtime_controller import RealtimeDataBuffer
        print("✓ realtime_controller импортирован")

        from realtime_work.realtime_recorder import RealtimeEEGRecorder
        print("✓ realtime_recorder импортирован")

        return True

    except ImportError as e:
        print(f"✗ Ошибка импорта: {e}")
        return False


def test_synthetic_driver():
    """Тест синтетического драйвера"""
    print("\n=== ТЕСТ СИНТЕТИЧЕСКОГО ДРАЙВЕРА ===")

    try:
        from core.realtime_driver import SyntheticEEGDriver

        # Создаем драйвер
        driver = SyntheticEEGDriver(sample_rate_hz=10.0)  # Низкая частота для теста
        print("✓ Драйвер создан")

        # Открываем соединение
        driver.open()
        print("✓ Соединение открыто")

        # Получаем несколько образцов
        samples = []
        start_time = time.time()

        for i, sample in enumerate(driver.iter_samples()):
            samples.append(sample)
            print(f"  Образец {i + 1}: t={sample.timestamp:.3f}, amplitudes={[f'{a:.1f}' for a in sample.amplitudes]}")

            if i >= 4:  # Получаем 5 образцов
                break

            if time.time() - start_time > 2:  # Таймаут 2 секунды
                break

        # Закрываем соединение
        driver.close()
        print("✓ Соединение закрыто")

        if len(samples) > 0:
            print(f"✓ Получено {len(samples)} образцов")
            return True
        else:
            print("✗ Образцы не получены")
            return False

    except Exception as e:
        print(f"✗ Ошибка теста драйвера: {e}")
        return False


def test_data_buffer():
    """Тест буфера данных"""
    print("\n=== ТЕСТ БУФЕРА ДАННЫХ ===")

    try:
        from core.realtime_controller import RealtimeDataBuffer
        from core.realtime_driver import EEGSample, EEGSampleBatch

        # Создаем буфер
        buffer = RealtimeDataBuffer(max_duration_seconds=5.0)
        print("✓ Буфер создан")

        # Создаем тестовые данные
        samples = []
        for i in range(10):
            timestamp = i * 0.1  # 10 Гц
            amplitudes = [10.0 + i, 20.0 + i * 2]
            samples.append(EEGSample(timestamp=timestamp, amplitudes=amplitudes))

        batch = EEGSampleBatch(samples=samples)

        # Добавляем в буфер
        buffer.add_batch(batch)
        print("✓ Данные добавлены в буфер")

        # Получаем статистику
        stats = buffer.get_statistics()
        print(f"  Образцов: {stats['total_samples']}")
        print(f"  Длительность: {stats['duration_seconds']:.2f}с")
        print(f"  Каналы: {stats['channels']}")
        print(f"  Память: {stats['memory_usage_mb']:.3f}МБ")

        # Получаем данные для отображения
        timestamps, channel_data = buffer.get_data_for_plotting(window_seconds=10.0)
        print(f"✓ Получены данные для отображения: {len(timestamps)} точек")

        # Получаем последние значения
        latest = buffer.get_latest_values()
        print(f"  Последние значения: {[f'{v:.1f}' for v in latest]}")

        return True

    except Exception as e:
        print(f"✗ Ошибка теста буфера: {e}")
        return False


def test_recorder():
    """Тест рекордера"""
    print("\n=== ТЕСТ РЕКОРДЕРА ===")

    try:
        from realtime_work.realtime_recorder import RealtimeEEGRecorder
        from core.realtime_driver import EEGSample, EEGSampleBatch
        import tempfile
        import os

        # Создаем временный файл
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_file = f.name

        try:
            # Создаем рекордер
            recorder = RealtimeEEGRecorder()
            print("✓ Рекордер создан")

            # Начинаем запись
            if recorder.start_recording(temp_file):
                print("✓ Запись начата")

                # Создаем тестовые данные
                samples = []
                for i in range(5):
                    timestamp = i * 0.1
                    amplitudes = [100.0 + i * 10, 200.0 + i * 20]
                    samples.append(EEGSample(timestamp=timestamp, amplitudes=amplitudes))

                batch = EEGSampleBatch(samples=samples)

                # Записываем данные
                if recorder.write_batch(batch):
                    print("✓ Данные записаны")
                else:
                    print("✗ Ошибка записи данных")

                # Останавливаем запись
                if recorder.stop_recording():
                    print("✓ Запись остановлена")
                else:
                    print("✗ Ошибка остановки записи")

                # Проверяем файл
                if os.path.exists(temp_file):
                    with open(temp_file, 'r') as f:
                        content = f.read()
                        lines = content.strip().split('\n')
                        print(f"✓ Файл создан, строк: {len(lines)}")
                        if len(lines) > 0:
                            print(f"  Первая строка: {lines[0]}")
                        if len(lines) > 1:
                            print(f"  Вторая строка: {lines[1]}")
                else:
                    print("✗ Файл не создан")

            else:
                print("✗ Не удалось начать запись")

        finally:
            # Удаляем временный файл
            if os.path.exists(temp_file):
                os.unlink(temp_file)


    except Exception as e:
        print(f"✗ Ошибка теста рекордера: {e}")
        return False


def test_serial_driver_creation():
    """Тест создания serial драйвера (без подключения)"""
    print("\n=== ТЕСТ СОЗДАНИЯ SERIAL ДРАЙВЕРА ===")

    try:
        from core.realtime_driver import SerialEEGDriver

        # Создаем драйвер (не открываем соединение)
        driver = SerialEEGDriver(
            port="COM1",  # Фиктивный порт
            baudrate=115200,
            sample_rate_hz=250.0,
        )
        print("✓ Serial драйвер создан")

        # Проверяем список портов
        ports = SerialEEGDriver.list_available_ports()
        print(f"✓ Найдено портов: {len(ports)}")
        for port, desc in ports:
            print(f"  {port}: {desc}")

        return True

    except Exception as e:
        print(f"✗ Ошибка теста serial драйвера: {e}")
        return False


def main():
    """Главная функция тестирования"""
    print("ТЕСТИРОВАНИЕ REAL-TIME ФУНКЦИОНАЛЬНОСТИ EEG")
    print("=" * 50)

    tests = [
        test_imports,
        test_synthetic_driver,
        test_data_buffer,
        test_recorder,
        test_serial_driver_creation
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Критическая ошибка в тесте: {e}")

    print("\n" + "=" * 50)
    print(f"РЕЗУЛЬТАТЫ: {passed}/{total} тестов пройдено")

    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        return 0
    else:
        print("⚠️  Некоторые тесты не пройдены")
        return 1


if __name__ == "__main__":
    sys.exit(main())
