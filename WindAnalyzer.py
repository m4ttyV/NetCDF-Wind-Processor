import xarray as xr
import numpy as np

# Функция ввода с проверкой
def get_input(prompt, input_type=str):
    while True:
        try:
            return input_type(input(prompt))
        except ValueError:
            print("Некорректный ввод. Попробуйте снова.")
#Считываем путь к файлу и порог с консоли
input_file = get_input("Введите путь к входному NetCDF-файлу: ", str).strip("\"")
output_file = input_file.replace(".nc", "_output.nc")
w_t = get_input("Введите значение пороговой скорости ветра (в м/с): ", float)
#Проверяем существует ли файл
try:
    ds = xr.open_dataset(input_file)
except FileNotFoundError:
    print(f"Ошибка: Файл {input_file} не найден.")
    exit()
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
        "XLAT": (["south_north", "west_east"], xlat.isel(Time=0).data),  # Широта без времени
        "XLONG": (["south_north", "west_east"], xlong.isel(Time=0).data),  # Долгота без времени
        "Times": (["Time"], times.data),  # Временные отметки
    },
)
# Генерируем новый netcdf-файл рядом с исходником и сохраняем туда все данные
output_ds.to_netcdf(output_file)
print(f"Результат сохранён в файл: {output_file}")