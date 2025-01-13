import xarray as xr
import numpy as np
import argparse

# Функция для обработки данных
def process_wind_data(input_file, output_file, w_t):
    try:
        ds = xr.open_dataset(input_file)
    except FileNotFoundError:
        print(f"Ошибка: Файл {input_file} не найден.")
        return

    #Считываем необходимые данные
    u10 = ds["U10"]      #   float U10(Time, south_north, west_east) ;
    v10 = ds["V10"]      #   float V10(Time, south_north, west_east) ;
    xlat = ds["XLAT"]    #    float XLAT(Time, south_north, west_east) ;
    xlong = ds["XLONG"]  #    float XLONG(Time, south_north, west_east) ;
    times = ds["Times"]  #    char Times(Time, DateStrLen) ;
    # Считаем и сохраняем необходимое
    wspd = np.sqrt(u10.data**2 + v10.data**2)
    acc = np.zeros_like(wspd)
    for t in range(1, wspd.shape[0]):  
        acc[t, :, :] = np.where(wspd[t, :, :] < w_t, acc[t - 1, :, :] + 1, 0)

    #Создаём датасэт и выводим результат
    output_ds = xr.Dataset(
        {
            "wspd": (["Time", "south_north", "west_east"], wspd),  # Скорость ветра
            "acc": (["Time", "south_north", "west_east"], acc),  # Накопленные случаи
            "XLAT": (["Time", "south_north", "west_east"], xlat.data),  # Широта без времени
            "XLONG": (["Time", "south_north", "west_east"], xlong.data),  # Долгота без времени
            "Times": (["Time"], times.data),  # Временные отметки
        },
    )

    output_ds.to_netcdf(output_file)
    print(f"Результат сохранён в файл: {output_file}")

# Основная программа
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Программа для анализа данных скорости ветра в файлах NetCDF.")
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
        help="Значение пороговой скорости ветра (в м/с, по умолчанию: 3.0)."
    )

    # Парсим аргументы
    args = parser.parse_args()

    # Запускаем обработку данных
    process_wind_data(args.input, args.output, args.threshold)
