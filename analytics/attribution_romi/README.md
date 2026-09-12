Attribution и ROMI

Для задач 6 и 8 реализовали несколько моделей attribution: `first_touch`, `last_touch`, `linear`, `time_decay` и `position_based`. Также учли attribution window, repeat purchases и заказы, для которых не удалось найти подходящий marketing touch.

Отдельно считаем `ROMI_attr` и ROMI с учётом contribution margin. Проверяем, насколько результаты меняются при разных attribution window и значениях contribution margin.

Основная логика находится в `attribution.py` и `romi.py`, запуск расчётов — в `pipeline.py`. В `attribution_romi.ipynb` собраны графики, сравнение моделей и основные выводы.

Так как в исходных данных нет истории marketing touches и реальных costs, для этой части используются synthetic data. Поэтому полученные значения ROMI нужны в первую очередь для демонстрации работы подхода и не показывают реальную эффективность конкретных рекламных каналов.