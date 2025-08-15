import xarray as xr
import numpy as np
import argparse

# Функция для обработки данных скорости ветра
def process_wind_data(input_file, output_file, w_t):
    """
    Processes meteorological wind speed data from a netCDF file.
    Args:
        input_file (str): the path to the input netCDF file.
        output_file (str): the path to the netCDF output file.
        w_t (float): threshold wind speed in m/s.

    Returns:
        Creates a netCDF with the calculated wind speed and quantity
        consecutive steps with the wind below the threshold.
    """
    try:
        # Открываем входной NetCDF-файл
        ds = xr.open_dataset(input_file)
    except FileNotFoundError:
        print(f"Ошибка: Файл {input_file} не найден.")
        return

    # Читаем переменные из файла
    u10 = ds["U10"]      # Горизонтальная компонента ветра (восток-запад)
    v10 = ds["V10"]      # Вертикальная компонента ветра (север-юг)
    xlat = ds["XLAT"]    # Широта
    xlong = ds["XLONG"]  # Долгота
    times = ds["Times"]  # Метки времени

    # Вычисляем мгновенную скорость ветра (м/с)
    wspd = np.sqrt(u10.data**2 + v10.data**2)

    # Массив для накопленных значений (счётчик шагов с ветром ниже порога)
    acc = np.zeros_like(wspd)

    # Заполняем массив acc
    for t in range(1, wspd.shape[0]):  
        # Если скорость ниже порога, увеличиваем счётчик,
        # иначе сбрасываем его в ноль
        acc[t, :, :] = np.where(wspd[t, :, :] < w_t,
                                acc[t - 1, :, :] + 1,
                                0)

    # Формируем новый Dataset с результатами
    output_ds = xr.Dataset(
        {
            "wspd": (["Time", "south_north", "west_east"], wspd),  # Скорость ветра
            "acc": (["Time", "south_north", "west_east"], acc),    # Счётчик
        },
        coords={
            "XLAT": (["Time", "south_north", "west_east"], xlat.data),   # Широта
            "XLONG": (["Time", "south_north", "west_east"], xlong.data), # Долгота
            "Times": (["Time"], times.data),                             # Время
        },
    )

    # Добавляем атрибуты для геопривязки переменных координат
    output_ds["XLAT"].attrs["MemoryOrder"] = "XY"
    output_ds["XLAT"].attrs["description"] = "LATITUDE, SOUTH IS NEGATIVE"
    output_ds["XLAT"].attrs["units"] = "degree_north"
    output_ds["XLAT"].attrs["stagger"] = ""
    output_ds["XLAT"].attrs["coordinates"] = "XLONG XLAT"

    output_ds["XLONG"].attrs["MemoryOrder"] = "XY"
    output_ds["XLONG"].attrs["description"] = "LONGITUDE, WEST IS NEGATIVE"
    output_ds["XLONG"].attrs["units"] = "degrees_east"
    output_ds["XLONG"].attrs["stagger"] = ""
    output_ds["XLONG"].attrs["coordinates"] = "XLONG XLAT"

    # Добавляем глобальные атрибуты для выходного файла
    output_ds.attrs["title"] = "Анализ скорости ветра"
    output_ds.attrs["description"] = (
        "Результаты расчёта скорости ветра и накопленных случаев ниже порога"
    )
    output_ds.attrs["source"] = input_file

    # Сохраняем результат в NetCDF
    output_ds.to_netcdf(output_file)
    print(f"Результат сохранён в файл: {output_file}")


# Основная программа (точка входа)
if __name__ == "__main__":
    # Описание аргументов командной строки
    parser = argparse.ArgumentParser(
        description="Программа для анализа данных скорости ветра в файлах NetCDF."
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Путь к входному NetCDF-файлу."
    )
    parser.add_argument(
        "--output", "-o",
        required=False,
        default="output.nc",
        help="Путь для сохранения выходного файла (по умолчанию: output.nc)."
    )
    parser.add_argument(
        "--threshold", "-t",
        required=False,
        type=float,
        default=3.0,
        help="Пороговая скорость ветра (м/с, по умолчанию: 3.0)."
    )

    # Разбор аргументов
    args = parser.parse_args()

    # Запуск обработки данных с переданными параметрами
    process_wind_data(args.input, args.output, args.threshold)
